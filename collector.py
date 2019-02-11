__author__ = "Marko Maric"
__copyright__ = "Copyright 2018, Croatian Academic and Research Network (CARNET)"

from pyvirtualdisplay import Display

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.keys import Keys

from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException, StaleElementReferenceException
import time as time_

from bs4 import BeautifulSoup


import sys  #for exit()
import codecs

import re
import ssdeep

import psycopg2

from datetime import datetime

import traceback
import time

import urllib2

import captcha
import rateLimit

sys.stdout = codecs.getwriter('utf-8')(sys.stdout)  #needed for sending Unicode to file

conn = psycopg2.connect("dbname='webdfcdb4' user='webdfc' host='localhost' password='webdfc'")


display = Display(visible=0, size=(800, 600))
display.start()

browser = webdriver.Chrome('/home/marko/workspace/chromedriver')

#browser.get can be called only once each 5 seconds,
#to reduce possibility of zone-h blacklisting.
browser_get = rateLimit.rateLimit(0.2, browser.get)

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


def processDefacement(time, notifier, url, mirrorsrc):

    elements = getElements(mirrorsrc)

    elements = filterValidElements(elements)

    elements = calculateFuzzy(elements)

    insertInDatabase(notifier, time, url, elements, mirrorsrc)


#Function enables recovery if element disappears from DOM tree or webpage is refreshed

def getDynamicElements(getFunction, *args):

    try:
        return getFunction(*args)
    except StaleElementReferenceException as e:
        print "Stale element"
        return STALE
          

#Discards None or anything shorter than three symbols

def filterValidElements(elements):

    for key in elements:

        elements[key] = filter(lambda x: False if x == None or x == STALE or len(x) < 3 else True, elements[key])

    return elements


    allElems = {'alerts': [], 'texts': [], 'images': [], 'backgroundImages': [], 'music': []}



def insertInDatabase(notifier, time, url, elements, mirrorsrc):

    #Insert in database
    print "insertInDatabase\n"
    print notifier, time, url, sys.getsizeof(elements), mirrorsrc
    print "\n"
 
    dataType = lambda basictype, size: 'L' + basictype if size <= 1000 else 'H' + basictype

    curr = conn.cursor()

    notifier_id = None
    #adding new notifier in 'notifier' table if does not exists
    curr.execute("SELECT id FROM notifier WHERE name=%s", (notifier,))
    result = curr.fetchall()
    if len(result) == 0:
        curr.execute("INSERT INTO notifier (name) VALUES (%s) RETURNING id;", (notifier,))
        notifier_id = curr.fetchone()[0]
    else:
        notifier_id = result[0][0]

    #adding new deface in 'defaces' table
    #TODO: Adds wrong date if time after 21:00/22:00
    today = datetime.today()
    time = datetime.strptime('%s %s %s ' % (today.day, today.month, today.year) + time, '%d %m %Y %H:%M')
    curr.execute("INSERT INTO defaces (time, notifier_id, url, mirrorsrc) VALUES (%s, %s, %s, %s) RETURNING id;", (time, notifier_id, url, mirrorsrc))
    defaces_id = curr.fetchone()[0]
    #Adding new element if does not exists in 'elements_defaces'
    for key, values in elements.iteritems():
            for value in values:

                data = bytearray(value[0], 'utf-8') if isinstance(value[0], unicode) else bytearray(value[0])

                curr.execute("SELECT id FROM elements_defaces WHERE type=%s AND element=%s", \
                                                                (dataType(key, len(data)), data))
                result = curr.fetchall()
                if len(result) == 0:
                    curr.execute("INSERT INTO elements_defaces (type, element, hash, resource) VALUES (%s, %s, %s, %s) RETURNING id;", \
                                                                (dataType(key, len(data)), data, value[1], value[2]))
                    elements_dafaces_id = curr.fetchone()[0]
                else:
                    elements_dafaces_id = result[0][0]
    
                #for each pair 'defaces'-'elements_defaces' adding new entry in defaces_elements_defaces
                curr.execute("INSERT INTO defaces_elements_defaces (defaces_id, elements_defaces_id) VALUES (%s, %s) RETURNING id;",\
                                 (defaces_id, elements_dafaces_id))

    curr.close()
    conn.commit()
    

def calculateFuzzy(elements):
    #print "**********************************************************************************************\n"
    #print elements

    pics = {}
    for key, value in elements.iteritems():

        if key in ('images', 'backgroundImages'):

            for url in value:
                try:
                    if not url in pics:
                        #TODO: images are already present on system. How to avoid double download. Doing crawling this will be crucial.
                        pic = urllib2.urlopen(url).read()
                        pics[url] = pic
                except (urllib2.HTTPError, urllib2.URLError) as e:
                    print "Not able to download image (%s).\n" % (url, )
                    pics[url] = None
                except ValueError as e:
                    if 'unknown url type' in str(e):
                        print "Incorrectly formatted URL (%s).\n" % (url, )
                        pics[url] = None
                    else:
                        raise e

            elements[key] = filter(lambda (x, y, z): not y == None, \
                            map(  lambda x: (None, None, x) if pics[x] == None else (pics[x], ssdeep.hash(pics[x]), x) , value))

        elif key in ('alerts', 'texts'):

            elements[key] = map(  lambda x: (x, ssdeep.hash(x.encode('utf-8')), None) , value)

        else:   #music

            elements[key] = map(lambda x: (x.split(u'?')[0], ssdeep.hash(x.split(u'?')[0]), x), value) 

    return elements


