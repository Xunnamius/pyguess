'''
Created on Sep 14, 2010

@author: Xunnamius

Provides a convenient wrapper for Python's http library
'''

import httplib, urllib, socket, sys;
from DisplayInterface import Display;

# NetworkInterface Class
# Description: This is a slightly neutered version of the class that regulates all
# of MAR's network communications.

# Available initialization parameters include:
#    silent=(bool): If True, the NetworkInterface will print anything to the command line (excluding the messaging methods)
class NetworkInterface():
    
    # Properties
    _silent = False;
    _retries = 1;
    _totalRetries = 0;
    _timeout = 9;
    _failThrough = False;
    _connObject = None;
    
    spinObject = None;
    makeNulls = False;
    
    params = {};
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"};
    
    baseSite = "";
    target = "";
    
    # Initializes our class
    def __init__(self, **args): self.redefine(**args);
    
    # (re)Defines our interal pseudo-private properties
    def redefine(self, **args):
        for key in args:
            if(key == "silent"): self._silent = args[key];
            elif(key == "retries"): self._retries = args[key];
            elif(key == "failThrough"): self._failThrough = args[key];
            elif(key == "timeout"): self._timeout = args[key];
            
    # Prints the status of the Network Object (if silent=False)
    def status(self):
        self._stopSpin();
        if self._silent == False: Display.sysMsg("NetworkInterface module mounted successfully");
        
    def connect(self):
        try:
            if len(self.baseSite) < 4:
                self._stopSpin();
                if self._silent == False: Display.errorMsg("Invalid connection parameters specified. Check your source code.");
                return False;
            else:
                self._connObject = httplib.HTTPConnection(self.baseSite, timeout=self._timeout);
                self._stopSpin();
                return True;
        except:
            self._stopSpin();
            return False;
        
    def request(self, method="POST"):
        if not self.connect(): self.connect();
        try:
            self._totalRetries = self._retries;
            if  self._connObject:
                while self._retries > 0:
                    self._connObject.request(method, self.target, urllib.urlencode(self.params), self.headers);
                    response = self._connObject.getresponse();
                    
                    self._stopSpin();
                    
                    if not self._failThrough:
                        if response.status == 200:
                            response = response.read().strip();
                            self.close();
                            
                            if response == "MAINTENANCE_MODE":
                                # Server is down for repairs!
                                if self._silent == False: Display.errorMsg("The server is down for maintenance at the moment.");
                                if self._silent == False: Display.errorMsg("Please try again in an hour or so.");
                                sys.exit(1);
                                response = False;
                            if self.makeNulls:
                                response = response.replace("null", "None");
                            return str(response) if response else False;
                        else:
                            if self._silent == False:
                                if self._silent == False: Display.errorMsg("Unable to connect to the server (" + str(response.status) + " " + str(response.reason) + ")!");
                                self._retries = self._retries - 1;
                                if self._retries > 0 and self._silent == False: Display.errorMsg("Re-attempting command (" + str(self._totalRetries-self._retries) + ").");
                                elif self._silent == False: Display.errorMsg("Please attempt to connect again.");
                                return False;
                    else: return response;
            else:
                self._stopSpin();
                if self._silent == False:
                    Display.errorMsg("Error: unable to complete request.\nThe connection object was not initialized correctly.");
                    sys.exit(1);
        except socket.gaierror:
            self._stopSpin();
            self.close();
            if self._silent == False: Display.errorMsg("Unable to connect!\nPlease check your internet connection and try again.");
            return False;
        except httplib.BadStatusLine:
            self.close();
            # raise httplib.BadStatusLine("BadStatusLine");
            Display.errorMsg("Error: Bad Statusline.");
            return False;
        except:
            self.close();
            self._stopSpin();
            return False;
    
    def requestKey(self, params=None):
        try:
            if params: self.params = params;
            else: self.params = {"nec":1, "python":1};
            response = self.request();
            
            if response != False:
                return response.partition("@");
            else: return False;
        except:
            Display.errorMsg('There was an error while attempting to process your request.');
            return False;
        
    def _stopSpin(self):
        if self.spinObject: self.spinObject.stop();
        
    def close(self):
        if self._connObject: self._connObject.close();
