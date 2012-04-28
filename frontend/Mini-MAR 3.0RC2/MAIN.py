# All related modules and source code is (C) Copyright 2010 - Dark Gray. All Rights Reserved.
# Windows only (thanks to msvcrt), sorreh!

#Our superglobals
__version__ = "3.0.60RC2";
__author__ = "Xunnamius of Dark Gray";

import re, sys, hashlib, time, os, threading, signal;
from string import ascii_uppercase, ascii_letters;
from random import randint, random;
from copy import deepcopy;
from math import fabs, floor;
from httplib import BadStatusLine;
from collections import OrderedDict;
from NetworkInterface import NetworkInterface;
from DisplayInterface import Display;
from Challenger import Challenger;
from winsound import MessageBeep, MB_OK, MB_ICONASTERISK as beep;

# Establish our connection object
conn1 = NetworkInterface();
conn1.baseSite = "dignityice.com";
conn1.target = "/dg/Xunnamius/house2/pyGameInterface.php";

# Set up our environment
globalskip = False;
usedSpecials = [];
SETTINGS_DIR = 'settings.ma';
default_settings = {'playSounds':1, 'cBlockInt':5, 'maxLogoutAttempts':10, 'AIDifficulty':5, 'catchInterrupts':1};
settings_names = {'playSounds':'Play Game Sounds (0 [No] - 1 [Yes])', 'cBlockInt':'Server Query Modulo (seconds between 2-5)', 'maxLogoutAttempts':'Maximum Automated Logout Attempts (1-100)', 'AIDifficulty':'AI Difficulty Level (1 [easy] - 10 [impossible])', 'catchInterrupts':'Catch Interrupts (0 [No] - 1 [Yes])'};
settings = deepcopy(default_settings);
loggedIn = False;
time.clock(); # Clear the timer
signal.signal(signal.SIGINT, signal.SIG_IGN); # Ctrl-C interrupts are so annoying to capture!

# Sound-off!
# No color support in this version, so the Display.*Msg distinctions are only code-deep for now
Display.sysMsg('Mini-MAR BETA version', __version__);
conn1.status();
Display.sysMsg('Bernard Dickens - Project II -', __author__);

# Transform setting names
def set_transform(name):
    global settings, settings_names;
    if(name in settings): return settings_names[name];
    elif(name in settings_names.values()):
        for i, value in enumerate(settings_names.values()):
            if(name == value): return settings_names.keys()[i];
    return False;
    
# Validate a setting and its data
def val_setting(setting, data):
    defaulting = False;
    
    if(setting in ['playSounds', 'catchInterrupts']):
        if(data not in ['1', '0']): data = default_settings[setting]; defaulting = True;
        else:
            data = int(data);
            if(setting == 'catchInterrupts'): Display.dieOnInterrupt = bool(data);
    elif(setting in ['cBlockInt']):
        if(5 < int(data) or 2 > int(data)): data = default_settings[setting]; defaulting = True;
        else: data = int(data);
    elif(setting in ['AIDifficulty']):
        if(10 < int(data) or 1 > int(data)): data = default_settings[setting]; defaulting = True;
        else: data = int(data);
    elif(setting in ['maxLogoutAttempts']):
        if(100 < int(data) or 1 > int(data)): data = default_settings[setting]; defaulting = True;
        else: data = int(data);
    else:
        Display.errorMsg('Setting Error: Unknown setting "'+str(setting)+'".');
        return -1;
    
    if(defaulting): Display.errorMsg('Setting Error: Invalid entry for "'+str(setting)+'". Defaulting...');
    return data;

# Retrieve/Modify MAR's core settings
def MAR_load_settings(setdict=None):
    global settings, SETTINGS_DIR, default_settings;

    Display.sysMsg('Refreshing settings data...');
    try:
        if(not setdict):
            with open(SETTINGS_DIR, 'r') as io:
                for line in io:
                    pos = line.find('=');
                    if(pos+1):
                        setting = line[:pos].strip();
                        data = val_setting(setting, line[pos+1:].strip());
                        if(not data and type(data) == type(False)): continue;
                        else: settings[setting] = data;
                return False;
        else:
            with open(SETTINGS_DIR, 'w') as io:
                settings = setdict;
                for line in settings.keys(): io.write(line+'='+str(settings[line])+'\n');
                return True;
    except (IOError, EOFError): Display.errorMsg('Setting Error: File busy. Try again later. (locked?)');

# Exit MAR
def MAR_exit(status=0):
    if(status == 0): Display.gameMsg('Program Terminated.');
    else: Display.errorMsg('Program Terminated Unexpectedly ('+str(status)+')!');
    Display.evnMsg('(C) Copyright 2010 - Dark Gray. All Rights Reserved.');
    Display.pause();
    os._exit(status);

# Is this JSON-like data?
def is_JSON(data):
    data = str(data).strip();
    if(data[0] == '{' and data[-1] == '}'): return True;
    return False;

# Decode JSON-like data
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

# Wait for a response from the server, depending on the parameters
def block_on_challenge(ignore_response, params, at_end=1, stall_time=60, debug=False, eval_response=True):
    global conn1, heartbeat;
    if(not conn1 or not heartbeat): MAR_exit(2);
    xtime = 0;
    
    # Give them 60 seconds
    while(xtime < stall_time):
        if(xtime == (stall_time-30)): Display.sysMsg('30 seconds remaining...');
        elif(xtime == (stall_time-10)): Display.sysMsg('10 seconds remaining...');

        sleeptime = time.clock();
        
        if(xtime % int(settings['cBlockInt']) == 0):
            # Setup our internal environment
            conn1.params = params;
            conn1.makeNulls = True;
            response = conn1.request();
            
            if(response and response != ignore_response):
                if(eval_response): response = json_decode(response, debug);
                conn1.makeNulls = False;
                return response;
            
        sleeptime = 1 - (time.clock() - sleeptime);
        if(sleeptime > 0): time.sleep(sleeptime);
        xtime = xtime + 1;
        
    # We timed-out!
    else:
        if(at_end == 1):
            Display.evnMsg('Request TIMED OUT. Destroying room...');
            conn1.params = {"u":u, "p":p, "python":1, "type":"kil", "SID":SID};
            response = conn1.request();
            Display.sysMsg('Room Destroyed!');
            heartbeat.pauseFlag = False;
            conn1.makeNulls = False;
        return False;

# Small distance algorithm
# Calculates the relative distance between two elements in an array (by Xunnamius of Dark Gray)
def distanceAlgorithm(haystack, targetNeedle, needle, slightDistMod, farDistMod):
    # Target array, element1, element2
    target = (haystack, needle, targetNeedle);
    
    # These percents modify the mangitude of the distance detection.
    # The first percent denotes slight distance while the second one denotes the distinction
    #   between moderate and far distance.
    # The higher the percents, the biggerer their respective margins-of-error will be.
    modifiers = (slightDistMod, farDistMod);
    
    length = len(target[0]);
    dist = target[0].index(target[1]) - target[0].index(target[2]);
    fdist = fabs(dist);

    # Based on the distance from the answer, print a different result (to the same line)
    if(fdist <= length*modifiers[0]/100): return 'slightly off.';
    elif(dist > 0):
       if(fdist <= length*modifiers[1]/100): return 'too low.';
       else: return 'WAY too low!';
    else:
        if(fdist <= length*modifiers[1]/100): return 'too high.';
        else: return 'WAY too high!';

