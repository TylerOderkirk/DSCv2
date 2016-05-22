#!/usr/bin/python
# ----------------------------
# --- DSC2 UI THREAD
#----------------------------
from time import sleep
import RPi.GPIO as GPIO
import iodef
from threading import *
from yubikey import Yubikey
from display import Display

class UI(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.event = Event()

        GPIO.add_event_detect(iodef.PIN_KEY_UP, GPIO.FALLING, callback=self.key_up, bouncetime=150)
        GPIO.add_event_detect(iodef.PIN_KEY_DOWN, GPIO.FALLING, callback=self.key_down, bouncetime=150)
        GPIO.add_event_detect(iodef.PIN_KEY_LEFT, GPIO.FALLING, callback=self.key_left, bouncetime=150)
        GPIO.add_event_detect(iodef.PIN_KEY_RIGHT, GPIO.FALLING, callback=self.key_right, bouncetime=150)
        GPIO.add_event_detect(iodef.PIN_KEY_ENTER, GPIO.FALLING, callback=self.key_enter, bouncetime=150)
        GPIO.add_event_detect(iodef.PIN_KEY_BACK, GPIO.FALLING, callback=self.key_back, bouncetime=150)

        self.yubikey = Yubikey(self.yubikey_status, self.yubikey_auth)
        self.yubikey.start()

        self.display = Display()
        self.display.start()
        self.display.lock()

        self.idle = False
        print "Initialized UI Thread."

    def run(self):
        self.event.wait(1)
        while not self.event.is_set():
            #print "Handling UI Stuff"
            self.event.wait(5)
            if self.idle:
                self.display.idle()
                self.idle = False
            else:
                self.idle = True
        print "ui thread should be dead"

    def stop(self):
        print "Stopping UI Thread."
        self.yubikey.stop()
        self.display.stop()
        self.event.wait(2)
        self.event.set()

    def key_up(self, channel):
        self.idle = False
        print "Pressed UP Key."
        self.display.key_up()        

    def key_down(self, channel):
        self.idle = False
        print "Pressed DOWN Key."
        self.display.key_down()

    def key_left(self, channel):
        self.idle = False
        print "Pressed LEFT Key."
        self.display.key_left()

    def key_right(self, channel):
        self.idle = False
        print "Pressed RIGHT Key."
        self.display.key_right()

    def key_enter(self, channel):
        self.idle = False
        print "Pressed ENTER Key."
        self.display.key_enter()

    def key_back(self, channel):
        self.idle = False
        print "Pressed BACK Key."
        self.display.key_back()

    def yubikey_status(self,is_present):
        if is_present:
            print "Yubikey Inserted"
            self.display.auth()
        else:
            #Perform System Wipe (Lock keys, wipe any user data from memory)
            self.display.lock()
            print "Yubikey Removed"

    def yubikey_auth(self, key_psw):
        #Check password (i.e. attempt to unlock key chain)
        #If pass, then unlock the screen, else show error? or silence??
        self.display.main_menu()
