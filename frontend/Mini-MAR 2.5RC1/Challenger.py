'''
Originally created on Oct 9, 2010

@author: Xunnamius
Used to send a server a series of heartbeats every x seconds
'''

import threading, time, os, math;
from DisplayInterface import Display;
from NetworkInterface import NetworkInterface;

class Challenger(threading.Thread):
    """ Based on my quick and dirty server 'keep-alive' heartbeat class """
    
    def __init__(self, baseSite, target, params, autostart=True):
        # Flag of Death
        self.stopFlag = False;
        self.pauseFlag = False;
        self._silent = False;
        self.server = NetworkInterface();
        self.server.baseSite = baseSite;
        self.server.target = target;
        self.server.params = params;
        self.server.makeNulls = True;
        
        # Clear the timer
        time.clock();
        
        threading.Thread.__init__(self, None, None, "Challenger Thread");
        self.daemon = True;
        if autostart: self.start();

    def run(self):
        """ Start sending beats to the server every 10 seconds """
        
        while(not self.stopFlag):
            sleeptime = time.clock();
            
            if(self.pauseFlag):
                op = self.server.params['type'];
                self.server.params['type'] = 'ali';
                self.server.request();
                self.server.params['type'] = op;
            else:
                response = self.server.request();

                if(response not in [None, '', False] and response != '$NoBattle' and 0 < len(response) <= 25):
                    if(response == '$Ingame'): continue;
                    else: os.system('start python Popup.py ' + response.strip());
                    
            time.sleep(math.fabs(3 - (time.clock() - sleeptime)));
        
    def stop(self, join=True):
        if(join and self.stopFlag): self.join(1);
        self.stopFlag = True;
