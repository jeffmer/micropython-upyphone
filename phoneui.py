# MIT License; Copyright (c) 2017 Jeffrey N. Magee

"""
Combines User Interface with SIM800L module. 
"""

import pyb
import lcd160cr
import sim800l
import gc

phonebook = {"Jeff"  :"+xxxxxxxxxxxx",
             "Home"  :"+xxxxxxxxxxxx",
             "John"  :"+xxxxxxxxxxxx",
             "Judith":"+xxxxxxxxxxxx",
             "Lottie":"+xxxxxxxxxxxx",
             "Cleder":"+xxxxxxxxxxxx"}

inverted_pb = dict((v,k) for k,v in phonebook.items())
national_pb = dict((v.replace('+44','0'),k) for k,v in phonebook.items())

from  ui import DialScreen, CallScreen, HomeScreen, PhoneBookScreen, SettingsScreen, MessageScreen, SendsmsScreen

lcd = lcd160cr.LCD160CR('Y')
lcd.set_orient(lcd160cr.PORTRAIT_UPSIDEDOWN)
dial = DialScreen(lcd, 'Dial')
call = CallScreen(lcd, 'Calling')
incoming = CallScreen(lcd, 'Incoming',True)
home = HomeScreen(lcd, 'UpyPhone')
book = PhoneBookScreen(lcd, 'Phone Book', phonebook)
messages = MessageScreen(lcd,'Messages')
sendsms = SendsmsScreen(lcd,'')
settings = SettingsScreen(lcd, 'Settings')
phone = sim800l.SIM800L(4)

current = home
count = 300
period = 0
bright_level = 31
volume_level = 33
new_sms = False


def switch_to(screen):
    global current, period
    current = screen
    current.draw()
    if current == home:
        period = 145

def docall():
    switch_to(call)
    call.set_number(dial.get_number())
    phone.call(dial.get_number())

msg_destination = ''

def dosms():
    global msg_destination
    switch_to(sendsms)
    msg_destination = dial.get_number()
    sendsms.set_destination(msg_destination)

def dosendsms():
    sendsms.set_destination('  SENDING')
    result = phone.send_sms(msg_destination, sendsms.get_msgtext())
    sendsms.set_destination(result)
    
def set_call():
    dial.callback_call(docall)
    switch_to(dial)
    
def set_sms():
    dial.callback_call(dosms)
    switch_to(dial)

def incomingcall():
    switch_to(incoming)
    clear_phone_sleep_mode()
    
def phonebookcall(name):
    global msg_destination
    if book.callmode():
        switch_to(call)
        call.set_number(name)
        phone.call(phonebook[name])
    else:
        switch_to(sendsms)
        msg_destination = phonebook[name]
        sendsms.set_destination(name)

def incomingclip():
    global inverted_pb, national_pb
    if current == incoming:
        nn = phone.get_clip()
        if nn in inverted_pb:
            nn = inverted_pb[nn]
        elif nn in national_pb:
            nn = national_pb[nn]
        incoming.set_number(nn)

def no_carrier():
    switch_to(home)
    clear_phone_sleep_mode()

def docancel():
    dial.set_number(' ')
    switch_to(home)

def cancelcall():
    switch_to(home)
    phone.hangup()
    
def answercall():
    phone.answer()
    
def set_brightness(level):
    global bright_level
    bright_level = level
    lcd.set_brightness(bright_level)

def set_volume(level):
    global volume_level
    volume_level = level
    phone.set_volume(volume_level)

def incoming_sms():
    global new_sms
    switch_to(home)
    clear_phone_sleep_mode()
    id = phone.get_msgid()
    home.set_smsid(id)
    new_sms = True
    phone.sms_alert()

def display_msg(id):
    global msg_destination, inverted_pb
    current_msg = phone.read_sms(id)
    if current_msg:
        msg_destination = current_msg[0]
        if msg_destination in inverted_pb:
            current_msg[0] = inverted_pb[msg_destination]
        messages.set_message(current_msg)
    else:
        msg_destination = ''
        messages.set_message(None)
    messages.set_id(id)