# Restructures the userpowers array to include the power's combined effect on the game
#  in the for of a new simpler array ( ie. w = floor(alottedSP/Y)*X+MODIFIER where w <=> Z )
def restruct():
    global conn1;
    
    conn1.params = {"u":u, "p":p, "python":1, "type":"pul", "SID":SID};
    conn1.makeNulls = True;
    response = conn1.request();
    conn1.makeNulls = False;
    
    if(str(response) != 'False'):
        response = json_decode(response);
        uDat = response['userdata'];
        uPow = response['powers'];
        
        for i, special in enumerate(uPow):
            digits = [];

            # Decode the powers' json data
            uPow[i]['json'] = json_decode(uPow[i]['json']);
            
            # Compute the magnitude of each special based on updates
            for j, stat in enumerate(uPow[i]['json']['effects']):
                fx, mag, upgrade = stat;
                
                v = None;
                if(type(mag) == type(list())):
                    v = mag[0];
                    mag = mag[1];
                    
                if(upgrade != False):
                    x, y, z = upgrade;
                    z = float(z);
                    mag = float(mag);
                    w = floor(float(special['sp'])/float(y))*float(x)+mag;
                    if(z <= 0.0 and mag < 0.0 and w < z): w = z; # Only special event moves (as opposed to cooldowns and chance based updates) can go negative!
                    elif((z <= 0.0 and w < fabs(z)) or (z > 0.0 and w > z)): w = fabs(z);
                    mag = w;

                # Commit changes
                uPow[i]['json']['effects'][j] = [fx, ([v, mag] if v != None else mag), False];
                digits.append((int(mag) if int(mag) == mag else mag));

            # Compute the magnitude of each "chance" based on updates
            mag, upgrade = uPow[i]['json']['chance'];
            mag = float(mag);
            if(upgrade != False):
                x, y, z = upgrade;
                z = float(z);
                w = floor(float(special['sp'])/float(y))*float(x)+float(mag);
                if((z <= 0.0 and w < fabs(z)) or (z > 0.0 and w > z)): w = fabs(z);
                
                # Fail-safe
                if(w > 1.0): w = 1.0;
                elif(w < 0.0): w = 0.0;
                mag = w;

            # Commit changes
            uPow[i]['json']['chance'] = [mag, False];
            digits.append(int(round(float(mag)*100)));

            # Compute the magnitude of each "cooldown" based on updates
            mag, upgrade = uPow[i]['json']['cooldown'];
            if(str(mag).find('#')+1): mag = int(round(eval(str(mag).replace('#', str(digits[0])))));
            elif(upgrade != False):
                x, y, z = upgrade;
                z = float(z);
                w = int(round(floor(float(special['sp'])/float(y))*float(x)+float(mag)));
                if((z <= 0.0 and w < fabs(z)) or (z > 0.0 and w > z)): w = int(round(fabs(z)));
                mag = w;
                
            # Commit cooldown magnitude changes
            uPow[i]['json']['cooldown'] = (mag, False);
            if(mag < 0): mag = '(can only be used once)';
            elif(mag == 0): mag = '(no cooldown)';
            else: mag = str(mag)+' turns';
            digits.append(mag);
            
            # Replace all # with appropriate content
            uPow[i]['desc'] = uPow[i]['desc'].replace('[##]', str(digits[-2])); # [##] == chance
            uPow[i]['desc'] = uPow[i]['desc'].replace('[#]', str(digits[-1]));  # [#] == cooldown
            uPow[i]['desc'] = uPow[i]['desc'].replace('#', str(digits[0]));

            # Replace all [] with the appropriate content
            #  (starting with the last two, and then from the top)
            uPow[i]['desc'] = uPow[i]['desc'].replace('ooldown: []', 'ooldown: '+str(digits.pop()), 1);
            uPow[i]['desc'] = uPow[i]['desc'].replace('ate: []%', 'ate: '+str(digits.pop())+'%', 1);
            digits.reverse();
            itr = uPow[i]['desc'].count('[]');
            while(itr and digits):
                uPow[i]['desc'] = uPow[i]['desc'].replace('[]', str(digits.pop()), 1);
                itr -= 1;

            # Replace all {} with the appropriate content
            typ = uPow[i]['json']['type'];
            if(typ == 0): typ = 'Offensive';
            elif(typ == 1): typ = 'Defensive';
            elif(typ == 2): typ = 'Utility';
            elif(typ == 3): typ = 'Power Move';
            
            uPow[i]['desc'] = uPow[i]['desc'].replace('{}', typ, 1);

            # Replace all inner expressions -> $() <- with their evaluated counterparts
            itr = uPow[i]['desc'].count('$(');
            while(itr):
                it = uPow[i]['desc'].find('$(');
                uPow[i]['desc'] = uPow[i]['desc'].replace(uPow[i]['desc'][it:(it + uPow[i]['desc'][it:].find(')') + 1)], str(eval(uPow[i]['desc'][it+2:(it + uPow[i]['desc'][it+2:].find(')') + 2)])));
                itr -= 1;

            # Replace all inner expressions -> @^^ <- with their executed counterparts
            itr = uPow[i]['desc'].count('@^');
            while(itr):
                it = uPow[i]['desc'].find('@^');
                res2 = uPow[i]['desc'][it+2:(it + uPow[i]['desc'][it+2:].find('^') + 2)];
                exec('res = str('+(res2 if res2 else 'None')+').strip()');
                uPow[i]['desc'] = uPow[i]['desc'].replace('@^'+res2+'^', (res if res else 'UNDEFINED'));
                itr -= 1;
                
        temp_arr = {};
        for special in uPow: temp_arr[special['name']] = {'desc':special['desc'], 'json':special['json'], 'sp':special['sp']};
        
        # Structure the user's powers into a workable menu object
        powerStructure = {};
        for power in temp_arr.keys(): powerStructure[str(power).lower()] = str(power);
        powerStructure = sorted(powerStructure.items(), key=lambda t:t[0]);
        powerStructure.extend([('guess', -1), ('skip', -2), ('help', -3)]);
        powerStructure = OrderedDict(powerStructure);

        # Return all this wonderful information!
        return (uDat, temp_arr, powerStructure);
    Display.errorMsg('Server connection rejected!');
    MAR_exit(1);

# Evaluate the specials array one last time, and then push the client's new stat data to the server
# Tell user the battle results
def finalEvaluation(data, opponent):
    global conn1, usedSpecials;
    if(data['userdata']['victory'] != -1):
        if(data['userdata']['victory'] == True):
            if(settings['playSounds']): MessageBeep(beep); time.sleep(0.1); MessageBeep(beep); time.sleep(0.1); MessageBeep(beep);
            conn1.params = {"u":u, "p":p, "python":1, "type":"upd", "SID":SID, 'data':'$Win:'+data['username']};
            conn1.request();
            xp = str(int(floor(data['userdata']['remainingTurns'] / 4)));
            data2 = xp+',0,1';
            Display.playerMsg('Good job,', data['username']+'!');
            Display.gameMsg("You've defeated", opponent, 'in', (data['userdata']['maxTurns'] - data['userdata']['remainingTurns']), 'turns.');
            Display.gameMsg("You've earned", xp, 'SP point(s)!');
            
        elif(data['userdata']['victory'] == False):
            if(settings['playSounds']): MessageBeep(MB_OK); time.sleep(0.1); MessageBeep(MB_OK); time.sleep(0.1); MessageBeep(MB_OK);
            conn1.params = {"u":u, "p":p, "python":1, "type":"upd", "SID":SID, 'data':'$Win:'+opponent};
            conn1.request();
            data2 = '1,1,0';
            Display.errorMsg("You failed", data['username']+".");
            Display.errorMsg("You've lost to", opponent+".");
            Display.errorMsg("The correct answer was " + data['userdata']['answer'] + ".");
            Display.gameMsg("You've received 1 SP point.");

        conn1.params = {"u":u, "p":p, "python":1, "type":"psh", "SID":SID, 'data':data2};
        response = conn1.request();
        if(response):
            if(response[0:7] == 'Leveled'): Display.gameMsg('-+-+-+-+ Congratulations! You are now level '+response[8:]+' +-+-+-+-');
            elif(response == 'Updated'): Display.gameMsg('Server updated successfully.');
            else: Display.errorMsg('Server update failed! ('+str(response)+')');
        else: Display.errorMsg('Server update failed! (could not establish connection)');

        # Display useage statistics
        if(len(usedSpecials) > 0):
            Display.gameMsg('\n  Useage Statistics:');
            Display.gameMsg('------------------');
            temp_array = {};
            for name in usedSpecials:
                if(temp_array.get(name)): temp_array[name] = temp_array[name] + 1;
                else: temp_array[name] = 1;
            for name in temp_array.keys(): Display.gameMsg('-', name, 'was used', temp_array[name], 'times');
            Display.gameMsg('------------------\n');
        Display.errorMsg('Game Over.');

