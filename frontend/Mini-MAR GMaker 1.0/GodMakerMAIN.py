# -*- coding: utf-8 -*-
# All related modules and source code is (C) Copyright 2010 - Dark Gray. All Rights Reserved.

#Our superglobals
__version__ = "1.0RC1";
__author__ = "Xunnamius of Dark Gray";

import re, sys, hashlib, time, os, threading;
from random import randint;
from math import fabs, floor;
from httplib import BadStatusLine;
from collections import OrderedDict;
from NetworkInterface import NetworkInterface;
from DisplayInterface import Display;

# Establish our connection object
conn1 = NetworkInterface();
conn1.baseSite = "dignityice.com";
conn1.target = "/dg/Xunnamius/house2/pyGameInterface.php";

# Set up our environment
usedSpecials = [];
loggedIn = False;
time.clock(); # Clear the timer

# Sound-off!
Display.sysMsg('Mini-MAR BETA\'s GOD CHARACTER MAKER v', __version__);
conn1.status();

# Login to the server
def login():
    global loggedIn, SID;
    if(loggedIn): return 2;

    # We're attempting to log someone in
    u = Display.cooked_input("> Username: ");
    p = Display.getpass("> Password:");

    # Tell the user that we're doing things
    Display.sysMsg("\n  Conversing with server...");

    if(u not in ['Xunnamius']):
        Display.sysMsg("Invalid username/permissions.");
        return False;

    # Package the new data
    conn1.params = {"u":u, "python":1, "type":"", "SID":SID};

    # 1. Split the key in half
    # 2. Place chunks at both the front and the end (double salt)
    # 3. SHA-1 the whole thing again
    eKeyPiece1 = KEY[0:20];
    eKeyPiece2 = KEY[20:40];
    p = str(hashlib.sha1(eKeyPiece1 + hashlib.sha1(hashlib.md5(p).hexdigest()).hexdigest() + eKeyPiece2).hexdigest());
    u = str(hashlib.sha1(eKeyPiece1 + u + eKeyPiece2).hexdigest());
    conn1.params["u"] = u;
    conn1.params["p"] = p;
    conn1.params["type"] = "lin";

    # Authenticate the user's information
    response = conn1.request();
    
    # Alert the user of the result, and display the proper options accordingly
    if response != False:
        if response == "Approved":
            Display.playerMsg("Login Successful.");
            Display.sysMsg('Loading...');
            loggedIn = True;
            return loggedIn;
                
        elif response == "Denied":
            Display.errorMsg("Invalid username/password combination.");
            Display.errorMsg("Remember your username/password is case sensitive!");
            
        elif response == "Malformed":
            Display.errorMsg("You have illegal characters in your username/password.");
            Display.errorMsg("(Usernames are only allowed letters and numbers!)");
            Display.errorMsg("Contact Dark Gray for assistance or create a new account.");
            
        else:
            if(not response): Display.errorMsg("Connection to server was dropped. Please try again.");
            else:
                Display.errorMsg("Error. The response received from server was unrecognizable.");
                Display.errorMsg(">>", response);
                
    else: Display.errorMsg("Connection to server was dropped. Please try again.");
    return False;

# Exit MAR
def MAR_exit(status=0):
    if(status == 0): Display.gameMsg('Program Terminated.');
    else: Display.errorMsg('Program Terminated Unexpectedly ('+str(status)+')!');
    Display.evnMsg('(C) Copyright 2010 - Dark Gray. All Rights Reserved.');
    Display.pause();
    os._exit(status);

# Is this
zz='JSON'#-like data?
def is_JSON(data):
    data = str(data).strip();
    if(data[0] == '{' and data[-1] == '}'): return True;
    return False;

# Decode JSON
z = None;#-like data
def json_decode(json_data, debug=False):
    try:
        if(not json_data): raise BadStatusLine;
        json_data = str(json_data).strip();
        if(debug): print json_data;
        elif(is_JSON(json_data)): return eval(json_data);
        else: return json_data;
    
    except(Exception, BadStatusLine):
        Display.errorMsg("Bad json_data received"+('' if not debug else ' ('+str(debug)+')')+". Unable to continue.");
        Display.errorMsg(">>", str(json_data));
        MAR_exit(1);
    
