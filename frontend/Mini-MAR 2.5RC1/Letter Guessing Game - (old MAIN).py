# (C) Copyright 2010 - Dark Gray. All Rights Reserved.

#Our superglobals
__version__ = "1.1b6";
__author__ = "Xunnamius of Dark Gray";

import re;
from string import ascii_uppercase, ascii_letters;
from random import randint;
from math import fabs;
from httplib import BadStatusLine;
from collections import OrderedDict;
from NetworkInterface import NetworkInterface;
from DisplayInterface import Display;
conn1 = NetworkInterface();
conn1.status();

ascii_uppercase = ascii_uppercase[::-1];

try:
    gameNum = 0;
    i = 1;
    state = 'y';
    # No color support in this version, so the Display.*Msg distinctions are only code-deep
    Display.sysMsg('Bernard Dickens - Letter Guessing Game (Project II) - ', __author__);

    while i == 1:
        i = Display.menu(OrderedDict([('free play', False), ('load profile', 1), ('online play', True), ('exit', 2)]), initMsg='Please Select Your Gameplay Mode:', prefix='# ');
        if(i == 1): Display.gameMsg('This gameplay mode is not available yet.');

    if(i != 2):
        name = Display.cooked_input("What's your name? ");
        while not re.match('^[0-9a-zA-Z_]{4}[0-9a-zA-Z_]*$', name) and 4 <= name <= 25: # ^[0-9a-zA-Z_]{4,25}$ wasn't working for some odd reason >.<
            Display.errorMsg('Invalid name! Numbers/Letters only (between 4 and 25 chars).');
            name = Display.cooked_input("What's your name? ");

        Display.gameMsg('Welcome to the Letter Guessing Game,', name+'!');

        while state == 'y':
            tries = 0;
            maxTries = 7;
            answer = ascii_uppercase[randint(0, 25)];
            gameNum = gameNum + 1;
            Display.gameMsg('For you, this is game #'+str(gameNum)+'.');
            while tries < maxTries:
                guess = Display.cooked_input('Guess a letter, '+name+': ');
                if(guess in ascii_letters):
                    if(guess.upper() == answer):
                        Display.gameMsg("You've guessed correctly! (Total", (tries + 1), "turns)");
                        answer = -1;
                        break;
                    else:
                        print Display.errorWrapper() + "Incorrect! Your guess was",;
                        
                        # Small distance algorithm (by Xunnamius of Dark Gray)
                        # If the syntax is weird, it's because it has been engineered it to be extensible and reusable.
                        # TODO: May make this into an object later.

                        # Target array, element1, element2
                        target = (ascii_uppercase, guess.upper(), answer);
                        
                        # These percents modify the mangitude of the distance detection.
                        # The first percent denotes slight distance while the second one denotes the distinction
                        #   between moderate and far distance.
                        # The higher the percents, the biggerer their respective margins-of-error will be.
                        modifiers = (4.0, 40);
                        
                        length = len(target[0]);
                        dist = target[0].index(target[1]) - target[0].index(target[2]);
                        fdist = fabs(dist);

                        # Based on the distance from the answer, print a different result (to the same line)
                        if(fdist <= length*modifiers[0]/100): print 'slightly off.';
                        elif(dist > 0):
                           if(fdist <= length*modifiers[1]/100): print 'too low.';
                           else: print 'WAY too low!';
                        else:
                            if(fdist <= length*modifiers[1]/100): print 'too high.';
                            else: print 'WAY too high!';
                else:
                    Display.errorMsg("That's not a letter,", name+". You've lost two turns for that!");
                    maxTries = maxTries - 2;
                report = maxTries - (tries + 1);
                Display.gameMsg("You have", (report if report > 0 else 'no'), "tries remaining.");
                tries = tries + 1;
            if(answer == -1): Display.playerMsg('Good job!');
            else: Display.errorMsg("You failed", name+".\nThe correct answer was " + answer + ".");
            state = Display.cooked_input('Try again? (y/n) ');
    Display.evnMsg('(C) Copyright 2010 - Dark Gray. All Rights Reserved.');
except KeyboardInterrupt: pass;
Display.errorMsg('Program Terminated.');
Display.pause();