def do_messages():
    global new_sms
    home.clear_sms()
    switch_to(messages)
    if new_sms:
        id = phone.get_msgid()
        new_sms =False
    else:
        id = messages.get_id()
    display_msg(id)

def do_msg_plus():
    id = messages.get_id();
    if id<65:
        id = id+1
        display_msg(id)

def do_msg_minus():
    id = messages.get_id();
    if id>1:
        id = id-1
        display_msg(id)

def do_msg_reply():
    global msg_destination
    if not msg_destination == '':
        switch_to(sendsms)
        sendsms.set_destination(msg_destination)

def do_msg_delete():
    id = messages.get_id()
    phone.delete_sms(id)
    display_msg(id)


hasnetname = False
def update():
    global period
    global hasnetname
    home.set_date_time(phone.date_time())
    home.set_signal_level(phone.signal_strength())
    home.set_battery_level(phone.battery_charge())
    if not hasnetname:
        ns = phone.network_name()
        if not ns == '':
            home.set_network(ns)
            hasnetname = True

def check_credit():
    phone.check_credit()
    settings.set_credit('Checking..')

def set_credit():
    switch_to(settings)
    settings.set_credit(phone.get_credit())

def dosettings():
    switch_to(settings)
    settings.set_memfree(str(gc.mem_free()))
    
wokenby = 0

def clear_phone_sleep_mode():
    global wokenby
    if wokenby == 2:
        phone.wakechars()
        phone.sleep(0)
        wokenby = 0
        
def do_wakebutton(t):
    global wokenby
    wokenby = 1
    
def do_phonering(t):
    global wokenby
    wokenby = 2

wakebutton = pyb.ExtInt('X12', pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_UP, do_wakebutton)
phonering = pyb.ExtInt('X5', pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_UP, do_phonering)

dial.callback_cancel(docancel)
call.callback_cancel(cancelcall)
home.callback_call(set_call)
home.callback_sms (set_sms)
home.callback_book(lambda x=book: switch_to(x))
home.callback_message(do_messages)
home.callback_settings(dosettings)
book.callback(phonebookcall)
book.callback_back(lambda x=home: switch_to(x))
settings.callback_bright(set_brightness)
settings.callback_volume(set_volume)
settings.callback_back(lambda x=home: switch_to(x))
settings.callback_checkcredit(check_credit)
messages.callback_back(lambda x=home: switch_to(x))
messages.callback_plus(do_msg_plus)
messages.callback_minus(do_msg_minus)
messages.callback_reply(do_msg_reply)
messages.callback_delete(do_msg_delete)
phone.callback_incoming(incomingcall)
phone.callback_no_carrier(no_carrier)
phone.callback_clip(incomingclip)
phone.callback_msg(incoming_sms)
phone.callback_credit_action(set_credit)
incoming.callback_answer(answercall)
incoming.callback_cancel(cancelcall)
sendsms.callback_cancel(lambda x=home: switch_to(x))
sendsms.callback_send(dosendsms)

lcd.set_brightness(bright_level)
phone.set_volume(volume_level)
current.draw()
phone.setup()
usb = pyb.USB_VCP()

while True:
    phone.check_incoming()
    try: 
        t,x,y = lcd.get_touch()
        current.check(t,x,y)
        if period == 0:
            if current==home:
                update()
            elif current == settings:
                settings.set_memfree(str(gc.mem_free()))
        period =  (period + 1) % 150
        if t:
            count = 300
        else:
            count = count - 1
            if count<=0 and not current == incoming and not current == call: 
                #sleep
                lcd.set_power(0)
                phone.sleep(2)
                if not usb.isconnected():
                    pyb.stop()     # wait for button or incoming call    
                else:
                    wokenby = 0
                    while wokenby == 0:
                        pyb.delay(100)
                #wakeup         
                count = 300
                period = 145         
                lcd.set_power(1)
                lcd.set_orient(lcd160cr.PORTRAIT_UPSIDEDOWN)
                lcd.set_brightness(bright_level)
                if wokenby ==1:
                    phone.wakechars()
                    phone.sleep(0)
                    current.draw()
                    wokenby==0
    except OSError:
        print('Error')
        t = False   
    pyb.delay(100)    
        

    
 