def checkForCommands(response, actionQueue, opponent):
    global conn1, globalskip;
    doBreak = False;
    
    if(response == '$Skipped:'+actionQueue['username']):
        conn1.params = {"u":u, "p":p, "python":1, "type":"upd", "SID":SID, 'data':'$ClearGameData'};
        conn1.request();
        Display.errorMsg('Temporarily desynched from the server. Your actions were discarded.');
        globalskip = True;
    elif(response == '$Skipped:'+opponent):
        Display.errorMsg('Your opponent has desynched from the server. You have been declared winner.');
        doBreak = True;
        actionQueue['userdata']['victory'] = True;
        finalEvaluation(actionQueue, opponent);
    elif(response == '$Updated'): Display.gameMsg("Synchronization complete.");
    elif(response == '$Win:'+opponent):
        actionQueue['userdata']['victory'] = False;
        finalEvaluation(actionQueue, opponent);
        doBreak = True;
    elif(response == '$Win:'+actionQueue['username']):
        actionQueue['userdata']['victory'] = True;
        finalEvaluation(actionQueue, opponent);
        doBreak = True;
    else:
        if(response == '$Alive:'+opponent or response == '$Yes' or response == '$Skipped:'+opponent):
            conn1.params = {"u":u, "p":p, "python":1, "type":"upd", "SID":SID, 'data':'$Die'};
            conn1.request();
            Display.errorMsg('Due to your opponent\'s excessive lag, the game has been canceled.');
            
        elif(response == '$Alive:'+actionQueue['username']):
            conn1.params = {"u":u, "p":p, "python":1, "type":"upd", "SID":SID, 'data':'$Die'};
            conn1.request();
            Display.errorMsg('Due to your excessive lag, the game has been canceled.');
            
        elif(response == '$Die'):
            Display.errorMsg('The game has been canceled unexpectedly. Probably due to lag.');
            
        else:
            if(str(response) != 'False'):
                Display.errorMsg('Bad response from server. Game Over.');
                conn1.params = {"u":u, "p":p, "python":1, "type":"upd", "SID":SID, 'data':'$Die'};
                conn1.request();
                Display.errorMsg('>>', response);
            else: Display.errorMsg('Disconnected from game server. Game Over.');
            
        actionQueue['userdata']['victory'] = -1;
        doBreak = True;
    return (actionQueue, doBreak);

# Evalute the current standing of the specials array
def evaluateQueue(data1, user=True, data2=None):
    
    # Evaluating the user's data
    if(user and data1):
        # Report to user everything that needs to be reported (losses, gains, effects waring off, etc.) in the beginning of the user's turn
        
        # Execute specials that exist in specialdata
        for name in data1['specialdata'].keys():
            if((data1['specialdata'][name]['cooldown'][0] <= 0 and not data1['specialdata'][name]['cooldown'][1]) or data1['specialdata'][name]['cooldown'][0] > 0):
                print '    Evaluating special', name, '...' #
                fx = data1['specialdata'][name]['effects'];
                
                # First search for a duration
                duration = False;
                durDex = 0;
                for durDex, effect in enumerate(fx):
                    if(effect[0] == 'duration'):
                        duration = effect[1];
                        print '        Found duration', duration #
                        if(duration == -1 and effect[2] == False): duration = data1['specialdata'][name]['effects'][durDex][1] = -2; print '        Infinite duration found, dumping to -2...' #
                        data1['specialdata'][name]['effects'][durDex][2] = True;
                        break;
                else: print '        No duration found.' #

                
                if(duration >= 0):
                    # Loop through effects from the special
                    for i, effect in enumerate(fx):
                        if(effect[0] != 'duration' and not effect[2]):
                            print '        Executing effect', effect, '...' #
                            # Evaluate the effect we've been given
                            if(effect[0] == 'winTheGame'): data1['userdata']['victory'] = True;
                            elif(effect[0] == 'modTurnCnt'):
                                data1['userdata']['remainingTurns'] += effect[1];
                                data1['updateText'].append(name+': turn count is now '+str(data1['userdata']['remainingTurns'])+'.');
                            elif(effect[0] == 'noSpecials'): data1['effectdata']['nospec'] = True;
                            elif(effect[0] == 'removePoison'):
                                if(data1['specialdata'].get('poison') != None): del data1['specialdata']['poison'];
                                if(data1['durabledata'].get('poison') != None): del data1['durabledata']['poison'];
                            elif(effect[0] == 'revealStats'): data1['effectdata']['revstats'] = True;
                            elif(effect[0] == 'modChance'):
                                data1['updateText'].append(name+': global chance '+('is now at' if effect[1][0] == '=' else ('was positively modified by' if effect[1][0] == '+' else 'was negatively modified by'))+' '+str(int(effect[1][1]*100))+'%.');
                                if(effect[1][0] == '='):
                                    data1['userdata']['gChanceMutator'][0] = effect[1][1];
                                    data1['userdata']['gChanceMutator'][1] = effect[1][1];
                                    data1['userdata']['gChanceMutator'][2] = effect[1][1];
                                else:
                                    data1['userdata']['gChanceModifier'][0] += float(effect[1][0]+str(effect[1][1]));
                                    data1['userdata']['gChanceModifier'][1] += float(effect[1][0]+str(effect[1][1]));
                                    data1['userdata']['gChanceModifier'][2] += float(effect[1][0]+str(effect[1][1]));
                            elif(effect[0] == 'mod0Chance'):
                                data1['updateText'].append(name+': offensive chance '+('is now at' if effect[1][0] == '=' else ('was positively modified by' if effect[1][0] == '+' else 'was negatively modified by'))+' '+str(int(effect[1][1]*100))+'%.');
                                if(effect[1][0] == '='): data1['userdata']['gChanceMutator'][0] = effect[1][1];
                                else: data1['userdata']['gChanceModifier'][0] += float(effect[1][0]+str(effect[1][1]));
                            elif(effect[0] == 'mod1Chance'):
                                data1['updateText'].append(name+': defensive chance '+('is now at' if effect[1][0] == '=' else ('was positively modified by' if effect[1][0] == '+' else 'was negatively modified by'))+' '+str(int(effect[1][1]*100))+'%.');
                                if(effect[1][0] == '='): data1['userdata']['gChanceMutator'][1] = effect[1][1];
                                else: data1['userdata']['gChanceModifier'][1] += float(effect[1][0]+str(effect[1][1]));
                            else: print '        Effect', effect, 'was NOT executed (not found).' # This whole line should be erased
                            
                            # Update any duration-related data
                            if(not duration):
                                data1['specialdata'][name]['effects'][i][2] = True;
                                if(data1['effectdata'].get(name)): del data1['effectdata'][name];
                            else: data1['specialdata'][name]['effects'][durDex][1] = duration-1;
                        else: print '        Effect', effect, 'was NOT executed.' # This whole line should be erased
                elif(duration == -2): data1['durabledata'][name] = deepcopy(data1['specialdata'][name]['effects']); print '        Specials from', name, 'were added to the durabledata array!' #
                else: print '        Duration over. No effects executed.' # This whole line should be erased
            else: print '    Skipped evaluating special', name+'!' # This whole line should be erased

        # Loop through durable data
        for name in data1['durabledata'].keys():
            print '    Evaluating DURABLE (infinite) special', name, '...' #
            fx = data1['durabledata'][name];
            for i, effect in enumerate(fx):
                if(effect[0] != 'duration'):
                    print '          Durable (infinite) Effect', effect, 'is being executed...' #
                    if(effect[0] == 'modChance'):
                        data1['updateText'].append(name+': global chance '+('is now at' if effect[1][0] == '=' else ('was positively modified by' if effect[1][0] == '+' else 'was negatively modified by'))+' '+str(int(effect[1][1]*100))+'%.');
                        if(effect[1][0] == '='):
                            data1['userdata']['gChanceMutator'][0] = effect[1][1];
                            data1['userdata']['gChanceMutator'][1] = effect[1][1];
                            data1['userdata']['gChanceMutator'][2] = effect[1][1];
                        else:
                            data1['userdata']['gChanceModifier'][0] += float(effect[1][0]+str(effect[1][1]));
                            data1['userdata']['gChanceModifier'][1] += float(effect[1][0]+str(effect[1][1]));
                            data1['userdata']['gChanceModifier'][2] += float(effect[1][0]+str(effect[1][1]));
                    elif(effect[0] == 'mod0Chance'):
                        data1['updateText'].append(name+': offensive chance '+('is now at' if effect[1][0] == '=' else ('was positively modified by' if effect[1][0] == '+' else 'was negatively modified by'))+' '+str(int(effect[1][1]*100))+'%.');
                        if(effect[1][0] == '='): data1['userdata']['gChanceMutator'][0] = effect[1][1];
                        else: data1['userdata']['gChanceModifier'][0] += float(effect[1][0]+str(effect[1][1]));
                    elif(effect[0] == 'mod1Chance'):
                        data1['updateText'].append(name+': defensive chance '+('is now at' if effect[1][0] == '=' else ('was positively modified by' if effect[1][0] == '+' else 'was negatively modified by'))+' '+str(int(effect[1][1]*100))+'%.');
                        if(effect[1][0] == '='): data1['userdata']['gChanceMutator'][1] = effect[1][1];
                        else: data1['userdata']['gChanceModifier'][1] += float(effect[1][0]+str(effect[1][1]));
                    else: print '        Infinity effect', effect, 'was NOT executed (not found).' # This whole line should be erased
                else: print '          Durable (infinite) Effect', effect, 'was NOT executed.' # This whole line should be erased
        
        # One cooldown cycle has passed!
        for special in data1['specialdata'].keys():
            if((data1['specialdata'][special]['cooldown'][0] <= 0 and data1['specialdata'][special]['cooldown'][1]) or data1['specialdata'][special]['cooldown'][0] < 0):
                del data1['specialdata'][special];
            else: data1['specialdata'][special]['cooldown'] = (data1['specialdata'][special]['cooldown'][0]-1, True);
        return data1;

    # Evaluating the opponent's data
    elif(not user and data2):
        # Report to user everything that needs to be reported (losses, gains, effects waring off, etc.)
        return data2;
    
    else:
        Display.errorMsg('Invalid parameters passed to evaluateQueue (', data1, ') [', data2, '].');
        MAR_exit(1);

