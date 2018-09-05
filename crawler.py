
from pyvirtualdisplay import Display

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert

from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException, StaleElementReferenceException
import time as time_

from bs4 import BeautifulSoup

import sys  #for exit()
import codecs

import re

import urllib2

import psycopg2

import traceback

import spamsum


conn = psycopg2.connect("dbname='webdfcdb4' user='webdfc' host='localhost' password='webdfc'")
curr = conn.cursor()


def multiset(list_):

    return set(map(lambda x: (list_.count(x), x), set(list_)))


def list_(multiset):

    return [m for c, m in multiset for i in range(0, c)]


sys.stdout = codecs.getwriter('utf-8')(sys.stdout)  #needed for printing Unicode in file

display = Display(visible=0, size=(800, 600))
display.start()

browser = webdriver.Chrome('/home/marko/workspace/chromedriver')

class Stale():
    pass

STALE = Stale()
ALERT_CONFIRMS = 10

def visible(element):
    if element.parent.name in ['style', 'script', '[document]', 'head']:
        return False
    elif re.match('<!--.*-->', element):
        return False
    elif element.strip() == '':
        return False
    else:
        return True


def getSignaturesAndDomains():

    curr.execute("SELECT notifier.name, timestamp, deface_signature.id, ARRAY_AGG(ARRAY[type::bytea,element]) FROM notifier \
                    JOIN deface_signature ON notifier.id=deface_signature.notifier_id \
                    JOIN defaces_signature_elements_dfcsign ON defaces_signature_elements_dfcsign.deface_signature_id=deface_signature.id \
                    JOIN elements_dfcsign ON defaces_signature_elements_dfcsign.elements_dfcsign_id=elements_dfcsign.id \
                    GROUP BY notifier.name, timestamp, deface_signature.id")


    table = curr.fetchall()

    curr.close()
    conn.close()

    f = open("domains.file", "r")
    domains = f.readlines()
    f.close()

    return table, domains


#Function enables recovery if element disappears from DOM tree or page is refreshed

def getDynamicElements(getFunction, *args):

    try:
        return getFunction(*args)
    except StaleElementReferenceException as e:
        #print "stalan element"
        return STALE
 

#Discards None or anything shorter than three symbols

def filterValidElements(elements):

    for key in elements:

        elements[key] = filter(lambda x: False if x == None or x == STALE or len(x) < 3 else True, elements[key])

    return elements


    allElems = {'alerts': [], 'texts': [], 'images': [], 'backgroundImages': [], 'music': []}


#TODO: Replace with resource and hash!!
def calculateFuzzy(elements):
    #print "**********************************************************************************************\n"
    #print elements

    pics = {}
    for key, value in elements.iteritems():

        if key in ('images', 'backgroundImages'):

            for url in value:
                try:
                    if not url in pics:
                        pic = urllib2.urlopen(url).read()
                        pics[url] = pic
                except (urllib2.HTTPError, urllib2.URLError) as e:
                    print "Not able to download image: %s\n" % (url, )
                    pics[url] = None
                except ValueError as e:
                    if 'unknown url type' in str(e):
                        print "Incorrectly formatted URL.\n"
                        pics[url] = None
                    else:
                        raise e

            elements[key] = filter(lambda (x, y, z): not y == None, \
                            map(  lambda x: (None, None, x) if pics[x] == None else (pics[x], spamsum.spamsum(pics[x]), x) , value))

        elif key in ('alerts', 'texts'):

            elements[key] = map(  lambda x: (x, spamsum.spamsum(x.encode('utf-8')), None) , value)

        else:   #music

            elements[key] = map(lambda x: (x.split(u'?')[0], spamsum.spamsum(x.split(u'?')[0]), x), value) 

    return elements



def getElementContent(allElems):

    #downloading images and backgroundImages
    return allElems


