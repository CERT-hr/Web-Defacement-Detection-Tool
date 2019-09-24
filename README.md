Development of this tool was a part of the Action "Increase of National CERT capacities and enhancement of cooperation on national and  European level - GrowCERT" which was co-financed through the Connecting Europe Facility (CEF) Telecom program of the European Commission, contract number: INEA / CEF / ICT / A2016 / 1334308 (Action No: 2016-HR-IA-0085)

The contents of this tool is the sole responsibility of Croatian Academic and Research Network - CARNET / National CERT and do not necessarily reflect the opinion of the European Union. 

# Web Defacement Detection Tool

This tool uses archived defaced websites as source for learning about *defacement signatures*. 
Defacement signature is basic concept in this tool, and represents set of elements that are typical for specific defacer (notifier). 
Having knowledge of one’s signature (or signatures), it is possible to detect similar web defacements in future, 
or detect/prevent defacement hacking action on server side. 
Defacement signature is represented with **5 types** of web elements that are typical for any defacer. 
Those elements are: all visible text, Images, backgroundImages, alerts, embedded audio or video content. 
Detection of these signatures is not trivial, as sometimes signature elements are embedded as part of legitimate website. 
Therefore, we are encountering problem of elimination of elements that are not part of signature. 
Idea, algorithm and whole theory behind algorithm concerning *signature noise elimination* is fully covered in DEFACEMENTS.docx.

Tool consists of four Python scripts, and one PostgreSQL database.

### collector.py
This script uses Chrome web driver controlled over Selenium to access HTML elements of archived defaced website. 
Script also navigates trough list of reported defacements on publishing source (zone-h.org). 
All defacements are collected periodically and stored in database with complete set of elements from defaced webpage representation. 
Each defacement is associated with notifier in database.

### processor.py
This script takes care of maintaining database size, 
generating defacement signatures and deleting old signatures that are not used anymore by defacers. 
As complete content of webpages is saved in database, we need to deal with problem of fast growing database size. 
Old defacements that does not anymore represent significant input to signature detection algorithm are deleted from database. 
All defacements from past 6 months are left in database for possible future testing with algorithm. 
Script takes necessary input from database and calls for signature detection algorithm, 
then saves resulting signature output back to database. All signatures older than 3 years are deleted from database.

### crawler.py
Script reads domains.list file and scans all URLs in file for possible signature detection. 
Chrome web driver over Selenium is used to retrieve elements from scanned webpages, which are then compared against detected signatures. 
Comparison algorithm is to be further improved and described afterwards. 
Script returns scan result for each URL, with information if any signature and associated defacer are detected.

### WebDfcAlg.py
Script implementing signature noise elimination algorithm. Algorithm is described in DEFACEMENTS.docx in detail.


### schema.sql
pg_dump generated database schema 

![alt text]https://raw.githubusercontent.com/HR-CERT/Web-Defacement-Detection-Tool/master/en_horizontal_cef_logo_2.png