# Start a head2head battle
def MAR_battle(opponent, first):
    print '';
    global conn1, heartbeat, loggedIn, userdict, userpowers, powerStructure, ascii_uppercase, globalskip, usedSpecials;
    if(not conn1 or not loggedIn): MAR_exit(3);
    
    # Finish setting up our environment
    # Special data (meant for keeping track of turns)
    # Durable data (meant for keeping up with infinite effects)
    # Effect data (meant for storing temporary data to be used by the different effects each turn)
    # UpdateText (meant for storing phrases that will be printed out when the user's turn begins)
    actionQueue = {'username':userdict['username'], 'specialdata':{}, 'durabledata':{}, 'effectdata':{}, 'updateText':[],
                   'userdata':{
                       'guess':None,
                       'miniTurns':0,
                       'remainingTurns':27,
                       'maxTurns':28,
                       'letterNum':1,
                       'answer':None,
                       'answerStatus1':None,
                       'answerStatus2':None,
                       'skipped': False,
                       'victory': False,
                       'gChanceModifier': [0, 0, 0, 0],
                       'gChanceMutator': [-1, -1, -1, -1]
                   }};

    # Begin the game
    firstplay = True;
    while(actionQueue['userdata']['remainingTurns'] > 0 and not actionQueue['userdata']['victory']):
        if(actionQueue['userdata']['letterNum'] <= 4 and not actionQueue['userdata']['victory']):
            # We're up!
            if(first):
                if(not actionQueue['userdata']['skipped']):
                    # Set up our environment
                    if(actionQueue['userdata']['answer'] == None):
                        actionQueue['userdata']['answer'] = ascii_uppercase[randint(0, 25)];
                        Display.gameMsg('--> For you, this is letter '+str(actionQueue['userdata']['letterNum'])+' of 4.');
                    if(firstplay):
                        Display.gameMsg('[To use your specials, type the special\'s name and press "enter"]');
                        Display.gameMsg('[To guess, type "guess" followed by your letter guess.]');
                        Display.gameMsg('[To skip your turn, type "skip" and press "enter"]');
                        Display.gameMsg('[For help with a specific special, type "help" and press "enter"]');
                        Display.gameMsg('[You have 60 seconds until your turn is automatically skipped]');
                        firstplay = False;
                    else:
                        print '';
                        if(len(actionQueue['updateText']) > 0):
                            for i, text in enumerate(actionQueue['updateText']):
                                Display.evnMsg('--|', text);
                                del actionQueue['updateText'][i];
                        if(len(actionQueue['specialdata']) > 0):
                            for special in actionQueue['specialdata'].keys():
                                cool = actionQueue['specialdata'][special]['cooldown'][0];
                                if(cool <= 0): Display.gameMsg('|-|', special, 'can now be invoked again!');
                                else: Display.gameMsg('|||', special, 'is cooling down for ['+str(cool)+'] more turns.');

                    if(not globalskip):
                        i = -3;
                        sleeptime = time.clock();
                        while(i == -3):
                            # Prompt for selection of powers or guess (60 second time limit)
                            if(not globalskip):
                                if(actionQueue['effectdata'].get('nospec') != None and actionQueue['effectdata']['nospec']):
                                    i = Display.menu(OrderedDict([('guess', -1), ('skip', -2), ('help', -3)]), initMsg='Your move:', prefix='- ', time_limit=(60-(time.clock()-sleeptime)), limit_phrase='skip');
                                    del actionQueue['effectdata']['nospec'];
                                else: i = Display.menu(powerStructure, initMsg='Your move:', prefix='- ', time_limit=(60-(time.clock()-sleeptime)), limit_phrase='skip');
                            if(not globalskip):
                                # User wants to guess normally
                                if(i == -1):
                                    if(actionQueue['userdata']['guess'] != None and actionQueue['userdata']['answerStatus2'] not in ['', None]): Display.gameMsg('-> You previous guess was:', actionQueue['userdata']['guess'], '('+actionQueue['userdata']['answerStatus2'][:-1].lower()+')');
                                    actionQueue['userdata']['guess'] = Display.timed_input('> Guess a letter, '+actionQueue['username']+': ', 'skip', 60 - (time.clock() - sleeptime));
                                    if(actionQueue['userdata']['guess'] == 'skip'): actionQueue['userdata']['skipped'] = True;
                                    elif(actionQueue['userdata']['guess'] in ascii_letters):
                                        if(actionQueue['userdata']['guess'].upper() == actionQueue['userdata']['answer']):
                                            actionQueue['userdata']['miniTurns'] = actionQueue['userdata']['miniTurns'] + 1;
                                            Display.gameMsg("You've guessed correctly! (Total", actionQueue['userdata']['miniTurns'], "turns)");
                                            actionQueue['userdata']['letterNum'] = actionQueue['userdata']['letterNum'] + 1;
                                            if(actionQueue['userdata']['letterNum'] <= 4 and not actionQueue['userdata']['victory']):
                                                if(settings['playSounds']): MessageBeep(beep); time.sleep(0.1); MessageBeep(beep);
                                                actionQueue['userdata']['answerStatus1'] = actionQueue['username']+" guessed correctly and is onto the next letter! (Letter "+str(actionQueue['userdata']['letterNum'])+" of 4)";
                                                actionQueue['userdata']['answerStatus2'] = '';
                                                actionQueue['userdata']['miniTurns'] = 0;
                                                actionQueue['userdata']['answer'] = None;
                                            else:
                                                actionQueue['userdata']['victory'] = True;
                                                finalEvaluation(actionQueue, opponent);
                                                break;
                                        else:
                                            dist = distanceAlgorithm(ascii_uppercase, actionQueue['userdata']['guess'].upper(), actionQueue['userdata']['answer'], 4.0, 40);
                                            actionQueue['userdata']['answerStatus1'] = actionQueue['username']+' guessed incorrectly!';
                                            actionQueue['userdata']['answerStatus2'] = "Guess was "+dist;
                                            print Display.errorWrapper() + "Incorrect! Your guess was", dist;
                                    else:
                                        Display.errorMsg("That's not a letter,", actionQueue['username']+". You've lost two turns for that!");
                                        actionQueue['userdata']['answerStatus1'] = actionQueue['username']+' entered an invalid response and was penalized!\n  What a fool!';
                                        actionQueue['userdata']['answerStatus2'] = 'Guess was invalid.';
                                        actionQueue['userdata']['remainingTurns'] = actionQueue['userdata']['remainingTurns'] - 2;
                                        actionQueue['userdata']['miniTurns'] = actionQueue['userdata']['miniTurns'] + 1;

                                # User wants help on a specific power
                                elif(i == -3):
                                    response = Display.timed_input('> Which special would you like help on, '+actionQueue['username']+'? ', 'skip', 60 - (time.clock() - sleeptime));
                                    if(response == 'skip'):
                                        actionQueue['userdata']['skipped'] = True;
                                        break;
                                    elif(response.title() not in userpowers): Display.errorMsg('Invalid selection.');
                                    else: Display.gameMsg('\nDescription: '+userpowers[response.title()]['desc']);
                                    Display.evnMsg('\n  **You have', int(floor(60-(time.clock()-sleeptime))), 'seconds remaining**');

                                # User wants to skip their turn
                                elif(i == -2): actionQueue['userdata']['skipped'] = True;

                                # A special was chosen, attempt to activate it
                                else:
                                    selectedPower = userpowers[i]['json'];
                                    actionQueue['userdata']['guess'] = None;
                                    actionQueue['userdata']['miniTurns'] = actionQueue['userdata']['miniTurns'] + 1;
                                    
                                    # Check if special doesn't allow itself to be used more than once + exists in the usedSpecials list
                                    if(selectedPower['cooldown'][0] < 0 and i in usedSpecials):
                                        Display.errorMsg('That special can only be used once (and has already been used)!');
                                        actionQueue['userdata']['answerStatus1'] = actionQueue['username']+' attempted to activate "'+i+'" but failed!';
                                    elif(i in actionQueue['specialdata'].keys() and actionQueue['specialdata'][i]['cooldown'][0] > 0):
                                        Display.errorMsg('You must wait at least', actionQueue['specialdata'][i]['cooldown'][0], 'turns before you can use that special!');
                                        actionQueue['userdata']['answerStatus1'] = actionQueue['username']+' attempted to activate "'+i+'" but failed!';
                                    else:
                                        # Check if chance is being affected by something, and, if so, make it the new chance
                                        chance = selectedPower['chance'][0];
                                        powType = selectedPower['type'];
                                        if(actionQueue['userdata']['gChanceMutator'][powType] != -1): chance = float(actionQueue['userdata']['gChanceMutator'][powType]);
                                        else: chance += float(actionQueue['userdata']['gChanceModifier'][powType]);
                                        
                                        # If chance succeeds, invoke the special!
                                        if(random() <= chance):
                                            Display.evnMsg('=+=+=+=+ You used the special', i+'! +=+=+=+=');
                                            actionQueue['specialdata'][i] = selectedPower;
                                            usedSpecials.append(i);
                                            if(selectedPower['cooldown'][0] == -1): del powerStructure[i.lower()];
                                            if(i.find(':')+1): actionQueue['userdata']['answerStatus1'] = '>> '+actionQueue['username'].upper()+' EXECUTED A POWER MOVE BY UTTERING THE WORD "'+i[12:].upper()+'"! << <-';
                                            else: actionQueue['userdata']['answerStatus1'] = actionQueue['username']+' has successfully activated the "'+i+'" special <-\n';
                                        else:
                                            actionQueue['userdata']['answerStatus1'] = actionQueue['username']+' attempted to activate "'+i+'" but failed!';
                                            Display.evnMsg('=+=+ You attempted to use', i, 'but failed! +=+=');
                                        actionQueue['userdata']['answerStatus2'] = None;
                            else: actionQueue['userdata']['skipped'] = True; globalskip = False;
                    else: actionQueue['userdata']['skipped'] = True; globalskip = False;
                if(actionQueue['userdata']['skipped']):
                    actionQueue['userdata']['guess'] = actionQueue['userdata']['answerStatus1'] = None;
                    actionQueue['userdata']['answerStatus2'] = None;
                    actionQueue['userdata']['miniTurns'] = actionQueue['userdata']['miniTurns'] + 1;

                # Evaluate specialdata array & victory conditions (return luck to normal)
                actionQueue['userdata']['gChanceModifier'] = [0, 0, 0, 0];
                actionQueue['userdata']['gChanceMutator'] = [-1, -1, -1, -1];
                actionQueue = evaluateQueue(deepcopy(actionQueue));
                Display.gameMsg('Turn ended!');
                Display.gameMsg("You have", (actionQueue['userdata']['remainingTurns'] if actionQueue['userdata']['remainingTurns'] > 0 else 'no'), "turns remaining.");
                Display.gameMsg("Synchronizing with server...");
                conn1.params = {"u":u, "p":p, "python":1, "type":"upd", "SID":SID, 'data':actionQueue};
                response = conn1.request();

                if(response == '$UpdateFailed'): Display.errorMsg('Internal Error: server failed to update properly! Report this!');
                if(response == '$LookupError'): Display.errorMsg('Internal Error: server-user lookup error! Report this!');
                else:
                    actionQueue, doBreak = checkForCommands(response, actionQueue, opponent);
                    if(doBreak): break;
                
                actionQueue['userdata']['remainingTurns'] = actionQueue['userdata']['remainingTurns'] - 1;
                actionQueue['userdata']['miniTurns'] = actionQueue['userdata']['miniTurns'] + 1;
                actionQueue['userdata']['skipped'] = False;
                
            # They're up! (wait for 60[+10] seconds)
            else:
                Display.gameMsg('Waiting on', opponent+' (~60 seconds until timeout)...');
                response = block_on_challenge('$NoData', {"u":u, "p":p, "python":1, "type":"bat4", "SID":SID, 'opponent':opponent}, at_end=0, stall_time=70);
                
                if(is_JSON(response)):
                    if(response['username'] != actionQueue['username']):
                        if(response['userdata']['answerStatus1']):
                            if(response['userdata']['answerStatus1'].find('guessed correctly and is onto')+1 and settings['playSounds']): MessageBeep(MB_OK); time.sleep(0.1); MessageBeep(MB_OK);
                            elif(response['userdata']['answerStatus1'].find('has successfully activated the')+1): print '';
                            elif(response['userdata']['answerStatus1'].find('EXECUTED A POWER MOVE')+1): Display.evnMsg('\n  The ground shakes as thunder rolls and lightning dances across the sky...');
                            Display.evnMsg('->', response['userdata']['answerStatus1']);
                            if(response['userdata']['answerStatus1'].find('EXECUTED A POWER MOVE')+1): Display.evnMsg('You stand in awe before one of the great Power Words of legend.\n');
                            if(actionQueue['effectdata'].get('revstats') != None and actionQueue['effectdata']['revstats'] and response['userdata']['answerStatus2'] not in['', None]):
                                Display.gameMsg('->>', response['userdata']['answerStatus2']);
                                del actionQueue['effectdata']['revstats'];
                        else: Display.gameMsg('->', opponent, 'skipped his turn?! Foolish!');
                        actionQueue = evaluateQueue(deepcopy(response), False, deepcopy(actionQueue));
                        Display.sysMsg('Opponent\'s turn ended. Your move!');
                    else:
                        actionQueue, doBreak = checkForCommands('$Die', actionQueue, opponent);
                        if(doBreak): break;
                            
                elif(not response):
                    # Send the "is alive ne?" packet
                    Display.gameMsg('No response from opponent, clearing victory conditions...');
                    conn1.params = {"u":u, "p":p, "python":1, "type":"upd", "SID":SID, 'data':'$Alive:'+opponent};
                    conn1.request();
                    response = block_on_challenge('$NoData', {"u":u, "p":p, "python":1, "type":"bat4", "SID":SID, 'opponent':opponent, "ignore":'$Alive:'+opponent}, at_end=0, stall_time=10, eval_response=False);

                    if(not response):
                        Display.gameMsg('Opponent has disconnected from the server. You win by default.');
                        actionQueue['userdata']['victory'] = True;
                        finalEvaluation(actionQueue, opponent);
                        break;
                    
                    elif(is_JSON(response)):
                        Display.gameMsg('Experiencing data delay...');
                        print response;
                        if(response['username'] != actionQueue['username']):
                            if(response['userdata']['answerStatus1']):
                                if(response['userdata']['answerStatus1'].find('guessed correctly and is onto')+1 and settings['playSounds']): MessageBeep(MB_OK); time.sleep(0.1); MessageBeep(MB_OK);
                                elif(response['userdata']['answerStatus1'].find('has successfully activated the')+1): print '';
                                elif(response['userdata']['answerStatus1'].find('EXECUTED A POWER MOVE')+1): Display.evnMsg('\n  The ground shakes as thunder rolls and lightning dances across the sky...');
                                Display.evnMsg('->', response['userdata']['answerStatus1']);
                                if(response['userdata']['answerStatus1'].find('EXECUTED A POWER MOVE')+1): Display.evnMsg('You stand in awe before one of the great Power Words of legend.\n');
                            else: Display.gameMsg('->', opponent, 'skipped his turn?! Foolish!');
                            actionQueue = evaluateQueue(deepcopy(response), False, deepcopy(actionQueue));
                            Display.sysMsg('Opponent\'s turn ended. Your move!');
                        else:
                            actionQueue, doBreak = checkForCommands('$Die', actionQueue, opponent);
                            if(doBreak): break;
                        
                    elif(response == '$Yes'):
                        Display.gameMsg('Opponent\'s turn was skipped.');
                        conn1.params = {"u":u, "p":p, "python":1, "type":"upd", "SID":SID, 'data':'$Skipped:'+opponent};
                        conn1.request();
                        time.sleep(3);

                    else:   
                        actionQueue, doBreak = checkForCommands(response, actionQueue, opponent);
                        if(doBreak): break;
                else:   
                    actionQueue, doBreak = checkForCommands(response, actionQueue, opponent);
                    if(doBreak): break;

            #Change up the order
            first = not first;
            
        else:
            actionQueue['userdata']['victory'] = True;
            finalEvaluation(actionQueue, opponent);
            break;
    else:
        if(not actionQueue['userdata']['victory']): finalEvaluation(actionQueue, opponent);

    Display.sysMsg('Cleaning up room...');
    globalskip = False;
    usedSpecials = [];
    conn1.params = {"u":u, "p":p, "python":1, "type":"kil", "SID":SID};
    conn1.request();
    Display.sysMsg('Room sanitized successfully.');
    Display.gameMsg('Returning to main menu...');
    heartbeat.pauseFlag = False;
    conn1.makeNulls = False;
    
