import socket
import urllib2
import time


POST = lambda cntlen, pic: '''\
POST /in.php HTTP/1.1\r\n\
HOST: 2captcha.com\r\n\
Connection: keep-alive\r\n\
Content-Length: %d\r\n\
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryAQUtZWIPknqRJqiz\r\n\
\r\n\
------WebKitFormBoundaryAQUtZWIPknqRJqiz\r\n\
Content-Disposition: form-data; name="method"\r\n\
\r\n\
post\r\n\
------WebKitFormBoundaryAQUtZWIPknqRJqiz\r\n\
Content-Disposition: form-data; name="key"\r\n\
\r\n\
0e748f31b75a4cfb3a669d7abe18f9dd\r\n\
------WebKitFormBoundaryAQUtZWIPknqRJqiz\r\n\
Content-Disposition: form-data; name="file"; filename="captcha.png"\r\n\
Content-Type: application/octet-stream\r\n\
\r\n\
%s\r\n\
------WebKitFormBoundaryAQUtZWIPknqRJqiz--\r\n\
''' % (cntlen, pic)



def send_request(sock, msg):

        MSGLEN = len(msg)
        totalsent = 0
        while totalsent < MSGLEN:
                try:
                        sent = sock.send(msg[totalsent:])
                except socket.error as e:
                        raise BrokenSocketError("Cannot send to socket") #slomljena pipa

                #if sent == 0:
                #        raise RuntimeError("socket connection broken")

                totalsent = totalsent + sent




def read_response(sock):
        #download headera
        header = ''
        while header[-4:] != '\r\n\r\n':
                byte = sock.recv(1)

                if byte == '':
                        raise BrokenSocketError("Cannot receive on socket") #slomljena pipa

                header += byte

        #TODO:Predpostavljam da body postoji
        body = ''
        if 'Transfer-Encoding: chunked' in header:
                #download body
                while True:
                        chunk = ''
                        chunk_size = ''
                        while True:
                                #detect size
                                byte = sock.recv(1)

                                if byte == '':
                                        raise BrokenSocketError("Cannot receive on socket") #slomljena pipa

                                chunk_size += byte
                                if ';' in chunk_size:
                                        chunk_size = int('0x' + chunk_size.split(';')[0], 16)
                                        break
                                elif '\r\n' in chunk_size:
                                        chunk_size = int('0x' + chunk_size.split('\r\n')[0], 16)
                                        break
                                else:
                                        pass

                        if chunk_size == 0:
                                #ostalo za procitat trailer + CRLF
                                trailer = ''
                                while (trailer[-2:] != '\r\n' and ';' not in trailer) or\
                                                (trailer[-4:] != '\r\n\r\n' and ';' in trailer):        #trailer postoji ili nepostoji
                                        byte = sock.recv(1)
                                        if byte == '':
                                                raise BrokenSocketError("Cannot receive on socket") #slomljena pipa
                                        trailer += byte
                                break

                        REAL_CHUNK_SIZE = chunk_size + 2        #plus \r\n
                        while len(chunk) < REAL_CHUNK_SIZE:
                                bytes_ = sock.recv(REAL_CHUNK_SIZE - len(chunk))
                                if bytes_ == '':
                                        raise BrokenSocketError("Cannot receive on socket") #slomljena pipa

                                chunk += bytes_

                        body += chunk[:-2]

        return body



host = "2captcha.com"
port = 80

def solve_captcha(imagepath):

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)        #max blocking na citanje/pisanje
    sock.connect((host, port))

    f = open(imagepath, "rb")
    pic = f.read()
    f.close()

    boundary = '------WebKitFormBoundaryAQUtZWIPknqRJqiz'

    emptypost =  POST(0, '')

    pos = len(emptypost) - emptypost.find(boundary)
    cntlen = len(pic) + pos

    send_request(sock, POST(cntlen, pic))
    taskid = read_response(sock).split('|')[1]

    output = 'CAPCHA_NOT_READY'
    repeat = 0

    while output == 'CAPCHA_NOT_READY' and repeat < 7:
        
        time.sleep(5)

        f = urllib2.urlopen("http://2captcha.com/res.php?key=0e748f31b75a4cfb3a669d7abe18f9dd&action=get&id=%s" % (taskid,))

        repeat += 1

        output = f.read()

    return output.split('|')[1]
    
    







