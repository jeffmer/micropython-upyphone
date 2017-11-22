# Driver for SIM800L module (using AT commands)
# MIT License; Copyright (c) 2017 Jeffrey N. Magee


import pyb
import math

# kludge required because "ignore" parameter to decode not implemented
def convert_to_string(buf):
    try:
        tt =  buf.decode('utf-8').strip()
        return tt
    except UnicodeError:
        tmp = bytearray(buf)
        for i in range(len(tmp)):
            if tmp[i]>127:
                tmp[i] = ord('#')
        return bytes(tmp).decode('utf-8').strip()

class SIM800LError(Exception):
    pass

def check_result(errmsg,expected,res):
    if not res:
        res = 'None'
    #print(errmsg+res)
    if not expected == res and not res == 'None':
        raise SIM800LError('SIM800L Error {}  {}'.format(errmsg,res))


class SIM800L:

    def __init__(self,uartno):  # pos =1 or 2 depending on skin position
        self._uart = pyb.UART(uartno, 9600, read_buf_len=2048)
        self.incoming_action = None
        self.no_carrier_action = None
        self.clip_action = None
        self._clip = None
        self.msg_action = None
        self._msgid = 0
        self.savbuf = None
        self.credit = ''
        self.credit_action = None
        
    def callback_incoming(self,action):
        self.incoming_action = action

    def callback_no_carrier(self,action):
        self.no_carrier_action = action
    
    def callback_clip(self,action):
        self.clip_action = action
    
    def callback_credit_action(self,action):
        self.credit_action = action

    def get_clip(self):
        return self._clip
        
    def callback_msg(self,action):
        self.msg_action = action

    def get_msgid(self):
        return self._msgid
    
    def command(self, cmdstr, lines=1, waitfor=500, msgtext=None):
        #flush input
        #print(cmdstr)
        while self._uart.any():
            self._uart.readchar()
        self._uart.write(cmdstr)
        if msgtext:
            self._uart.write(msgtext)
        if waitfor>1000:
            pyb.delay(waitfor-1000)
        buf=self._uart.readline() #discard linefeed etc
        #print(buf)
        buf=self._uart.readline()
        #print(buf)
        if not buf:
            return None
        result = convert_to_string(buf)
        if lines>1:
            self.savbuf = ''
            for i in range(lines-1):
                buf=self._uart.readline()
                if not buf:
                    return result
                #print(buf)
                buf = convert_to_string(buf)
                if not buf == '' and not buf == 'OK':
                    self.savbuf += buf+'\n'
        return result
    
    def setup(self):
        self.command('ATE0\n')         # command echo off
        self.command('AT+CRSL=99\n')   # ringer level
        self.command('AT+CMIC=0,10\n') # microphone gain
        self.command('AT+CLIP=1\n')    # caller line identification
        self.command('AT+CMGF=1\n')    # plain text SMS
        self.command('AT+CALS=3,0\n')  # set ringtone
        self.command('AT+CLTS=1\n')    # enabke get local timestamp mode
        self.command('AT+CSCLK=0\n')   # disable automatic sleep
        
    def wakechars(self):
        self._uart.write('AT\n')        # will be ignored
        pyb.delay(100)
    
    def sleep(self,n):
        self.command('AT+CSCLK={}\n'.format(n))
            
    def sms_alert(self):
        self.command('AT+CALS=1,1\n')  # set ringtone
        pyb.delay(3000)
        self.command('AT+CALS=3,0\n')  # set ringtone
  
    def call(self,numstr):
        self.command('ATD{};\n'.format(numstr))
        
    def hangup(self):
        self.command('ATH\n')     
        
    def answer(self):
        self.command('ATA\n')
    
    def set_volume(self,vol):
        if (vol>=0 and vol<=100):
            self.command('AT+CLVL={}\n'.format(vol))
    
    def signal_strength(self):
        result = self.command('AT+CSQ\n',3)
        if result:
            params=result.split(',')
            if not params[0] == '':
                params2 = params[0].split(':')
                if params2[0]=='+CSQ':
                    x = int(params2[1])
                    if not x == 99:
                        return(math.floor(x/6+0.5))
        return 0
        
    def battery_charge(self):   
        result = self.command('AT+CBC\n',3,1500)
        if result:
            params=result.split(',')
            if not params[0] == '':
                params2 = params[0].split(':')
                if params2[0]=='+CBC':
                    return int(params[1])
        return 0
        
    def network_name(self):   
        result = self.command('AT+COPS?\n',3)
        if result:
            params=result.split(',')
            if not params[0] == '':
                params2 = params[0].split(':')
                if params2[0]=='+COPS':
                    if len(params)>2:
                        names = params[2].split('"')
                        if len(names)>1:
                            return names[1]
        return ''


    def read_sms(self,id):
        result = self.command('AT+CMGR={}\n'.format(id),99)
        if result:
            params=result.split(',')
            if not params[0] == '':
                params2 = params[0].split(':')
                if params2[0]=='+CMGR':
                    number = params[1].replace('"',' ').strip()
                    date   = params[3].replace('"',' ').strip()
                    time   = params[4].replace('"',' ').strip()
                    return  [number,date,time,self.savbuf]
        return None
    
    def send_sms(self,destno,msgtext):
        result = self.command('AT+CMGS="{}"\n'.format(destno),99,5000,msgtext+'\x1A')
        if result and result=='>' and self.savbuf:
            params = self.savbuf.split(':')
            if params[0]=='+CUSD' or params[0] == '+CMGS':
                return 'OK'
        return 'ERROR'
    
    def check_credit(self):
        self.command('AT+CUSD=1,"*100#"\n')
    
    def get_credit(self):
        return self.credit
    
    def delete_sms(self,id):
        self.command('AT+CMGD={}\n'.format(id),1)
                     
    def date_time(self):
        result = self.command('AT+CCLK?\n',3)
        if result:
            if result[0:5] == "+CCLK":
                return result.split('"')[1]
        return ''
        
    def check_incoming(self): 
        if self._uart.any():
            buf=self._uart.readline()
            # print(buf)
            buf = convert_to_string(buf)
            params=buf.split(',')
            if params[0] == "RING":
                if self.incoming_action:
                    self.incoming_action()
            elif params[0][0:5] == "+CLIP":
                params2 = params[0].split('"')
                self._clip = params2[1]
                if self.clip_action:
                    self.clip_action()
            elif params[0][0:5] == "+CMTI":
                self._msgid = int(params[1])
                if self.msg_action:
                    self.msg_action()
            elif params[0][0:5] == "+CUSD":
                if len(params)>1:
                    st = params[1].find('#')
                    en = params[1].find('.',st)
                    en = params[1].find('.',en+1)
                    if st>0 and en>0:
                        self.credit = '£'+params[1][st+1:en]
                        if self.credit_action:
                            self.credit_action()
            elif params[0] == "NO CARRIER":
                    self.no_carrier_action()


    # http get command using gprs
    def http_get(self,url,apn="giffgaff.com"):
        resp = None
        rstate = 0
        proto, dummy, surl = url.split("/", 2)
        is_ssl = 0
        if  proto == "http:":
            is_ssl = 0
        elif proto == "https:":
            is_ssl == 1
        else:
            raise ValueError("Unsupported protocol: " + proto)
        try:
            # open bearer context
            res = self.command('AT+SAPBR=3,1,"Contype","GPRS"\n')
            check_result("SAPBR 1: ",'OK',res)
            res = self.command('AT+SAPBR=3,1,"APN","{}"\n'.format(apn))
            check_result("SAPBR 2: ",'OK',res)
            res = self.command('AT+SAPBR=1,1\n',1,2000)
            check_result("SAPBR 3: ",'OK',res)
            # now do http request
            res = self.command('AT+HTTPINIT\n',1)
            check_result("HTTPINIT: ",'OK',res)
            res = self.command('AT+HTTPPARA="CID",1\n')
            check_result("HTTPPARA 1: ",'OK',res)
            res = self.command('AT+HTTPPARA="URL","{}"\n'.format(surl))
            check_result("HTTPPARA 2: ",'OK',res)
            res = self.command('AT+HTTPSSL={}\n'.format(is_ssl))
            check_result("HTTPSSL: ",'OK',res)
            res = self.command('AT+HTTPACTION=0\n')
            check_result("HTTPACTION: ",'OK',res)
            for i in range(20):  #limit wait to max 20 x readline timeout
                buf = self._uart.readline()
                if buf and not buf==b'\r\n':
                    buf = convert_to_string(buf)
                    #print(buf)
                    prefix,retcode,bytes = buf.split(',')
                    rstate = int(retcode)
                    nbytes = int(bytes)
                    break
            res = self.command('AT+HTTPREAD\n',1)
            buf = self._uart.read(nbytes)
            check_result("HTTPACTION: ",'+HTTPREAD: {}'.format(nbytes),res)
            if buf[-4:] == b'OK\r\n':  # remove final OK if it was read
                buf = buf[:-4]
            resp = Response(buf)
        except SIM800LError as err:
            print(str(err))
        self.command('AT+HTTPTERM\n',1) # terminate HTTP task
        self.command('AT+SAPBR=0,1\n',1) # close Bearer context
        return resp


    def test(self):
        r = self.http_get('http://exploreembedded.com/wiki/images/1/15/Hello.txt')
        print(r.text)


    
 
 
class Response:
    
    def __init__(self, buf, status = 200):
        self.encoding = "utf-8"
        self._cached = buf
        self.status = status
    
    def close(self):
        self._cached = None
    
    @property
    def content(self):
        return self._cached
    
    @property
    def text(self):
        return str(self.content, self.encoding)
    
    def json(self):
        import ujson
        return ujson.loads(self.content)