def getElements(mirrorsrc):

    #creating dictionary of Elements
    allElems = {'alerts': [], 'texts': [], 'images': [], 'backgroundImages': [], 'music': []}

    browser.get(mirrorsrc)

    try:

        for i in range(0, ALERT_CONFIRMS + 1):       #number of alert confirms: 10 alerts and content

            try:

                try:
                    WebDriverWait(browser, 10).until(
                                EC.presence_of_element_located((By.TAG_NAME, "body"))
                                )
                except TimeoutException as e:
                    #print "Time elapsed for zone-h page processing getElements\n"
                    break
                else:
                    time_.sleep(2)  #safety hold in case HTML is not fully loaded, and time for potential another alert

                    soup = BeautifulSoup(browser.page_source, 'html.parser')

                    #Downloading all element types
                    #All visible text
                    texts = soup.findAll(text=True)
                    visible_texts = filter(visible, texts)  
                    allElems['texts'] = visible_texts

                    #Images (img tags)
                    images = browser.find_elements_by_tag_name('img')
                    images = map(lambda x: getDynamicElements(x.get_attribute, 'src'), images)
                    fimageurls = images

                    allElems['images'] = fimageurls
                    
                    #Background images

                    allNodes = browser.find_elements_by_xpath("//*")

                    allBackImageURLs = map(lambda x: getDynamicElements(x.value_of_css_property, 'background-image'), allNodes)

                    #Although None and STALE are filtered afterwards in filterValidElements
                    allBackImageURLsFiltered = filter(lambda x: False if x in [u'none', u'', None, STALE] else True, allBackImageURLs)

                    allBackImageURLsFiltered = map(lambda x: x[5:-2], allBackImageURLsFiltered)

                    allElems['backgroundImages'] = allBackImageURLsFiltered         #Check for background value is needed as well!!
                    
                    #Music (embed:src, iframe:src,  - width=height=0 does not have to be!!)

                    musicLinks1 = map(lambda x: getDynamicElements(x.get_attribute, 'src'), browser.find_elements_by_tag_name('embed'))
                    musicLinks2 = map(lambda x: getDynamicElements(x.get_attribute, 'src'), browser.find_elements_by_tag_name('iframe'))

                    musicLinks = musicLinks1 + musicLinks2

                    allElems['music'] = musicLinks
                    break


            except UnexpectedAlertPresentException as e:
                #print "Accepting alert in getElements: %s\n" % (Alert(browser).text,)

                allElems['alerts'].append(Alert(browser).text)
                allElems['texts'] = []
                allElems['images'] = []
                allElems['backgroundImages'] = []
                allElems['music'] = []

                #if i == ALERT_CONFIRMS:
                    #print traceback.format_exc()
                    #print "\n"

                #Accept alert
                Alert(browser).accept()

    except:
        #print "Unsuccessful processing of getElements\n"
        #print traceback.format_exc()
        #print "\n"
        pass


    allElemsWithContent = getElementContent(allElems)

    return allElemsWithContent



def processWebpage(mirrorsrc):

    elementsOutput = []

    elements = getElements(mirrorsrc)

    elements = filterValidElements(elements)

    elements = calculateFuzzy(elements)

    dataType = lambda basictype, size: 'L' + basictype if size <= 1000 else 'H' + basictype

    for key, values in elements.iteritems():

        for value in values:

            data = bytearray(value[0], 'utf-8') if isinstance(value[0], unicode) else bytearray(value[0])

            elementsOutput.append((dataType(key, len(data)), buffer(data))) 

    return elementsOutput


def serializeElements(mset):

    list_ = sorted(list(mset), key=lambda x: str(x[1][1]))

    return ''.join([str(i[1][1]) * i[0] for i in list_])


maxSim = 0

def calculus(matchesTable, forbbidenList, currSum):

    global maxSim

    if matchesTable == []:

        if currSum > maxSim:

            maxSim = currSum

        return

    for i in range(0, len(matchesTable[0])):

        if i in forbbidenList:
            continue

        calculus(matchesTable[1:], forbbidenList + [i], currSum + matchesTable[0][i])

        


def similarityIndex(elementsWebpage, sdefaces):

    matchesTable = []
    mSum = 0

    #print "length"
    #print len(elementsWebpage), len(sdefaces)

    for i in sdefaces:
        matchesTable.append([])
        for j in elementsWebpage:
            a = spamsum.spamsum(i)
            b = spamsum.spamsum(j)
            matchesTable[-1].append(spamsum.match(a, b))

    if len(sdefaces) > len(elementsWebpage):

        #iters = itertools.combinations(range(0, len(sdefaces)), len(elementsWebpage))

        for i in range(0, 10):

            s = random.sample(range(0, len(sdefaces)), len(elementsWebpage))

            matchesTableP = map(lambda x: matchesTable[x], s)

            maxSim = 0
            calculus(matchesTableP, [], 0)

            if maxSim > mSum:
                mSum = maxSim
    else:
        maxSim = 0
        #print matchesTable
        calculus(matchesTable, [], 0)
        mSum = maxSim


    return mSum*1.0/len(sdefaces)
            

#CRAWLING
def processDomainsList(domains, table):
    #prepare multisets of retrived (type, elements) from database

    table = map(lambda x: x[:3] + ( multiset(map(lambda y: (str(y[0]), y[1]), x[3])) ,) + x[4:], table)        
    
    for domain in domains:
         
         #TODO: map from domain to webpage URL. Is it needed?
         elementsWebpage = processWebpage(domain)
         elementsWebpage = multiset(elementsWebpage)

         elementsWebpage = spamsum.spamsum(serializeElements(elementsWebpage))

         notfound = True

         for row in table:

            sdeface = spamsum.spamsum(serializeElements(row[3]))
            #sdeface = row[3]

            #similarity = similarityIndex(map(lambda x: x[1], elementsWebpage), map(lambda x: x[1], sdeface))
            similarity = spamsum.match(elementsWebpage, sdeface)

            if similarity >= 70: #TODO: Comparison Strategy!!
    
                notfound = False
                print "Defacement found at %s -> Notifier: %s, Signature ID: %s, Detected on: %s (%s%%)" % \
                                            (domain.strip(), row[0], row[2], row[1], similarity)
                break

         if notfound:
                print "No defacement found (%s)" % (domain.strip(),)



def main():


    try:
        table, domains = getSignaturesAndDomains()
        processDomainsList(domains, table)

        print "Successfully done.\n"
    except:
        print "Unsuccessfully done.\n"
        print traceback.format_exc()
        print "\n"
    finally:
        browser.quit()
 


print "----------------------------------------------------%s\
---------------------------------------------------------------------------------\n"  % (time_.strftime("%c"),)
main()


