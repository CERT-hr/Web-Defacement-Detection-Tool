__author__ = "Marko Maric"
__copyright__ = "Copyright 2018, Croatian Academic and Research Network (CARNET)"

flatset = lambda x: set([j for i in x for j in i])

def multiset(list_):

    return set(map(lambda x: (list_.count(x), x), set(list_)))

def list_(multiset):

    return [m for c, m in multiset for i in range(0, c)]


def compare_elements(a, b):

    return a==b


def deflines(defaces):

    results = {}

    for ideface in range(0, len(defaces)):

        for ielement in range(0, len(defaces[ideface])):

            if defaces[ideface][ielement] == '##':
                continue 

            #defaces[ideface][ielement] - element to be observed
            pivot = defaces[ideface][ielement]
            results[pivot] = {}
            ielemstart = ielement

            for jdeface in range(ideface, len(defaces)):

                count = 0

                for jelement in range(ielemstart, len(defaces[jdeface])):

                    if compare_elements(pivot, defaces[jdeface][jelement]):
                        defaces[jdeface][jelement] = '##'
                        count += 1

                ielemstart = 0

                if count == 0:
                    continue

                if not count in results[pivot]:
                    results[pivot][count] = [jdeface]
                else:
                    results[pivot][count].append(jdeface)

            #if len(flatset(results[pivot].values())) == 1:   #minimum of one will always be
            #    del results[pivot]

    return results



######## Example of function call ########
'''
a = range(0, 30)
random.shuffle(a)
b, c, d = a[0:10], a[10:20], a[20:30]
e = random.sample(a, 20)
d1, d2, d3 = e[0:6], e[6:12], e[12:20]
result = subdefaces( ([b, c, d], { 1: 0, 2: 1 }) , {1: d1, 2: d2, 3: d3} )
'''

def subdefaces((subdfcs, colored), D):
    ##print subdfcs
    subdfcs = map(lambda x: set(x), subdfcs)
    D = map(lambda x: set(x), D.values())
    
    colors_index = colored.keys()
    
    result = ([], {})

    for subdfc, icolor in zip(subdfcs, range(0, len(subdfcs))):

        subd = subdfc
    
        for nD in D:
        
            r = subd & nD
            subd -= r
                
            if not len(r) == 0:

                result[0].append(r)
                

        if not len(subd) == 0:

            result[0].append(subd)

            if icolor in colors_index:

                #result[1].append(len(result[0]) - 1)
                result[1][len(result[0]) - 1] = colored[icolor]
 
    return result



'''
subdfcs = [set([0]), set([1, 2, 3, 4]), set([8, 9, 5, 6, 7])]
colored = {0: 0, 1: 1, 2: 2}
Ds = [{2: [2, 8]}]
onlyNX = [1, 4, 5, 6, 8, 9]
AA = 3
XX = 10
'''

def broji2(  (subdfcs, colored), Ds, onlyNX, AA , XX):  #br is list

    data_copy = lambda (subdfcs, colored): ([set([i for i in j]) for j in subdfcs], dict([(k,v) for k,v in colored.items()])) 
    pozn = 0    #index of last position
    maxpoz = len(Ds)
    lista = [maxpoz]
    cpoz = 0
    curnx = lista   #list of current state with optimisation of counting
    ctrace = colored.values()
    memsubdfcs = [(data_copy((subdfcs, colored))) for i in range(0, maxpoz + 1)]

    rDs = [[] for i in range(0, XX)]

    for D, index in zip(Ds, range(0, len(Ds))):

        for d in flatset(D.values()):       #TODO: could be flatlist also

            rDs[d].append(index)
    
        
    (cursubdfcs, curcolored) = memsubdfcs[0]    #could be replaced with [cpoz]

    while(True):

        evaluated = True
        enter = True

        evlpositions = zip(range(lista[cpoz], lista[cpoz]+cpoz) ,  range(cpoz, 0 , -1))

        for tnum, tpoz in evlpositions:
            cpoz = tpoz
            lista[tpoz] = tnum

            #New entry to memsubdfcs from previous iteration (check of last one)
            if not enter:
                memsubdfcs[tpoz] = cursubdfcs, curcolored
            else:
                enter = False
        
            #OPTIMIZATION OF COUNTING
            #1. Do not generate unnecessary deface line sets 

            (cursubdfcs, curcolored) = memsubdfcs[tpoz]

            colordindex = flatset(map(lambda x: cursubdfcs[x], curcolored.keys()))  #defacement indices colored, TODO:moze biti i flatlist

            curdlines = flatset(map(lambda x: rDs[x], colordindex))

            if not tnum in curdlines:
                evaluated = False
                break

            (cursubdfcs, curcolored) = data_copy(subdefaces( (cursubdfcs, curcolored) , Ds[tnum] ))

            #2. Do not continue with "breaches" (LIMIT)
            
            if len(cursubdfcs) > AA:
                evaluated = False
                break

        #print "****************************before UN level subgrouping**************************************"

        if evaluated:
            #At (cursubdfcs, curcolored) is state after full evaluation

            #Check colors

            #1. onlyNX founded in curculored, curcolored index moves on
            onlyNXset = set(filter(lambda x: len(set(cursubdfcs[x]) & set(onlyNX)) != 0 , curcolored.keys()))
            #print onlyNXset
            
            #2. Below ili equal to LIMIT (onlyNX not present)
            unpairedSet = set(curcolored.keys()) - onlyNXset

            for i in unpairedSet:
                if len(cursubdfcs[i]) + len(cursubdfcs) - 1 <= AA:
                    del(curcolored[i])
            #3. Colored disappear
            pass

            #If curcolored is empty, there is no any solution. Exit.
            if len(curcolored) == 0:
                return []

            #curcolored holds all colors that moves on
            #checking number from pozn->1 and looking for first deface line set
            #that is NOT one of remaining colorits.
            ccolors = curcolored.values()
            cindex = map(lambda x: x[0], filter(lambda (x, y): y in ccolors, memsubdfcs[0][1].items()))
            
            colordindex = flatset(map(  lambda x: memsubdfcs[0][0][x], cindex ))
            #print colordindex
            curdlines = flatset(map(lambda x: rDs[x], colordindex))
            #print curdlines

            #print "**************************************************************************"
            for tpoz in range(maxpoz, 0 , -1):
                ccolors = memsubdfcs[tpoz][1].keys()
                cvalues = curcolored.values()

                for i in ccolors:
                    if memsubdfcs[tpoz][1][i] not in cvalues:
                        del(memsubdfcs[tpoz][1][i])

                if tpoz<=pozn and not lista[tpoz] in curdlines:
                    cpoz = tpoz
                    break

        #checking loop    
        #max at postion = br-poz
        #cpoz = 0
        while(True):

            if maxpoz-cpoz == lista[cpoz] and pozn == cpoz: #reached maximum at last position
                if maxpoz == cpoz:      #reached maximum at maximum postion
                    return curcolored.values() 
                else:
                    lista.append(-1)
                    pozn += 1
                    cpoz += 1
                    break
            elif maxpoz-cpoz == lista[cpoz]:    #reached maximum
                cpoz += 1
            else:
                break   #maximum not reached at current position

        lista[cpoz] += 1



