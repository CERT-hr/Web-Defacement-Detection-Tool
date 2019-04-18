
import urllib2
import json
import dns.resolver
import iptoolsng
import traceback
import signal



def getHrDomains():

    URL = 'https://registrar.carnet.hr/data/activedomains'

    domains = urllib2.urlopen(URL).read()

    domains = json.loads(domains)

    return map(lambda x: x['domain_name'], domains)



def getDomainsIP(domains):

    result = {}

    def handler(signum, frame):
        f = open("domainsips.hr", "w")
        json.dump(result, f)
        f.close()

    signal.signal(signal.SIGPROF, handler)
    signal.setitimer(signal.ITIMER_PROF, 0.2, 0.2)

    dnsresolver = dns.resolver.Resolver()
    dnsresolver.nameservers = ['8.8.8.8']

    dnum = len(domains)

    for domain, num in zip(domains, range(1, dnum + 1)):

        print "%s (%d/%d)" % (domain, num, dnum)

        try:
            r = dnsresolver.query(domain, 'A')
            ip = str(r[0])
            if iptoolsng.validate_ip(ip):
                result[domain] = ip
            else:
                result[domain] = 'Not valid IPv4'
        except dns.exception.DNSException:
            try:
                r = dnsresolver.query('www.' + domain, 'A')
                ip = str(r[0])
                if iptoolsng.validate_ip(ip):
                    result['www.' + domain] = ip
                else:
                    result['www.' + domain] = 'Not valid IPv4'
            except dns.exception.DNSException:
                try:
                    r = dnsresolver.query(domain, 'AAAA')
                    result[domain] = str(r[0])
                except dns.exception.DNSException:
                    result[domain] = "No IPv4 nor IPv6 record"
        except:
            result[domain] = 'Error'
            print "------------------------------------------------------------\n"
            print traceback.format_exc()



def IPsToASNQueues():

    result = {}

    f = open("domainsips.hr", "r")

    domainsips = json.load(f)

    f.close()

    #clean domains list of non IP codes

    domainsips = filter(lambda (x, y): not y == 'Error' and not y == 'No IPv4 nor IPv6 record', domainsips.items())

    domains = map(lambda (x, y): x, domainsips)

    ips = map(lambda (x, y): y, domainsips)

    ipsToASN = iptoolsng.cymruIP2ASN(ips)

    for domain, ip in domainsips:

        asn = ipsToASN[ip][0]

        if not asn in result:
            result[asn] = [domain]
        else:
            result[asn].append(domain)

    return result

