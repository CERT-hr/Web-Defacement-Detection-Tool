
import WebDfcAlg

import psycopg2
import iptoolsng
import datetime

conn = psycopg2.connect("dbname='webdfcdb4' user='webdfc' host='localhost' password='webdfc'")
curr = conn.cursor()


def multiset(list_):

    return set(map(lambda x: (list_.count(x), x), set(list_)))

def list_(multiset):

    return [m for c, m in multiset for i in range(0, c)]


#######################################################################MAINTAINING DATABASE SIZE################################################################################

curr.execute("SELECT notifier.id, array_agg(DISTINCT defaces.id), array_agg(DISTINCT defaces_elements_defaces.id), array_agg(DISTINCT elements_defaces.id) FROM notifier \
                    JOIN defaces ON notifier.id=defaces.notifier_id \
                    JOIN defaces_elements_defaces ON defaces.id=defaces_elements_defaces.defaces_id \
                    JOIN elements_defaces ON elements_defaces.id=defaces_elements_defaces.elements_defaces_id \
                    WHERE time <= now() - interval '6 months' GROUP BY notifier.id")

table = curr.fetchall()

#1. Deleting defaces_elements_defaces

deds = [n for row in table for n in row[2]]

curr.execute("DELETE FROM defaces_elements_defaces WHERE id IN %s", (tuple(deds),))

#2. Deleting defaces
ds = [n for row in table for n in row[1]]

curr.execute("DELETE FROM defaces WHERE id IN %s", (tuple(ds),))

#Deleting elements defaces and notifiers must be controlled with transactions because foreign key constrains

#Deleting records from elements_defaces unless reference violation occurs

#If I continue to delete, there are still IntegrityErrors, so problem must be solved with transactions.

eds = set([n for row in table for n in row[3]]) #set - because same element can be used in many defacements

for ed in eds:

    curr.execute('SAVEPOINT sp1')

    try:

        curr.execute("DELETE FROM elements_defaces WHERE id = %s", (ed,))

    except psycopg2.IntegrityError as e:
        curr.execute('ROLLBACK TO SAVEPOINT sp1')

    curr.execute('RELEASE SAVEPOINT sp1')


#Deleting notifier

ns = [row[0] for row in table]

for n in ns: 

    curr.execute('SAVEPOINT sp1')

    try:

        curr.execute("DELETE FROM notifier WHERE id = %s", (n,))

    except psycopg2.IntegrityError as e:
        curr.execute('ROLLBACK TO SAVEPOINT sp1')

    curr.execute('RELEASE SAVEPOINT sp1')



curr.close()
conn.commit()

########################################################################MAINTAINING DATABASE SIZE########################################################################



#################################################################NOTIFIERS, NEW DEFACEMENTS, ALGORITHM###################################################################


#************LAST ID**************
#Current start id
f = open("id.temp", "r")
idstart = int(f.read())
f.close()

#Current end id
curr.execute("SELECT max(id) FROM defaces")
idend = curr.fetchall()[0][0]

#Write current end id as start id for next signature processing
f = open("id.temp", "w")
f.write(str(idend))
f.close()
#************LAST ID**************


curr = conn.cursor()

curr.execute("SELECT DISTINCT notifier.id FROM notifier JOIN defaces ON notifier.id=defaces.notifier_id\
                        WHERE defaces.id>%s AND defaces.id<=%s", (idstart, idend))

table = curr.fetchall()

notifiersid = [i[0] for i in table]
print "notifiersid:"
print notifiersid