# Begin the main python code
try:
    MAR_load_settings();
    while(True):
        # Staying away from my complex menu object, since explaining it in a write up would be... well, complex.
        i = Display.menu(OrderedDict([('free play', 0), ('local play', 1), ('online play', 2), ('exit', 3)]), initMsg='Select Your Gameplay Mode:', prefix='# ');
        
        # Free play mode, which is basically the game as it was originally intended
        if(i == 0):
            gameNum = 0;
            state = 'y';
            name = Display.cooked_input("> What's your name? "); # Python doesn't even have a do-while?! Wow. Really? ... Really? What a waste of code.
            
            while not re.match('^[0-9a-zA-Z_]{4}[0-9a-zA-Z_]*$', name) and 4 <= name <= 25: # ^[0-9a-zA-Z_]{4,25}$ wasn't working for some odd reason >.<
                Display.errorMsg('Invalid name! Numbers/Letters only (between 4 and 25 chars).');
                name = Display.cooked_input("> What's your name? ");

            Display.gameMsg('Welcome to the Letter Guessing Game,', name+'!');
            
            while state == 'y':

                # Finish setting up our environment
                tries = 0;
                maxTries = 7;
                answer = ascii_uppercase[randint(0, 25)];
                gameNum = gameNum + 1;
                Display.gameMsg('For you, this is game #'+str(gameNum)+'.');

                # Begin the game
                while tries < maxTries:
                    guess = Display.cooked_input('> Guess a letter, '+name+': ');
                    
                    if(guess in ascii_letters):
                        if(guess.upper() == answer):
                            Display.gameMsg("You've guessed correctly! (Total", (tries + 1), "turns)");
                            answer = -1;
                            break;
                        
                        else:
                            print Display.errorWrapper() + "Incorrect! Your guess was", distanceAlgorithm(ascii_uppercase, guess.upper(), answer, 4.0, 40);
                                
                    else:
                        Display.errorMsg("That's not a letter,", name+". You've lost two turns for that!");
                        maxTries = maxTries - 2;
                        
                    report = maxTries - (tries + 1);
                    Display.gameMsg("You have", (report if report > 0 else 'no'), "tries remaining.");
                    tries = tries + 1;
                    
                if(answer == -1): Display.playerMsg('Good job!');
                else:
                    Display.errorMsg("You failed", name+".");
                    Display.errorMsg("The correct answer was " + answer + ".");
                state = Display.cooked_input('> Try again? (y/n) ');
            
        # Play mode which would allow players to grab their stats from the server and play a local head2head match
        elif(i == 1): Display.gameMsg('Unfortunately, this gameplay mode is not available yet!');
        
        # We're in Online Play mode!
        elif(i == 2):
            # Tell the user that we're asking the server for a new encryption key
            Display.sysMsg("Handshaking with server..."); # Go pre-emptive handshake!

            # Ask for, obtain, and store the the encryption key
            switch = False;
            response = conn1.requestKey();

            if(response != False):
                switch = True;
                KEY = response[0];
                SID = response[2];
            else:
                Display.errorMsg('Connection was rejected (maybe to too many people playing for too long?)');
                Display.errorMsg('Please try again later.');
            
            while(not loggedIn and switch):
                i = Display.menu(OrderedDict([('login', 0), ('register', 1), ('back', 2)]), initMsg='Select an option:', prefix='# ');

                # We're attempting to log someone in
                if(i == 0):
                    u = Display.cooked_input("> Username: ");
                    p = Display.getpass("> Password:");

                    # Tell the user that we're doing things
                    Display.sysMsg("\n  Conversing with server...");

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
                                                            
                            # Grab the user's player data and store it as a dictionary
                            response = restruct();
                            if(response != False):
                                userdict, userpowers, powerStructure = response;
                                loggedIn = True;
                                
                                # Welcome the user
                                Display.playerMsg("Welcome to Online Mini-MAR,", userdict["username"]+"!");
                                
                                # Report any bugs you may find in this program to trefighter2334@aol.com ASAP, thanks!
                                Display.adminMsg("Please report any bugs you may find to trefighter2334@aol.com");

                                # Start polling the server for challenge requests
                                heartbeat = Challenger(conn1.baseSite, conn1.target, {"u":u, "p":p, "python":1, "type":"bat", "SID":SID});
                                
                                while(loggedIn):
                                    i = Display.menu(OrderedDict([('challenge', 0), ('whois', 1), ('powers', 4), ('settings', 5), ('logout', 2), ('exit', 3)]), initMsg='Available Options:', prefix='# ');

                                    # Challenge someone! Woooo!
                                    if(i == 0):
                                        heartbeat.pauseFlag = True;
                                        conn1.params = {"u":u, "p":p, "python":1, "type":"cha", "SID":SID};
                                        conn1.params['chal'] = Display.cooked_input('> Enter the username of the player you\'d like to challenge: ');
                                        Display.sysMsg('Conversing with the server...');
                                        response = conn1.request();

                                        # Waiting for Challengee to accept/deny
                                        if(response == "$ChallengerWaiting"):
                                            Display.gameMsg('Waiting for a response from', conn1.params['chal']+'...');
                                            response = block_on_challenge('$NoDice', {"u":u, "p":p, "python":1, "type":"bat2", "SID":SID});
                                            if(response != False):
                                                first = (False if response['opponent'] == response['first'] else True);
                                                Display.evnMsg('Challenge Accepted! '+(response['opponent']+' is' if not first else 'You\'re') + ' up first.');
                                                Display.sysMsg('Preparing battlefield...');
                                                time.sleep(5);
                                                MAR_battle(response['opponent'], first);
                                                userdict, userpowers, powerStructure = restruct();
                                            else: Display.errorMsg("Connection to server was dropped. Please try again.");

                                        # Waiting for challenger's client to acknowledge our acceptance of their initial challenge
                                        elif(response == "$ChallengedWaiting"):
                                            Display.sysMsg('Waiting for acknowlegement...');
                                            response = block_on_challenge('$NoDice', {"u":u, "p":p, "python":1, "type":"bat3", "SID":SID});
                                            
                                            if(response != False):
                                                first = (False if response['opponent'] == response['first'] else True);
                                                Display.evnMsg('Challenge Acknowledged! '+(response['opponent']+' is' if not first else 'You\'re') + ' up first.');
                                                Display.sysMsg('Preparing battlefield...');
                                                time.sleep(5);
                                                MAR_battle(response['opponent'], first);
                                                userdict, userpowers, powerStructure = restruct();
                                            else: Display.errorMsg("Connection to server was dropped. Please try again.");
                                                
                                        else:
                                            if(response == "$NoMatch"): Display.errorMsg('Invalid or bad username.');
                                            elif(response == "$Busy"): Display.errorMsg('That user is already in a game!');
                                            elif(response == "$Illegal"): Display.errorMsg('You cannot challenge yourself!');
                                            elif(response == "$AlreadyWaiting"): Display.errorMsg('You already have a challenge pending. Try again later.');
                                            else:
                                                if(not response): Display.errorMsg("Connection to server was dropped. Please try again.");
                                                else:
                                                    Display.errorMsg("Error. The response received from server was unrecognizable.");
                                                    Display.errorMsg(">>", response);
                                                
                                            heartbeat.pauseFlag = False;

                                    # Request information on another user     
                                    elif(i == 1):
                                        conn1.params = {"u":u, "p":p, "python":1, "type":"req", "SID":SID};
                                        conn1.params['stat'] = Display.cooked_input('> Enter the username of the player you\'d like information on: ');
                                        Display.sysMsg('Conversing with the server...');
                                        response = conn1.request();
                                        if(response != False):
                                            if(response == "BadUser"): Display.errorMsg('Invalid or bad username.');
                                            else: Display.gameMsg(Display.newline+'  '+response, '\n');
                                        else: Display.errorMsg('Your request failed. Please try again.');

                                    # Logout of the program and return to the main options screen
                                    elif(i == 2):
                                        # Di~e!
                                        itera = 0;
                                        conn1.params = {"u":u, "p":p, "python":1, "type":"out", "SID":SID};
                                        Display.sysMsg('Attempting to log you out of the system...');
                                        while loggedIn:
                                            try:
                                                if itera > int(settings['maxLogoutAttempts']):
                                                    Display.errorMsg("Logout attempt limit exceeded.");
                                                    loggedIn = False;
                                                    switch = False;
                                                    break;
                                                else:
                                                    response = None;
                                                    response = conn1.request();
                                                    
                                                    if response == "Goodbye":
                                                        loggedIn = False;
                                                        Display.playerMsg("Logged out successfully!");
                                                        switch = False;
                                                        break;
                                            except BadStatusLine: pass;
                                            except Exception:
                                                Display.errorMsg("Error. The system was not able to log you out at this time.");
                                                Display.errorMsg("Please try again next time.");
                                                switch = False;
                                                break;
                                            itera = itera + 1;

                                    # The user wishes to exit the program
                                    elif(i == 3): MAR_exit(0);

                                    # The user wishes to modify their player's power tree
                                    elif(i == 4):
                                        while(True):
                                            # List the powers that are available for modification and how much SP is currently associated with each one
                                            Display.gameMsg('\n  Listing Powers...');
                                            powStruct = deepcopy(powerStructure);
                                            del powStruct['help'];
                                            del powStruct['skip'];
                                            del powStruct['guess'];
                                            opt2 = [];

                                            for special in powStruct:
                                                special = special.title();
                                                Display.gameMsg(special, '('+str(userpowers[special]['sp']), 'sp allotted)');
                                                opt2.append(special);

                                            Display.gameMsg('-->', userdict['free_sp'],'special points (SP) free');
                                            if(int(userdict['free_sp']) > 0): setting = Display.menu(OrderedDict([('alter', 0), ('reload', -2), ('describe', -3), ('back', -1)]), initMsg='\n  Available Options:', prefix='');
                                            else: setting = Display.menu(OrderedDict([('reload', -2), ('describe', -3), ('back', -1)]), initMsg='\n  Available Options:', prefix='');
                                            
                                            if(setting == -1): break;
                                            elif(setting == -2):
                                                Display.sysMsg('Loading...');
                                                response = restruct();
                                                if(response != False): userdict, userpowers, powerStructure = response;
                                                else: Display.errorMsg("Connection to server was dropped. Please try again.");
                                            elif(setting == -3):
                                                response = Display.cooked_input('> Which special would you like described? ');
                                                if(response == 'back'): continue;
                                                elif(response.title() not in userpowers): Display.errorMsg('Invalid selection.');
                                                else: Display.gameMsg('\nDescription: '+userpowers[response.title()]['desc']);
                                            elif(int(userdict['free_sp']) > 0):
                                                data = Display.cooked_input('> Enter the name of the special you wish to alter: ');
                                                data = data.title();
                                                if(data not in opt2): Display.errorMsg('Invalid selection.');
                                                elif(userpowers[data]['json']['updateText'][:9] == 'WARNING: '): Display.errorMsg('That special is not upgradeable.');
                                                else:
                                                    Display.gameMsg('\nDescription: '+userpowers[data]['desc']+'\n');
                                                    Display.gameMsg('->', userpowers[data]['json']['updateText'], '\n');
                                                    data2 = int(Display.cooked_input('> Enter the amount of SP you wish to allocate or "0" to cancel: '));
                                                    if(0 < data2 <= int(userdict['free_sp'])):
                                                        Display.sysMsg('Updating server...');
                                                        conn1.params = {"u":u, "p":p, "python":1, "type":"spp", "SID":SID, 'target':data, 'modifier': data2};
                                                        response = conn1.request();
                                                        if(response == 'Valid'): Display.evnMsg('Action approved.');
                                                        else: Display.evnMsg('Action denied ('+response+')!');
                                                        Display.sysMsg('Refreshing...');
                                                        response = restruct();
                                                        if(response != False): userdict, userpowers, powerStructure = response;
                                                        else: Display.errorMsg("Connection to server was dropped. Please try again.");
                                                    elif(data2 == 0): Display.errorMsg('Canceling...');
                                                    else: Display.errorMsg('Invalid allocation amount.');
                                            else: Display.errorMsg('Invalid menu item.');
                                            
                                    # The user wishes to tinker with the game's internal settings
                                    elif(i == 5):
                                        while(True):
                                            Display.gameMsg('\n  Current Settings:');
                                            opt2 = [];
                                            
                                            # Structure the available options into a workable menu object
                                            for i, line in enumerate(settings.keys()):
                                                Display.gameMsg(str(i)+')', set_transform(line), 'is set to', settings[line]);
                                                opt2.append(line);
                                            
                                            setting = Display.menu(OrderedDict([('alter', 0), ('reload', -3), ('reset', -2), ('back', -1)]), initMsg='\n  Available Options:', prefix='');
                                            
                                            if(setting == -1): break;
                                            elif(setting == -2): MAR_load_settings(default_settings);
                                            elif(setting == -3): MAR_load_settings();
                                            else:
                                                data = int(Display.cooked_input('> Enter the # of the setting you wish to modify: '));
                                                if(data >= len(opt2)): Display.errorMsg('Invalid selection.');
                                                else:
                                                    data2 = val_setting(opt2[data], Display.cooked_input('> Enter the setting\'s new value: '));
                                                    if(data2 >= 0):
                                                        settings[opt2[data]] = data2;
                                                        MAR_load_settings(settings);
                            else: Display.errorMsg("Connection to server was dropped. Please try again.");
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
                    
                #We're attempting to register someone
                elif(i == 1):
                    # Display all the available class choices
                    Display.gameMsg('After all the classes are exposed below, you will be prompted to choose');
                    Display.gameMsg('your character\'s class (press enter to proceed):\n');
                    
                    Display.indent();
                    
                    Display.gameMsg(' -- Assassin -- ');
                    Display.gameMsg("Naturally awesome, the Assassin is the ultimate man-slayer.");
                    Display.gameMsg("Nothing is True; Everything is permitted. A creed.\n");
                    Display.gameMsg(" -- Quote: \"That's thirty minutes away. I'll be there in ten.\"");
                    Display.gameMsg(" -- Specialty: Turn Slayer");
                    
                    Display.pause();
                    
                    Display.gameMsg(Display.newline+' -- Doctor -- ');
                    Display.gameMsg("As the Doctor you'll hold the lives of thousands in your hands. If you");
                    Display.gameMsg("decide to cure or crush those lives, however, is up to you.\n");
                    Display.gameMsg(" -- Quote: \"ha... Maha... Muaha... Muahaha!... BWHAHAHAHAHHAHAA!\"");
                    Display.gameMsg(" -- Specialty: Turn Gainer");
                    
                    Display.pause();
                    
                    Display.gameMsg(Display.newline+' -- Priest -- ');
                    Display.gameMsg("The path of the righteous man is beset on all sides by the iniquities.");
                    Display.gameMsg("As a Priest, make your enemies pay for their sins.\n");
                    Display.gameMsg(" -- Quote: [Chasing guy down the street] \"You will pay for your sins!\"");
                    Display.gameMsg(" -- Specialty: Special Intervention");
                    
                    Display.pause();
                    
                    Display.gameMsg(Display.newline+' -- Courtesan -- ');
                    Display.gameMsg("Mysterious, secret, and rich.");
                    Display.gameMsg("The courtesan may just be the deadliest persona available.");
                    Display.gameMsg(" -- Quote: Any of you move and I'll execute every last onea ya!\n");
                    Display.gameMsg(" -- Specialty: Vertigo");
                    Display.gameMsg("NOTE: RECOMMENDED FOR EXPERIENCED PLAYERS ONLY!\n");

                    Display.pause();
                                    
                    Display.outdent();
                    user_class = Display.menu(OrderedDict([('assassin', 0), ('doctor', 1), ('priest', 2), ('courtesan', 3)]), initMsg='\n  Select Your Class:', prefix='-> ');

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
                        conn1.params["class"] = user_class;
                        conn1.params["type"] = "reg";

                        # Send the data off for processing
                        response = conn1.request();

                        # Alert the user of the result, and display the proper options accordingly
                        if response != False:
                            if response == "Approved":
                                Display.playerMsg("The username", u, "has been registered successfully!");
                                Display.playerMsg("You may now log in with the password you provided.");
                                Display.evnMsg('--> NOTE THAT NEW ACCOUNTS START WITH 50 Spending Points (SP)!');
                                
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

                # Go back a page
                elif(i == 2): break;

        # The user wishes to exit the program
        elif(i == 3): MAR_exit();

# Someone or something tried to interrupt the program!           
except (KeyboardInterrupt):
    if(settings['catchInterrupts']):
       choice = Display.cooked_input("\n> Are you sure you wish to exit MAR? (y/n) ");
       if(choice == 'y'): MAR_exit();
       else: pass;
    else: MAR_exit();
