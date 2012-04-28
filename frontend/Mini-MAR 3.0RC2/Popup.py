'''
Originally created on Oct 9, 2010

@author: Xunnamius
Servers as a pseudo 'popup box'
'''
import sys, threading, os, time;
from DisplayInterface import Display;

class Autodeath(threading.Thread):
    """ Die after x seconds """
    
    def __init__(self):
        # Clear the timer
        self.countdown = time.clock();
        
        threading.Thread.__init__(self, None, None, "Autodeath Thread");
        self.daemon = True;
        self.start();

    def run(self):
        self.countdown = time.clock();
        while(self.countdown + 20 > time.clock()):
            time.sleep(1);
        os._exit(1);

challenger = sys.argv[1];
if(challenger and 0 < len(challenger) <= 25):
    death = Autodeath();
    Display.sysMsg(('----- MAR Battle Request Warning! -----').center(53));
    Display.sysMsg(time.strftime("%m/%d/%Y @ [%I:%M:%S]").center(51),"\n\n\n");
    Display.evnMsg("You have a pending battle request from " +challenger+"!");
    Display.evnMsg("Type 'Challenge' and then '"+challenger+"'");
    Display.evnMsg("in the main window to accept or do nothing to decline.\n");
    Display.sysMsg('This window will automatically close in 20 seconds.');
    Display.cooked_input('  Press "Enter" to immediately close this window.', True);
