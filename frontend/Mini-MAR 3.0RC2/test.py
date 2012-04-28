data = {'effects':[('modTurnCnt', 4, (1,15,10))], 'type': 2, 'chance':(0.95, (0.01,5,1.0)), 'cooldown':(4, (-1,5,0))};
msg = 'Statistics: ';

# Compute the magnitude of each special based on updates
for i, stat in enumerate(data['effects']):
    fx, mag, upgrade = stat;
    if(upgrade != False):
        x, y, z = upgrade;
        z = float(z);
        w = floor(float(special['sp'])/float(y))*float(x)+float(mag);
        if((z <= 0.0 and w < fabs(z)) or (z > 0.0 and w > z)): w = fabs(z);
        uPow[i]['json']['effects'][j] = (fx, w, True);
        mag = w;
        
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
    uPow[i]['json']['chance'] = (w, True);
    mag = w;
    
digits.append(int(round(float(mag)*100)));

# Compute the magnitude of each "cooldown" based on updates
mag, upgrade = uPow[i]['json']['cooldown'];
if(str(mag).find('#')+1):
    mag = int(round(eval(str(mag).replace('#', str(digits[0])))));
    uPow[i]['json']['cooldown'] = (mag, False);
elif(upgrade != False):
    x, y, z = upgrade;
    z = float(z);
    w = int(round(floor(float(special['sp'])/float(y))*float(x)+float(mag)));
    if((z <= 0.0 and w < fabs(z)) or (z > 0.0 and w > z)): w = int(round(fabs(z)));
    uPow[i]['json']['cooldown'] = (w, True);
    mag = w;
