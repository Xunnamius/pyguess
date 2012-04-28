# Import and mount the necessary class modules
# (C) Copyright 2010 - Dark Gray. All Rights Reserved.
import os, math, signal, warnings, sys, time, msvcrt;
signal.signal(signal.SIGINT, signal.SIG_IGN); # Ctrl-C interrupts are so annoying to capture!
#from colorama import init, Fore, Back, Style;
#from DarkMods import DM_lookup;
#init(); # (attempt to) Initialize our colorization module

# DisplayInterface Class
# Description: This class is a neutered version of the DisplayInterface class I used to
# regulates all communications within MAR.
# Available initialization parameters include:
#    broadcast=(bool): If True, everything displayed to the console will be prepended with a command type followed by a '>'; Default is False
#    silent=(bool): If True, the DisplayInterface will print anything to the command line (excluding the messaging methods)
class DisplayInterface():
    # Properties
    _silent = False;
    _broadcast = False;
    _indentLevel = "";
    _currentOptionDict = {};
    _curOptDictAllCmds = [];
    mMode = 0;
    
    # "Constants"
    separators = ("\n\t-----\n", "\n\t+++++\n", "\n\t*****\n", "\n\t~~~~~\n");
    newline = "\n" + _indentLevel;
    
    # Initializes our class
    def __init__(self, **args): self.redefine(**args);
    
    # (re)Defines our interal pseudo-private properties
    def redefine(self, **args):
        for key in args:
            if(key == "broadcast"): self._broadcast = args[key];
            elif(key == "silent"): self._silent = args[key];
    
    # Internal funciton that updates the newline constant to be consistent with the current indent level
    def _updateNewline(self): self.newline = "\n" + self._indentLevel;
            
    # Prints the status of the Display Object (if silent=False)
    def status(self):
        if self._silent == False: self.sysMsg("DisplayInterface module mounted successfully!");
    
    # Internal function that transforms (mostly colorizes) messages received by the messaging methods. If broadcast=True, broadcast the cmd type. 
    def _transform(self, msgs, sender="Unknown"):
        print self._indentLevel,;
        for msg in msgs:
            if msg == msgs[0]:
                #if self._broadcast == True or (self._broadcast != False and sender in self._broadcast):
                #    print Style.BRIGHT + sender + ">" + Style.NORMAL,;
                #if sender == "administrator": msg = Back.WHITE + " " + msg;
                if self._broadcast != False and msg in self.separators: msg = msg.lstrip("\n");
            print msg,;
        print '';#Style.RESET_ALL;
    
    # Provides a convenient abstract "wrapper" for the color codes used to compose the various messaging
    # functions (primarily for use with spinzor)
    def _transformWrapper(self, sender):
        wrapper = "";
        #if self._broadcast == True or (self._broadcast != False and sender in self._broadcast):
        #    wrapper += Style.BRIGHT + sender + "> " + Style.NORMAL;
        #if sender == "administrator": wrapper += Back.WHITE + " ";
        return wrapper;
    
    # These are the publicly available "Messaging Methods"
    # Accepts any number of comma-separated arguments and prints them all on the same line with the correct colorization
    
    # All the definitions for the various messaging methods exist within the list below
    _definition = ['',#Style.RESET_ALL,
                   {"name":"system", "style": ''},#Fore.MAGENTA},
                   {"name":"error", "style": ''},#Fore.RED},
                   {"name":"game", "style": ''},#Fore.YELLOW},
                   {"name":"event", "style": ''},#Fore.CYAN},
                   {"name":"administrator", "style": ''},#Fore.BLACK},
                   {"name":"player", "style": ''}];#Fore.GREEN}];
                   
    # Returns the color codes used to make a "system" message (primarily for use with spinzor)
    def sysWrapper(self): return self._definition[0] + self._definition[1]["style"] + self._indentLevel + self._transformWrapper(self._definition[1]["name"]);
    def sysMsg(self, *msg):
        print self._definition[0] + self._definition[1]["style"],;
        self._transform(msg, self._definition[1]["name"]);
    
    def errorWrapper(self): return self._definition[0] + self._definition[2]["style"] + self._indentLevel + self._transformWrapper(self._definition[2]["name"]);
    def errorMsg(self, *msg):
        if(self.mMode != 2):
            print self._definition[0] + self._definition[2]["style"],;
            self._transform(msg, self._definition[2]["name"]);
    
    def gameWrapper(self): return self._definition[0] + self._definition[3]["style"] + self._indentLevel + self._transformWrapper(self._definition[3]["name"]);
    def gameMsg(self, *msg):
        print self._definition[0] + self._definition[3]["style"],;
        self._transform(msg, self._definition[3]["name"]);
    
    def evnWrapper(self): return self._definition[0] + self._definition[4]["style"] + self._indentLevel + self._transformWrapper(self._definition[4]["name"]);
    def evnMsg(self, *msg):
        print self._definition[0] + self._definition[4]["style"],;
        self._transform(msg, self._definition[4]["name"]);
    
    def adminWrapper(self): return self._definition[0] + self._definition[5]["style"] + self._indentLevel + self._transformWrapper(self._definition[5]["name"]);
    def adminMsg(self, *msg):
        print self._definition[0] + self._definition[5]["style"],;
        self._transform(msg, self._definition[5]["name"]);
    
    def playerWrapper(self): return self._definition[0] + self._definition[6]["style"] + self._indentLevel + self._transformWrapper(self._definition[6]["name"]);
    def playerMsg(self, *msg):
        print self._definition[0] + self._definition[6]["style"],;
        self._transform(msg, self._definition[6]["name"]);
        
    def customMsg(self, startcolor, customSender="", *msg):
        print startcolor,;
        self._transform(msg, customSender);
    
    # This method is used to present the user with a consistent user-friendly menu format
    # Returns the user's choice (in the form you select)
    # Available parameters include:
    #    initMsg=(string/number): The initial message that alerts the user to the presence of the menu interface
    #    options=(dict): An ORDERED (or not!) dictionary of string:object relations that dictate what options are presented
    #                    to the user, and how those options should be represented to the caller.
    #
    #                    Ex. options=[("choice 1", 1), ("choice2", "wrong"), (1, False)]
    #                    The example above will return 1, "wrong", or False depending on
    #                    the user's choice of either "choice 1", "choice2", or 1 respectively.
    def menu(self, options, prompt="> ", initMsg="::Options::", errorMsg="Invalid Response.", prefix="- ", caseSense=False, capitalize=True, time_limit=None, limit_phrase=None):
        self.gameMsg(initMsg);#Style.BRIGHT + initMsg);
        for key in options: self.gameMsg(prefix + (key.title() if capitalize else key));
        input = None;
        while options.has_key(input) == False:
            try:
                input = (self.timed_input(self._indentLevel + prompt, limit_phrase, time_limit) if time_limit else raw_input(self._indentLevel + prompt));
                input = input.strip();
                if caseSense == False: input = input.lower();
                if options.has_key(input): return options[input];
                else: self.errorMsg(errorMsg);
            except (KeyboardInterrupt, EOFError):
                #from DarkMods import grab;
                #World = grab("World", "World");
                #World.exit("Mar has experienced an unexpected interrupt.");
                choice = self.cooked_input("Are you sure you wish to exit MAR? (y/n) ");
                if(choice == 'y'): os._exit(1);
                else: pass;
            except: self.errorMsg("Program has experienced an unexpected error.");
    
    # Mutate the target string, replacing certain characters with others
    # NOT TO BE USED WITH THIS GAME
    def _mutate(self, target): return target.replace("(", Fore.BLUE).replace(")", Fore.WHITE);
            
    # This method is used to present the user with a complex consistent user-friendly menu format
    # Returns the user's choice (in the form you select)
    # To return the user's input parsed by spaces as a tuple, choose -1 as the returnValue
    # Available parameters include:
    #    initMsg=(string/number): The initial message that alerts the user to the presence of the menu interface
    #    options=(dict): An ORDERED (or not!) dictionary of complex property-value relations that dictate what options are presented
    #                    to the user, and how those options should be represented to the caller, etc.
    #
    #                    Syntax: OrderedDict([((string tuple of acceptable cmds), ["user-friendly pattern", "regexp", returnValue])])
    #                    Ex. OrderedDict([(("status", "stats", "s"), ["[username|userID]", "", -1]), (("list", "l"), ["[item]", "", -1])]);
    # NOT TO BE USED WITH THIS GAME
    def complexMenu(self, options, prompt="> ", initMsg="::Options::", errorMsg=None, defaultNFError=None, suggestSpelling=True, prefix="- ", caseSense=False, capitalize=True, pLevel=0):
        if not errorMsg: errorMsg = "Invalid Response.";
        if not defaultNFError: defaultNFError = "Use help [command name] for help with a specific command.";
        self.gameMsg(Style.BRIGHT + initMsg);
        self._currentOptionDict = options;
        
        # Map out all possible keys (for other objects to reference later)
        self._curOptDictAllCmds = [];
        for tup in options.keys():
            self._curOptDictAllCmds.extend(list(tup));
        
        for key in options:
            if(int(options[key][3]) == 0 or (int(options[key][3]) > 0 and int(options[key][3]) <= int(pLevel)) or (int(options[key][3]) < 0 and math.fabs(options[key][3]) == float(pLevel))):
                self.gameMsg(prefix + (key[0].capitalize() if capitalize else key[0]) + " " + Style.BRIGHT + Fore.WHITE + self._mutate(options[key][0]));
            
        input = None;
        inputTuple = None;
        inputIndex = False;
        while not inputIndex:
            try:
                input = raw_input(self._indentLevel + prompt);
                input = input.strip();
                if(len(input) < 256):
                    inputTuple = tuple(input.split(" "));
                    inputTarget = inputTuple[0].lower() if not caseSense else inputTuple[0];
                    inputIndex = self._has_key(options, inputTarget, pLevel);
                    
                    if inputIndex:
                        source = options[inputIndex];
                        action = source[2];
                        if action == -1:
                            if (len(source[1]) <= 0) or (len(source[1]) > 0 and re.match(source[1], input)): return (inputIndex[0], inputTuple);
                        else: return action;
                self.errorMsg(errorMsg);
                if suggestSpelling and len(input) < 256:
                    lookup = DM_lookup(",".join(Display.getKeys()), inputTarget);
                    if lookup == inputTarget: Display.errorMsg(defaultNFError);
                    else: Display.errorMsg("Were you looking for" + Style.BRIGHT, lookup + Style.NORMAL + "?");
                
            except (KeyboardInterrupt, EOFError):
                #from DarkMods import grab;
                #World = grab("World", "World");
                #World.exit("Mar has experienced an unexpected interrupt.");
                self.errorMsg("An unexpected interrupt has been experienced.");
                
            except:
                self.errorMsg("Program has experienced an unexpected error.");
                #from ExceptionInterface import Xception;
                #Xception.complexError("Program has experienced an unexpected error.");
    
    # Check if a key exists within a dictionary (even one that has tuples for keys)
    def _has_key(self, l, input, pLevel=0):
        for key in l:
            try:
                if list(key).index(input) >= 0:
                    if(int(l[key][3]) == 0 or (int(l[key][3]) > 0 and int(l[key][3]) <= int(pLevel)) or (int(l[key][3]) < 0 and math.fabs(l[key][3]) == float(pLevel))): return key;
                    else: return False;
            except: pass;
        return False;
    
    # Slightly better version of "raw_input"
    def cooked_input(self, prompt, lax=False):
        #import sys;
        while True:
            food = raw_input(Display.sysWrapper() + prompt); #+ Fore.WHITE);
            #sys.stdout.write(Style.RESET_ALL);
            food = food.strip();
            if len(food) <= 0 and not lax:
                Display.errorMsg("Invalid entry. Please try again.");
                continue;
            return food;

    # It's like cooked_input, except it has a time limit before unblocking
    # default is returned if the method times out
    def timed_input(self, caption, default=None, timeout=60):
        start_time = time.time();
        sys.stdout.write(caption);
        input = '';
        while True:
            if msvcrt.kbhit():
                chr = msvcrt.getche()
                if ord(chr) == 13: # enter_key
                    break;
                elif ord(chr) == 8: #backspace_key
                    input = input[:-1];
                    sys.stdout.write('\b');
                elif ord(chr) >= 32: #space_char + (all keys on keyboard)
                    input += chr;
            if len(input) == 0 and (time.time() - start_time) > timeout: break;
        print '';  # needed to move to next line
        input = input.strip();
        if len(input) > 0: return input;
        else: return default;
    
    # Comparable to the DOS "pause" command
    def pause(self, msg="Press the enter key to continue..."):
        return self.cooked_input(msg, True);
    
    # Slightly cooler version of python's "getpass" method
    def getpass(self, prompt):
        from getpass import getpass;
        # Display.errorMsg("Note that Python can't hide your password when using IDLE!"); 
        with warnings.catch_warnings():
            warnings.simplefilter("ignore");
            while True:
                print Display.sysWrapper() + prompt + " (hidden) ",; #Fore.WHITE + " (hidden) ",;
                result = getpass("").strip();
                if len(result) <= 0:
                    Display.errorMsg("Invalid entry. Please try again.");
                    continue;
                return result;
    
    # A (potentially recursive) method to increase the internal indent pointer
    # You may specify a number as an argument to indent the current display by "plus" tabs
    def indent(self, plus=1):
        if plus > 0:
            self._indentLevel += "\t";
            plus -= 1;
            self.indent(plus);
        self._updateNewline();
    
    # A (potentially recursive) method to decrease the internal indent pointer
    # You may specify a number as an argument to oudent the current display by "plus" tabs
    def outdent(self, minus=1):
        if minus > 0:
            self._indentLevel = self._indentLevel.partition("\t")[2];
            minus -= 1;
            self.outdent(minus);
        self._updateNewline();
    
    # Return our current indentation level
    def getIndentLevel(self): return self._indentLevel.count("\t"); # (as an integer)
    def getLiteralIndent(self): return self._indentLevel; # (as a string)
    
    # Return the current "option" object that exists within memory
    def getOptions(self):
        return self._currentOptionDict;
    
    # Return an exhaustive list of the current "option" object's (unbound) unwrapped keys
    def getKeys(self):
        return self._curOptDictAllCmds;
    
    # Synonym of the windows CMD "cls" command
    def clear(self):
        os.system("cls"); # windows
        #os.system("clear");  bash (mac, linux)
        
# Pseudo-Singleton
Display = DisplayInterface(silent=True);