# Begin the main python code
try:
    # Tell the user that we're asking the server for a new encryption key
    Display.sysMsg("Handshaking with server..."); # Go pre-emptive handshake!

    # Ask for, obtain, and store the the encryption key
    response = conn1.requestKey();

    if(response != False):
        KEY = response[0];
        SID = response[2];
    else:
        Display.errorMsg('Connection was rejected (maybe to too many people playing for too long?)');
        Display.errorMsg('Please try again later.');
        MAR_exit(1);
        
    while(True):
        zzz=lambda(zz):z==zz;
        while(not zzz(zz)): z = Display.cooked_input('> 暗証? ');
        if(not loggedIn):
            while(not login()): login();
        i = Display.menu(OrderedDict([('create', 0), ('moderate', 1), ('delete', 2), ('exit', 3)]), initMsg='Select Mode:', prefix='# ');
        
        # Creation mode, which allows for the creation of God accounts
        if(i == 0):
            response = None;
            while(response != "Approved"):
                # Ask the user for his/her information
                Display.gameMsg('Type "Back" at any time to go back to the previous menu.');
                Display.gameMsg('(This means "Back" cannot be your username/password!)');
                u = Display.cooked_input("> Desired Username: ");
                p = Display.getpass("> Desired Password:");

                # The user wants to go back instead of registering
                if(u.lower() == 'back' or p.lower() == 'back'): break;

                # Tell the user that we're doing things
                Display.sysMsg("Conversing with server...");

                # Package the new data
                conn1.params = {"u":u, "python":1, "type":"", "SID":SID};

                # Simple validation
                if(len(u) > 25 or len(p) > 100 or len(u) < 4 or len(p) < 4):
                    Display.errorMsg("Your username/password must be between 4 and 25 characters in length.");
                    Display.errorMsg("Please try again.");
                    continue;

                # Finish packaging the data
                p = str(hashlib.sha1(hashlib.md5(p).hexdigest()).hexdigest());
                conn1.params["p"] = p;
                conn1.params["class"] = 4;
                conn1.params["type"] = "reg";

                # Send the data off for processing
                response = conn1.request();

                # Alert the user of the result, and display the proper options accordingly
                if response != False:
                    if response == "Approved":
                        Display.playerMsg("The username", u, "has been registered successfully!");
                        
                    elif response == "Malformed":
                        Display.errorMsg("Error: The selected username is illegal.");
                        Display.errorMsg("Note that usernames should only contain letters & numbers.");
                        Display.errorMsg("Feel free to contact DG should you require assistance.");
                        
                    elif response == "Denied":
                        Display.errorMsg("The username", u, "is not available for use.");
                        Display.errorMsg("Please select a different one.");
                        
                    else:
                        if(not response): Display.errorMsg("Connection to server was dropped. Please try again.");
                        else:
                            Display.errorMsg("Error. The response received from server was unrecognizable.");
                            Display.errorMsg(">>", response);
                        break;
                else:
                    Display.errorMsg("Connection to server was dropped. Please try again.");
                    break;
            
        # Moderation mode, which allows for (direct updates) access to the game's SQL database
        elif(i == 1): Display.gameMsg('Not available.');
            # Go back a page
            # elif(i == 2): break;
        
        # Deletion mode, which allows for deletion of things
        elif(i == 2): Display.gameMsg('Not available.');
            # Go back a page
            # elif(i == 2): break;

        # The user wishes to exit the program
        elif(i == 3): MAR_exit();

# Someone or something tried to interrupt the program!           
except KeyboardInterrupt:
   choice = Display.cooked_input("> Are you sure you wish to exit? (y/n) ");
   if(choice == 'y'): MAR_exit();
   else: pass;