for notifierid in notifiersid:

    ddomains = {}

    curr.execute("SELECT  defaces.id, defaces.time, defaces.url  FROM notifier JOIN defaces ON notifier.id=defaces.notifier_id\
                     WHERE notifier.id=%s ORDER BY defaces.id DESC", (notifierid,))

    table = curr.fetchall()

    #taking care all records are in 6 months time delta from first record
    timestart = table[0][1]
    delta = datetime.timedelta(days = 180)  #6 months
    table = filter(lambda x: x[1] >= timestart - delta, table)    

    #choosing last 7 from different second level domain
    for row in table:

        url = row[2]
        hostname = iptoolsng.url2host(url)

        #TODO: how many subdomains should I look? 
        #dnames = hostname.split('.')
        #domain = dnames[-2] + '.' + dnames[-1]

        domain = hostname

        if domain not in ddomains:

            ddomains[domain] = row[0]

        if len(ddomains) == 7:
            break

    print "notifierid:"
    print notifierid
    print "ddomains:"
    print ddomains

    #check if we have 7 defaces candidates for algorithm. If yes, get data from database and call algorithm
    if not len(ddomains) == 7:
        continue

    #get algorithm input from database

    curr.execute("SELECT defaces.id, ARRAY_AGG(elements_defaces.id) FROM \
                    defaces JOIN defaces_elements_defaces ON defaces.id=defaces_elements_defaces.defaces_id \
                        JOIN elements_defaces on defaces_elements_defaces.elements_defaces_id=elements_defaces.id \
                            WHERE defaces.id IN %s GROUP BY defaces.id", (tuple(ddomains.values()),))


    ##########################STRATEGY FOR USING ALGORITHM################################
    
    #For now only XX=7, AA=3, BB=3 as fix parameters.

    elements_table = curr.fetchall()
    elements_table = map(lambda x: x[1], elements_table)

    print "elements_table:"
    print elements_table

    output, _ = WebDfcAlg.WebDfcAlg(elements_table, 3)

    print "alg output:"
    print output

    if not output:  #algorithm did not detected any signature
        continue

    #################CHECKING IF DEFACE SIGNATURES ALREADY EXISTS#####################

    #same signature can be owned by many notifiers
    #get all (type, element) pairs from elements_defaces found in output
    #find same (type, element) pairs in elements_dfcsign and map between ids.

    #################################INSERTING DATA IN TABLE##############################

    #getting all elements

    curr.execute("SELECT id, type, element, hash, resource FROM elements_defaces WHERE id IN %s", (tuple(set([j for i in output for j in i])),))

    edtable = curr.fetchall()

    #creating dictionary

    edtable = dict(map(lambda x: [x[0], x[1:]] ,edtable))

    print notifierid


    curr.execute("SELECT deface_signature.id, ARRAY_AGG(ARRAY[elements_dfcsign.type::bytea, elements_dfcsign.element]) \
                    FROM deface_signature JOIN defaces_signature_elements_dfcsign \
                        ON deface_signature.id=defaces_signature_elements_dfcsign.deface_signature_id \
                            JOIN elements_dfcsign ON elements_dfcsign.id=defaces_signature_elements_dfcsign.elements_dfcsign_id \
                                WHERE notifier_id = %s GROUP BY deface_signature.id", (notifierid,))



    edstable = curr.fetchall()

    for out in output:

        #create (type, element) multiset of found algorithm output

        outed = map(lambda x: edtable[x] ,out)

        print map(lambda x: (edtable[x][0], edtable[x][1]) , out)

        outte = multiset(map(lambda x: (edtable[x][0], edtable[x][1]) , out))

        timestamp = False
        print "Comparing:"
        print outte
        for roweds in edstable:
            
            print "roweds[1]:"
            reds = map(lambda x: (str(x[0]), x[1]), roweds[1])
            print reds
            #print multiset(map(lambda x: (x[0], spamsum.spamsum(x[1])) , roweds[1]))
            #print "outte:"
            #print outte
            
            if multiset(reds) == outte:

                #update timestamp

                timestamp = True

                curr.execute('UPDATE deface_signature \
                                SET timestamp = NOW() \
                                WHERE id=%s', (roweds[0],))
                print "Update done!!"
                break

        if not timestamp:
            #add new signature
            curr.execute("INSERT INTO deface_signature (notifier_id, detection, timestamp) VALUES (%s, 0, NOW()) RETURNING id;", (notifierid,))
            defaces_signature_id = curr.fetchone()[0]
            #Adding new signature if does not exists in 'elements_dfcsign'
            for type_, element, hash_, resource in outed:

                curr.execute("SELECT id FROM elements_dfcsign WHERE type=%s AND element=%s", \
                                                                (type_, element))
                result = curr.fetchall()
                if len(result) == 0:
                    curr.execute("INSERT INTO elements_dfcsign (type, element, hash, resource) VALUES (%s, %s, %s, %s) RETURNING id;", \
                                                                (type_, element, hash_, resource))
                    elements_dfcsign_id = curr.fetchone()[0]
                else:
                    elements_dfcsign_id = result[0][0]

                #For all pairs 'defaces'-'elements_defaces' adding new entry in defaces_elements_defaces
                curr.execute("INSERT INTO defaces_signature_elements_dfcsign (deface_signature_id, elements_dfcsign_id) VALUES (%s, %s) RETURNING id;",\
                                 (defaces_signature_id, elements_dfcsign_id))


curr.close()
conn.commit()
    
#################################################################NOTIFIERS, NEW DEFACEMENTS, ALGORITHM###################################################################


####################################################################DELETING OLD DEFACES SIGNATURES######################################################################


curr.execute("SELECT notifier.id, array_agg(DISTINCT deface_signature.id), array_agg(DISTINCT defaces_signature_elements_dfcsign.id) \
                         , array_agg(DISTINCT elements_dfcsign.id) FROM notifier \
                     JOIN deface_signature ON notifier.id=deface_signature.notifier_id \
                     JOIN defaces_signature_elements_dfcsign ON deface_signature.id=defaces_signature_elements_dfcsign.deface_signature_id \
                     JOIN elements_dfcsign ON elements_dfcsign.id=defaces_signature_elements_dfcsign.elements_dfcsign_id \
                     WHERE timestamp <= now() - interval '6 months' GROUP BY notifier.id")

table = curr.fetchall()

#1. Deleting defaces_signature_elements_dfcsign

dseds = [n for row in table for n in row[2]]

curr.execute("DELETE FROM defaces_signature_elements_dfcsign WHERE id IN %s", (tuple(dseds),))

#2. Deleting deface_signature
dss = [n for row in table for n in row[1]]

curr.execute("DELETE FROM deface_signature WHERE id IN %s", (tuple(dss),))


#Deleting elements_dfcsign and notifiers must be controlled with transactions because foreign key constrains

#Deleting records from elements_dfcsign unless reference violation occurs

#If I continue to delete, there are still IntegrityErrors, so problem must be solved with transactions.

edss = set([n for row in table for n in row[3]]) #set - because same element can be used in many defacements

for eds in edss:

    curr.execute('SAVEPOINT sp1')

    try:

        curr.execute("DELETE FROM elements_dfcsign WHERE id = %s", (eds,))

    except psycopg2.IntegrityError as e:
        curr.execute('ROLLBACK TO SAVEPOINT sp1')

    curr.execute('RELEASE SAVEPOINT sp1')


#Deleting notifier

ns = set([n for row in table for n in row[0]])

for n in ns: 

    curr.execute('SAVEPOINT sp1')

    try:

        curr.execute("DELETE FROM notifier WHERE id = %s", (n,))

    except psycopg2.IntegrityError as e:
        curr.execute('ROLLBACK TO SAVEPOINT sp1')

    curr.execute('RELEASE SAVEPOINT sp1')


curr.close()
conn.commit()


####################################################################DELETING OLD DEFACES SIGNATURES######################################################################

conn.close()


