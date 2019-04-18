#If all queues empty change state of protocol to DIE for everybody.
#TODO: Here I need to be careful because if some process thread throws exception.
#I will never collect info about that process finished and dispatcher will be in deadlock state.
#Is there any other way to enter deadlock state?
#How can I know if process throwed exception? Read and test. I suppose it dies. Can I be notified?


from multiprocessing import Pool, Process, Queue, Pipe, Lock
from select import select
import copy
import json
import worker as worker1
import worker as worker2
import worker as worker3
import worker as worker4 
import psycopg2
import time

#One Worker - Multiple Queues - One Pipe (Two Connections)
#Dispatcher - Multiple Workers

#DISPATCHER:
#queueProcessMapping - mapping of queue to process(workers) list
#pipes and workers are mapped by equal list index

processToQueue = lambda p, d: filter(lambda (a, b): p in b, d.items())[0][0]

def SettingUpWorkers(defaceSignatures, queues, pNumber):

    #TODO: For starter manually determine optimal number of processes.
    #Later, number will be determined by algorithm, where start number could be
    #multiprocessing.cpu_count(), that is call to Pool() with no args.
    pool = Pool(processes = pNumber)

    lock = Lock()   #scan.log mutex locking

    pipes = [  Pipe(True)  for i in range(pNumber)  ]   #parent_conn, child_conn, duplex
    ppipes = [conn[0] for conn in pipes]

    workers = []
    workers.append(Process(target=worker1.main, args=(defaceSignatures, pipes[0][1], lock, queues, 0)))
    workers.append(Process(target=worker2.main, args=(defaceSignatures, pipes[1][1], lock, queues, 1)))
    workers.append(Process(target=worker3.main, args=(defaceSignatures, pipes[2][1], lock, queues, 2)))
    workers.append(Process(target=worker4.main, args=(defaceSignatures, pipes[3][1], lock, queues, 3)))
    [w.start() for w in workers]
    #workers = [  pool.apply_async(worker.main, (defaceSignatures, pipes[i][1], lock))  for i in range(pNumber)  ]


    #WorkerPipeMapping = dict(zip(range(pNumber), pipes))
   
    queuesLeft = queues.keys()
    processesStopped = workers
    queuesPerformance = []

    queueProcessMapping = QueueProcessAssignmentInit(queues, workers)
    processesLeft = len(workers)


    def copyArgs(queuesLeft, processesStopped, queuesPerformance, queueProcessMapping):

        queuesLeft = [i for i in queuesLeft]
        processesStopped = [i for i in processesStopped]
        #queuesPerformance depends on format used in future
        queueProcessMapping = dict( (i, [k for k in j] ) for i, j in queueProcessMapping.items() )

        return (queuesLeft, processesStopped, queuesPerformance, queueProcessMapping)

    #Piping protocol handling
    while processesLeft: 
        args = copyArgs(queuesLeft, processesStopped, queuesPerformance, queueProcessMapping)
        queueProcessMapping, processQueueMappingDiff, _ = QueueProcessAssignment(*args)

        #Dispatcher->Worker
        for p in processQueueMappingDiff.keys():

            if processQueueMappingDiff[p][0] == 'addToTake':
                
                lock.acquire()
                f.write("DISPATCHER: Worker %s., queue %s assigned.\n" % (workers.index(p), processQueueMappingDiff[p][1]))
                f.flush()
                lock.release()

                pipes[workers.index(p)][0].send(['TAKE', processQueueMappingDiff[p][1]])

            elif processQueueMappingDiff[p][0] == 'remove':

                lock.acquire()
                f.write("DISPATCHER: Worker %s., sent of to die.\n" % workers.index(p))
                f.flush()
                lock.release()

                pipes[workers.index(p)][0].send(['DIE'])

                #This could be handled asnychronously with callback function
                #But in that case we have potential situation of deadlock 
                #With blocked call on select() when there is no more processes.
                processesLeft -= 1

            else:

                pass    #should never be executed


        if processesLeft:
            conns, _, _ = select(ppipes, [], [],1) #parent_conn
        else:
            conns = []

        #Worker->Dispatcher
        processesStopped = []
        for conn in conns:

            data = conn.recv()

            if data[0] == 'DONE':

                num_of_bytes = data[1]
                #Add finished queue to list.
                proc = workers[ppipes.index(conn)]
                try:
                    queuesLeft.remove(processToQueue(proc, queueProcessMapping))
                except ValueError:
                    pass
                processesStopped.append(proc)

                lock.acquire()
                f.write("DISPATCHER: Worker %s. finished with queue. Queue %s empty.\n" % (ppipes.index(conn), processToQueue(proc, queueProcessMapping)))
                f.flush()
                lock.release()


            if data[0] == 'READY':
                pass

    [w.join() for w in workers]