def broji(  (subdfcs, colored), Ds, onlyNX, AA , XX):

    rDs = [[] for i in range(0, XX)]

    for D, index in zip(Ds, range(0, len(Ds))):

        for d in flatset(D.values()):       #TODO: could be flatlist also

            rDs[d].append(index)

    results = []
 
    for color_ in colored.items():

        color = dict([color_])

        ##
        colordindex = subdfcs[color.keys()[0]]
        DsI = flatset(map(lambda x: rDs[x], colordindex))
        ##

        #Novi Ds skup.
        DsC=[Ds[i] for i in DsI]

        results += broji2(  (subdfcs, color), DsC, onlyNX, AA , XX)

    return results

        


#AA - number of signatures
#BB - limit for deface

def WebDfcAlg(defaces, AA, BB=3):

    #chains extraction
    lines = deflines(defaces)
    #print lines

    DXlines = filter(lambda (x, y): len(flatset(y.values()))>BB , lines.items())
    #print "Dx lines"
    #print DXlines

    #for DXlining it is necesarry to have lines separated when number of symbol differs.
    #This is needed so it is possible to trace DX subdefaces "symbol strings" from this function.

    #DXlines = map(lambda x: (x[0], x[1].items()), DXlines)
    #print DXlines
    DXlines = [(i,)+(dict([k]),) for i, j in DXlines for k in j.items()]
    #print len(DXlines)

    NXlines = filter(lambda x: len(flatset(x.values())) in range(2, BB+1) , lines.values())
    
    UNs = filter(lambda x: len(flatset(x.values()))==1 , lines.values())
    UNs = set(map(lambda x: x.values()[0][0],UNs))

    onlyNX = set(range(0, len(defaces))) - UNs

    #DX subgrouping
    #subdefaces((subdfcs, colored), D)
    #colored - {index_liste_u_subdfcs: index_obojanog_skupa }
    sdefaces = [set(range(0, len(defaces)))]
    mdefaces = [[]]
    for symbol, DXline in DXlines:

        colors = dict(zip(range(0, len(sdefaces)), range(0, len(sdefaces))))
        sdefaces_t, colors = subdefaces((sdefaces, colors), DXline)

        mdefaces_t = []
        for s, index1 in zip(sdefaces_t, range(0, len(sdefaces_t))):

            for k, index2 in zip(sdefaces, range(0, len(sdefaces))):

                if s&k:
                    if index1 in colors:
                        mdefaces_t.append(mdefaces[index2])
                    else:
                        mdefaces_t.append(mdefaces[index2] + DXline.keys()[0] * [symbol]) 
             
        sdefaces = sdefaces_t
        mdefaces = mdefaces_t


    colors = dict(zip(range(0, len(sdefaces)), range(0, len(sdefaces))))

    if len(sdefaces) <= AA:

        result = broji(  (sdefaces, colors), NXlines, list(onlyNX), AA, len(defaces) )

    else:

        result = []

    return map(lambda x: mdefaces[x], result), map(lambda x: sdefaces[x], result) 