def getElementContent(allElems):

    #downloading images and backgroundImages
    return allElems


#captcha cannot appear here, so will not be handling code
def getElements(mirrorsrc):

    #creating dictionary of Elements
    allElems = {'alerts': [], 'texts': [], 'images': [], 'backgroundImages': [], 'music': []}

    browser_get(mirrorsrc)

    try:

        for i in range(0, ALERT_CONFIRMS + 1):       #number of alert confirms: 10 alerts and content

            try:

                try:
                    WebDriverWait(browser, 10).until(
                                EC.presence_of_element_located((By.TAG_NAME, "body"))
                                )
                except TimeoutException as e:
                    print "Time elapsed for zonehmirrors.org processing (getElements)\n"
                    break
                else:
                    time_.sleep(2)  #safety hold in case HTML is not fully loaded, and time for potential another alert

                    soup = BeautifulSoup(browser.page_source, 'html.parser')
                    
                    #Downloading all element types
                    #All visible text
                    texts = soup.findAll(text=True)
                    visible_texts = filter(visible, texts)  
                    allElems['texts'] = visible_texts

                    #Images (img tagovi)
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
                print "Accepting alert in zonehmirrors.org processing (getElements): %s\n" % (Alert(browser).text,)

                allElems['alerts'].append(Alert(browser).text)
                allElems['texts'] = []
                allElems['images'] = []
                allElems['backgroundImages'] = []
                allElems['music'] = []

                if i == ALERT_CONFIRMS:
                    print traceback.format_exc()
                    print "\n"

                #Accept alert
                Alert(browser).accept()

    except:
        print "Unsuccessful processing of zonehmirrors.org (getElements)\n"
        print traceback.format_exc()
        print "\n"


    #TODO: I don't want to take partial set of elements! Algorithm will give wrong outputs.
    allElemsWithContent = getElementContent(allElems)

    return allElemsWithContent



def process_zoneh_pages(f):

    ttime, tnotifier, tmirror = ctime, cnotifier, cmirror = f.read().split('\n')[:3]
    tnotifier = cnotifier = cnotifier.decode('utf-8')
    allData = []
     
    print [ctime, cnotifier, cmirror] 
    print "\n"

    i = -1

    for pagenum in range(1, 2):     #looking for defaces in first two pages

        try:
            print "Downloading zone-h.org page: %s\n" % pagenum

            #TODO: Connecting over TOR (captcha recognition and change of circuit)
            browser_get('http://zone-h.org/archive/page=%d' % (pagenum,))
            
            havepage = False

            for k in range(1, 5):   #Loop of uncorrectly solved captachas

                try:
                    WebDriverWait(browser, 10).until(
                                EC.presence_of_element_located((By.ID, "ldeface"))  #TODO: wait for ldeface OR propdeface. How to handle flows in that case?
                                )

                except TimeoutException as e:

                    WebDriverWait(browser, 5).until(
                                EC.presence_of_element_located((By.ID, "propdeface"))
                                )
                    
                    #In case of timeout on ldeface, we are checking if captcha is present.
                    #If captcha is not present generic exception handling code will take over control.
                    #Next page will tried to be downloaded.
                    #This differs from v0.9 that continued to scan next page immedatelly.
                    #Software robustness(resiliency) is kept.
                    #Timeout message will be printed out as part of GEH code.
                    #print "Time elapsed for zone-h page processing\n"

                    #Here captcha is resolved

                    cookies = browser.get_cookies()
                    cookie = ' '.join([i['name'] + '=' + i['value'] + ';' for i in cookies])

                    url = browser.find_elements_by_xpath("//*[@id='cryptogram']")[0].get_attribute('src')

                    req = urllib2.Request(url)
                    req.add_header('Cookie', cookie)
                    resp = urllib2.urlopen(req)
                    pic = resp.read()

                    f = open("captcha.png", "wb")
                    f.write(pic)
                    f.close()
                  
                    try: 
                        solution = captcha.solve_captcha('captcha.png')
                        elem = browser.find_element_by_name("captcha")
                        print "Captcha solved in process_zoneh_pages (%s).\n" % solution
                        elem.send_keys(solution)
                        elem.submit()
                    except:
                        print "Something wrong in solving captcha.\n"
                        print traceback.format_exc()
                        print "\n"

                else:
                    havepage = True
                    break

            if havepage:

                mirrors = browser.find_elements_by_link_text('mirror')
                ntdata = map(lambda x: x.find_elements_by_xpath("../../*"), mirrors)
                data = map(lambda (x, y): (x[0].text, x[1].text, y.get_attribute('href')), zip(ntdata, mirrors))

                #TODO: [HIGH PRIORITY] If there is unsuccessful processing for some page which contains (ctime, cnotifier, cmirror), code will continue
                #download next pages that have mirrors already in database. Do I deduplicate in that case?
                #CHECK DONE: in insertInDatabase is seen that new deface is always inserted in database.
                #(time, notifier_id, url, mirrorsrc) tuple gives unique deface id that can be used for deduplication

                allData += data

                if (ctime, cnotifier, cmirror) in data:
                    i = data.index((ctime, cnotifier, cmirror))
                    allData = list(reversed(allData[:i]))
                    break

            else:

                #captchas uncorrectly solved 5 times
                #TODO: save and make claim?
                pass

        except:
            print "Unsuccessful processing of zone-h.org page\n"
            print traceback.format_exc()
            print "\n"
            
    if i == -1:
        allData = list(reversed(allData))

    return allData