#################################################################NAIVE STRATEGY#######################################################


def QueueProcessAssignmentInit(queues, workers):

    queues = queues.keys()

    return dict([(queues[0], workers)] + map(lambda x: (x, []), queues[1:]))


#Naive strategy omits information about ASNs load, although it is used for verbosing.
#INPUT: queuesLeft, processesStopped, queuesPerformance, queueProcessMapping
#OUTPUT:
#New mappings {queue: process_list, ...}
#Diffs {process1: [addToTake, queue], process2: [remove], process3: [addToRun, queue, time], ...} for each of stopped process
#New processes ([addToTake, queue], [addToRun, queue, time], ...)
#DESCRIPTION: This function given living queue list, stopped process list, known queues performance, and current mapping
#of stopped and runnning processes on queues, makes conclusions about how to reassign stopped processes or conduct additional
#measurments with some processes on certian queues.
#Following strategy rule is important for PROTOCOL LOOP to continue working always (free of deadlocks) and to finish eventually.
#STRATEGY RULE: Always issue non-DIE message to at least one stopped process if there are living queues or DIE message to everybody if all queues are done.
#queueProcessMapping is showing current state of running and stopped processes over empty and non-empty queues (queuesLeft)
#queuesLeft are queues that are non-empty (intact or processes running on them).
#There may exist queues that are empty and removed from queuesLeft, but have processes running on them (vanishing queues).
#queuesProcessMapping shows distribution over queuesLeft and vanishing queues.

def QueueProcessAssignment(queuesLeft, processesStopped, queuesPerformance, queueProcessMapping):

    #Strategy: The simplest strategy will be to arrange stopped processes over queues
    #to have as much as possible uniform distribution. Assignement has only sense on queuesLeft,
    #there is no sense to assign to empty vanishing queues.

    #remove stopped processes from queueProcessMapping list
    for p in processesStopped:

        q = processToQueue(p, queueProcessMapping)

        queueProcessMapping[q].remove(p)


    #remove empty queues that have no running processes on them, from queueProcessMapping list
    queues = queueProcessMapping.keys()

    for q in queues:

        if q not in queuesLeft and not queueProcessMapping[q]:

            del queueProcessMapping[q]


    newQueueProcessMapping = queueProcessMapping
    processQueueMappingDiff = {}

    if not queuesLeft:

        for p in processesStopped:

            processQueueMappingDiff[p] = ('remove',)

        return newQueueProcessMapping, processQueueMappingDiff, [] 


    #Algorithm: find queue with minimum number of running processes and assign next process to it
    for p in processesStopped:

        numOfProcessesPerQueue = map(lambda x: (x, len(newQueueProcessMapping[x])), queuesLeft)

        QueueWithMinNumberOfProc = min(numOfProcessesPerQueue, key=lambda x: x[1])[0]

        newQueueProcessMapping[QueueWithMinNumberOfProc].append(p) 

        processQueueMappingDiff[p] = ('addToTake', QueueWithMinNumberOfProc)

    return newQueueProcessMapping, processQueueMappingDiff, []



#################################################################NAIVE STRATEGY#######################################################


def getSignaturesAndDomains():

    conn = psycopg2.connect("dbname='webdfcdb6' user='webdfc' host='localhost' password='webdfc'")
    curr = conn.cursor()

    curr.execute("SELECT notifier.name, timestamp, deface_signature.id, ARRAY_AGG(ARRAY[type::bytea,element]) FROM notifier \
                    JOIN deface_signature ON notifier.id=deface_signature.notifier_id \
                    JOIN defaces_signature_elements_dfcsign ON defaces_signature_elements_dfcsign.deface_signature_id=deface_signature.id \
                    JOIN elements_dfcsign ON defaces_signature_elements_dfcsign.elements_dfcsign_id=elements_dfcsign.id \
                    GROUP BY notifier.name, timestamp, deface_signature.id")


    table = curr.fetchall()

    curr.close()
    conn.close()

    return table



f = open("ASNsDomains.hr","r")
ASNsDomains = json.load(f)
f.close()


Queues = [ Queue() for i in range(len(ASNsDomains)) ]

Queues = Queues[0:10]   #For testing

result = {}


for (asn, domains), index in zip(ASNsDomains.items(), range(len(Queues))):

    [Queues[index].put(domain) for domain in domains]

    result[asn] = Queues[index]

    print asn, len(domains)


table = getSignaturesAndDomains()

f = open("scan.log", "a")

f.write("--------------------------------------------------------------------------------%s\
---------------------------------------------------------------------------------\n"  % (time.strftime("%c"),))
 
SettingUpWorkers(table, result, pNumber = 4)



f.write("DISPATCHER: Done at %s.\n" % (time.strftime("%c"),))

f.close()

