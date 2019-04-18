import re
import urllib2
import urllib
import urlparse
import socket

# sniff for python2.x / python3k compatibility "fixes'
try:
    basestring = basestring
except NameError:
    # 'basestring' is undefined, must be python3k
    basestring = str

try:
    next = next
except NameError:
    # builtin next function doesn't exist
    def next (iterable):
        return iterable.next()


_DOTTED_QUAD_RE = re.compile(r'^(\d{1,3}\.){0,3}\d{1,3}$')

def validate_ip(s):
    if _DOTTED_QUAD_RE.match(s):
        quads = s.split('.')
        for q in quads:
            if int(q) > 255:
                return False
        return True
    return False

_CIDR_RE = re.compile(r'^(\d{1,3}\.){0,3}\d{1,3}/\d{1,2}$')

def validate_cidr(s):
    if _CIDR_RE.match(s):
        ip, mask = s.split('/')
        if validate_ip(ip):
            if int(mask) > 32:
                return False
        else:
            return False
        return True
    return False

def ip2long(ip):
    if not validate_ip(ip):
        return None
    quads = ip.split('.')
    if len(quads) == 1:
        # only a network quad
        quads = quads + [0, 0, 0]
    elif len(quads) < 4:
        # partial form, last supplied quad is host address, rest is network
        host = quads[-1:]
        quads = quads[:-1] + [0,] * (4 - len(quads)) + host

    lngip = 0
    for q in quads:
        lngip = (lngip << 8) | int(q)
    return lngip

_MAX_IP = 0xffffffff

def long2ip(l):
    if _MAX_IP < l < 0:
        raise TypeError("expected int between 0 and %d inclusive" % _MAX_IP)
    return '%d.%d.%d.%d' % (l>>24 & 255, l>>16 & 255, l>>8 & 255, l & 255) 

def cidr2block(cidr):
    if not validate_cidr(cidr):
        return None

    ip, prefix = cidr.split('/')
    prefix = int(prefix)

    # convert dotted-quad ip to base network number
    # can't use ip2long because partial addresses are treated as all network 
    # instead of network plus host (eg. '127.1' expands to '127.1.0.0')
    quads = ip.split('.')
    baseIp = 0
    for i in range(4):
        baseIp = (baseIp << 8) | int(len(quads) > i and quads[i] or 0)

    # keep left most prefix bits of baseIp
    shift = 32 - prefix
    start = baseIp >> shift << shift

    # expand right most 32 - prefix bits to 1
    mask = (1 << shift) - 1
    end = start | mask
    return (long2ip(start), long2ip(end))

_RIPE_WHOIS = 'riswhois.ripe.net' 
_ASN_CACHE = {}

def ip2asn(ip):
    global _ASN_CACHE
    
    # ako nije u pitanju lista onda odmah trazimo IP adresu
    # u cacheu i vracamo ju
    if type(ip) is not list and ip in _ASN_CACHE:
       return _ASN_CACHE[ip]
        
    try:
        ripeip = socket.gethostbyname(_RIPE_WHOIS)
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((ripeip,43))
        #s.recv(4096)
    except socket.gaierror:
        raise AsnResolutionError('Could not resolve RIPE server name')
    except socket.error:
        raise AsnResolutionError('Error connecting to whois server')
    
    if type(ip) is list:
        # u slucaju da je upit lista IP adresa, treba svaku provjeriti
        result = {}
        for i in ip:
            # prvo provjera da li je IP adresa u cacheu, ako nije
            # kontaktiramo server i saljemo upit te dodajemo u cache
            if i in _ASN_CACHE:
                result[i] = _ASN_CACHE[i]
            else:
                try:
                    s.send('-k -F -M %s\r\n' % i)
                    result[i] = _ASN_CACHE[i] = _parse_whois(s.recv(4096))
                except AsnResolutionError, socket.error:
                    # TODO: popraviti ovo, ako je doslo do pogreske trenutno se
                    # vraca prazan string sto znaci da nema ASN-a
                    result[i] = ''
        s.close()
        return result
    else:
        # u slucaju da je upit jedna IP adresa koja nije u cacheu
        s.send('-F -M %s\r\n' % ip)
        _ASN_CACHE[ip] = asn = _parse_whois(s.recv(4096))
        s.close()
        return asn
    
def url2host(url):
    host = urlparse.urlparse(url).hostname
    if not host:
        host = urlparse.urlparse('http://' + url).hostname
    if not host:
        raise HostResolutionError('Could not parse hostname')
    
    return host

def url2ip(url):
    try:
        return socket.gethostbyname(url2host(url))
    except socket.gaierror:
        raise HostResolutionError('No IP address for host')

def url2tld(url):
    host = url2host(url)
    if '.' in host:
        return host.split('.')[-1:][0]
    else:
        raise HostResolutionError('No valid TLD in hostname')

#_GOOGLE_KEY = 'ABQIAAAAxYjVDAFhAe3o3ORFz0M4WhSRANfPA86NpChaGS3JPxvpQtPEMg'
_GOOGLE_KEY = 'ABQIAAAA91BfexGg9gwOzbZ1zsgJOBQDSU0_BEb6BufZ5pmVD4AMkVBbaA'
_GOOGLE_URL = 'https://sb-ssl.google.com/safebrowsing/api/lookup?client=python&apikey=%s&appver=1.5.2&pver=3.0&url=%s'

