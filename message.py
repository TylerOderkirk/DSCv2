#!/usr/bin/env python

from threading import *
import Queue

class Message(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.event = Event()

        self.repeat_msg_list = []
        self.repeat_msg_index = 0
        self.repeat_msg_segment = 0

        self.msg_seg_list = []
        self.radio_inbound_queue = Queue.Queue() #Should we set a buffer size??

        print "Initialized Message Thread."
    
    def run(self):
        self.event.wait(1)
        while not self.event.is_set():
            #Check Queued Msgs From Radio
            try:
                msg = self.radio_inbound_queue.get_nowait()
            except Queue.Empty:
                pass
                #print "Radio Inbound Queue Empty!"
            else:
                self.add_msg_to_seg_list(msg)

            self.check_for_complete_msgs()
            self.event.wait(1)

    def stop(self):
        print "Stopping Message Thread."
        self.event.set()

    def is_msg_avail_to_repeat(self):
        if len(self.repeat_msg_list) > 0:
            return True
        else:
            return False

    def get_next_msg_for_repeat(self):
        msg_list_len = len(self.repeat_msg_list)
        if msg_list_len > 0:
            if self.repeat_msg_index >= msg_list_len:
                self.repeat_msg_index = 0
                self.repeat_msg_segment = 0
            if self.repeat_msg_segment == 0:
                outbound_data = self.repeat_msg_list[self.repeat_msg_index][:255]
                self.repeat_msg_segment += 1
            elif self.repeat_msg_segment == 1:
                outbound_data = self.repeat_msg_list[self.repeat_msg_index][255:510]
                self.repeat_msg_segment += 1
            elif self.repeat_msg_segment == 2:
                #Grab Fingerprint from First 2 Segments
                seg1f = self.repeat_msg_list[self.repeat_msg_index][:100]
                seg2f = self.repeat_msg_list[self.repeat_msg_index][255:355]
                outbound_data = self.repeat_msg_list[self.repeat_msg_index][510:]
                outbound_data += seg1f + seg2f
                self.repeat_msg_segment += 1
            
            if self.repeat_msg_segment == 3:
                self.repeat_msg_segment = 0
                self.repeat_msg_index += 1

            return outbound_data
        else:
            return ""

    def new_composed_msg(self, msg):
        print "Processing new message."
        #Encrypt / Sign and add to the list
        self.repeat_msg_list.append(msg)

    def add_msg_to_repeat_list(self,msg):
        #lots of things to do here...
        if not self.check_for_dup(msg):
            self.repeat_msg_list.append(msg)
            print "New Unique Message Received via Radio."
            print msg
        else:
            print "Duplicate Message Received via Radio. Dropped"

    def add_msg_to_seg_list(self,msg):
        #lots of things to do here...
        if not self.check_for_seg_dup(msg):
            self.msg_seg_list.append(msg)
            print "New Unique Seqment Received ."
            print msg
        else:
            print "Duplicate Segment Received via Radio. Dropped"
            
    def check_for_dup(self,msg):
        #Check for duplicates in the repeat msg list, every encrypted msg is unique, no dups allowed!
        for m in self.repeat_msg_list:
            if msg == m:
                return True
        return False

    def check_for_seg_dup(self,msg):
        #Check for duplicates in the repeat msg list, every encrypted msg is unique, no dups allowed!
        for m in self.msg_seg_list:
            if msg == m:
                return True
        return False
        
    def check_for_complete_msgs(self):
        seg1f = ""  #Part of Encrypted Packet (Fingerprint)
        seg2f = ""  #Part of Signature Packet (Fingerprint)
        seg1_found = False
        seg2_found = False
        seg1 = ""   #Actual Msg Segment
        seg2 = ""   #Actual Msg Segment 
        
        for mf in self.msg_seg_list:
            if len(mf) == 212:
                seg1f = mf[12:112]
                seg2f = mf[112:212]
                print "Found Finger Print:"
                print seg1f
                print seg2f
                print "Searching for remaining segments."
            for m in self.msg_seg_list:
                if len(m) == 255:
                    if m[:100] == seg1f:
                        seg1_found = True
                        seg1 = m
                        print "Msg Segment 1 Found!"
                        print seg1
                    elif m[:100] == seg2f:
                        seg2_found = True
                        seg2 = m
                        print "Msg Segment 2 Found!"
                        print seg2
                if seg1_found and seg2_found:
                    print "Complete Msg Found!"
                    self.add_msg_to_repeat_list(seg1+seg2+mf[:12])
                    self.msg_seg_list.remove(mf)
                    self.msg_seg_list.remove(seg1)
                    self.msg_seg_list.remove(seg2)
                    break