def process_mirror_pages(allData):

        for time, notifier, mirror in allData:

            try:

                print notifier, time, mirror

                browser_get(mirror)

                for i in range(0, ALERT_CONFIRMS + 1):       #number of alert confirmations plus content

                    try:

                        havepage = False

                        for k in range(1, 5):   #Loop of uncorrectly solved captachas

                            try:
                                WebDriverWait(browser, 10).until(
                                            EC.presence_of_element_located((By.TAG_NAME, "iframe"))   #TODO: wait for iframe OR propdeface. How to handle flows in that case?
                                            )

                            except TimeoutException as e:

                                WebDriverWait(browser, 5).until(
                                            EC.presence_of_element_located((By.ID, "propdeface"))
                                            )
                                
                                #In case of timeout on iframe, we are checking if captcha is present.
                                #If captcha is not present generic exception handling code will take over control.
                                #Next mirror page will tried to be downloaded.
                                #This differs from v0.9 that continued to scan next page immedatelly.
                                #Software robustness(resiliency) is kept.
                                #Timeout message will be printed out as part of GEH code.
                                #print "Time elapsed for zone-h page processing\n"

                                #Here captcha is resolved

                                cookies = browser.get_cookies()
                                cookie = ' '.join([i['name'] + '=' + i['value'] + ';' for i in cookies])

                                print browser.page_source

                                url = browser.find_elements_by_xpath("//*[@id='cryptogram']")[0].get_attribute('src')

                                req = urllib2.Request(url)
                                req.add_header('Cookie', cookie)
                                resp = urllib2.urlopen(req)
                                pic = resp.read()

                                f = open("captcha.png", "wb")
                                f.write(pic)
                                f.close()
                              
                                try: 
                                    solution = captcha.solve_captcha('captcha.png')
                                    print "Captcha solved in process_mirror_pages (%s).\n" % solution
                                    elem = browser.find_element_by_name("captcha")
                                    elem.send_keys(solution)
                                    elem.submit()
                                except:
                                    print "Something wrong in solving captcha.\n"
                                    print traceback.format_exc()
                                    print "\n"

                            else:
                                havepage = True
                                break   #break out of captcha solving loop



                        if havepage:

                            time_.sleep(2)  #safety hold in case HTML is not fully loaded 

                            mirrorsrc = browser.find_element_by_tag_name('iframe').get_attribute('src')
                            url = browser.find_elements_by_xpath("//*[@id='propdeface']/ul/li[2]/ul[1]/li[2]")[0].text.split(": ")[1].strip()

                            print url
                            print "\n"

                            processDefacement(time, notifier, url, mirrorsrc)
                            break   #break out of alert confirmation loop

                        else:

                            #captchas uncorrectly solved 5 times
                            #TODO: save and make claim?
                            break   #break out of alert confirmation loop


                    except UnexpectedAlertPresentException as e:
                        print "Accepting alert in process_mirror_pages.\n"
                        #confirmation of alert here
                        Alert(browser).accept()
                        if i == ALERT_CONFIRMS:
                            print traceback.format_exc()
                            print "\n"

            except:
                print "Unsuccessful processing in process_mirror_pages.\n"
                print traceback.format_exc()
                print "\n"                    




def main():


    try:
        f = open("deface.temp", "r+")

        allData = process_zoneh_pages(f)
        process_mirror_pages(allData)

        if not allData == []:
            ttime, tnotifier, tmirror = allData[-1] #index not in range error znaci da se nije pojavio novi deface page od zadnjeg pokretanja
            f.seek(0)
            f.write(ttime + "\n")
            f.write(tnotifier.encode('utf-8') + "\n")
            f.write(tmirror)
            f.truncate()
        else:
            print "There is no new web defacemens!\n"

        print "Successfully done.\n"
    except:
        print "Unsuccessfully done.\n"
        print traceback.format_exc()
        print "\n"
    finally:
        f.close()
        browser.quit()
        conn.close()
 


print "--------------------------------------------------------------------%s\
---------------------------------------------------------------------\n"  % (time.strftime("%c"),)
main()