def _check_google(url):
    gurl = _GOOGLE_URL % (_GOOGLE_KEY, urllib.quote(url))
    result = urllib2.urlopen(gurl)
    if result.getcode() == 204:
        return False
    if result.getcode() == 200:
        return True

_BLACKLIST_CACHE = {}
       
def url_blacklisted(url):
    global _BLACKLIST_CACHE
    
    if url in _BLACKLIST_CACHE:
        return _BLACKLIST_CACHE[url]
     
    try:
        _BLACKLIST_CACHE[url] = _check_google(url)
        return _BLACKLIST_CACHE[url]
    except urllib2.URLError, e:
        raise BlacklistCheckError(str(e))
            
class IpRange(object):
    def __init__ (self, start, end=None):
        if end is None:
            if isinstance(start, tuple):
                # occurs when IpRangeList calls via map to pass start and end
                start, end = start
            elif validate_cidr(start):
                # CIDR notation range
                start, end = cidr2block(start)
            else:
                # degenerate range
                end = start

        start = ip2long(start)
        end = ip2long(end)
        self.startIp = min(start, end)
        self.endIp = max(start, end)

    def __repr__ (self):
        return (long2ip(self.startIp), long2ip(self.endIp)).__repr__()

    def __contains__ (self, item):
        if isinstance(item, basestring):
            item = ip2long(item)
        if type(item) not in [type(1), type(_MAX_IP)]:
            raise TypeError("expected dotted-quad ip address or 32-bit integer")

        return self.startIp <= item <= self.endIp

    def __iter__ (self):
        i = self.startIp
        while i <= self.endIp:
            yield long2ip(i)
            i += 1

class IpRangeList(object):
    def __init__ (self, args):
        self.ips = tuple(map(IpRange, args))

    def __repr__ (self):
        return self.ips.__repr__()

    def __contains__ (self, item):
        for r in self.ips:
            if item in r:
                return True
        return False
        
    def __iter__ (self):
        for r in self.ips:
            for ip in r:
                yield ip
                
_RIPE_IP_URL = 'ftp://ftp.ripe.net/ripe/stats/delegated-ripencc-latest'

_RANGE_CACHE = {}

_RIPE_DATA = None

class AddressSpace(object):
    def __init__(self, tld, range=None):
        self._tld = tld.upper()

        if range:
            self._range = IpRangeList(range)
        else:
            self._range = self._load_range(tld.upper())
    
    def _load_range(self, cc):
        global _RANGE_CACHE
        global _RIPE_DATA

        if cc.upper() in _RANGE_CACHE:
            return _RANGE_CACHE[cc.upper()]

        if _RIPE_DATA==None:
            _RIPE_DATA = urllib.urlopen(_RIPE_IP_URL).readlines()
        ranges = filter(lambda x: x.find(cc.upper()) is not -1 and x.find('ipv4') is not -1, _RIPE_DATA)
        ranges_list = []
        for r in ranges:
            start = r.split('|')[3]
            end = long2ip(ip2long(start) + int(r.split('|')[4]))
            ranges_list.append((start,end))

        _RANGE_CACHE[cc.upper()] = IpRangeList(ranges_list)
        return _RANGE_CACHE[cc.upper()]
    
    def __contains__ (self, item):
        if validate_ip(item):
            if item in self._range:
                return True
        else:
            if url2tld(item).lower() == self._tld:
                return True
            if url2ip(item) in self._range:
                return True
        return False

class HostResolutionError(Exception):
    pass
    
class AsnResolutionError(Exception):
    pass
    
class BlacklistCheckError(Exception):
    pass
    
# interna funkcija koja parsira reply whois servera i iz njega
# vadi van ASN broj, baca iznimku ako to ne moze napraviti
def _parse_whois(data):
    data = filter(lambda x: x and not x.startswith('%'), ''.join(data).split('\n'))
    if len(data) <> 1:
        raise AsnResolutionError('Invalid reply from whois server')
        
    asn = data[0].split('\t')
    if len(asn) <> 2:
        raise AsnResolutionError('Invalid reply from whois server')
    
    if asn[0] == '3303':
        return ''
    else:
        return asn[0]

def ip_in_tlds(ipurl, tlds):
    """ provjera je li IP u rangeu provajdanih TLDova (zemalja) (c) fvlasic
    """
    for tld in tlds:
        if ipurl in AddressSpace(tld=tld):
            return tld.upper()
    return False


def cymruIP2ASN(ips):
    addr = ('whois.cymru.com', '43')
    sock = socket.create_connection(addr)
    query='begin\ncountrycode\nasnumber\nnoasname\n[insert]end\n'

    ips_on_wire = ""
    if isinstance(ips, basestring):
        ips = [ips]
    for ip in ips:
        ips_on_wire = ips_on_wire + ip + "\n"
    query = query.replace('[insert]', ips_on_wire)

    sent = 0
    while not sent==len(query):
        sendbytes = sock.send(query[sent:])
        sent += sendbytes

    data=''
    more = True
    while more:
        more = sock.recv(8192)
        data += more

    sock.close()

    return dict(map(lambda x: (x.split('|')[1].strip(), \
                (x.split('|')[0].strip(), x.split('|')[2].strip())), filter(lambda x: '|' in x, data.split('\n'))))
        
 
