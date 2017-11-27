from psychopy import gui, core, data
import numpy, random, os, serial, pygame
from math import *
from tap_arduino import *

fingerName = ['thumb','index','middle','ring','pinky']

# -- get input from experimenter --
exptInfo = {'01. Participant Code':'000',
            '02. Test number (0 for practice)':1,
            '03. Dominant hand':'right',
            '04. Hand pose':'hands square',
            '05. No. trials per finger':5,
            '06. Right fingers to use (1 thumb - 5 pinky)':'1,2,3,4,5',
            '07. Left fingers to use (1 thumb - 5 pinky)':'',
            '08. Provide feedback':True,
            '09. Folder for saving data':'TAP-data',
            '10. Motor activation duration (ms)':100,
            '11. Motor intensity (0 - 255)':255,
            '12. Accelerometer range (2,4,8,16G)':16,
            '12. Tap threshold (0 - 255)':100,
            '13. Max tap duration (0 - 159 ms)':150,
            '14. Right arduino serial port':'COM3',
            '15. Left arduino serial port':'COM5',
            '16. Serial baud rate':9600,
            '17. Serial timeout (sec)':0.05,
            '18. Print arduino messages':False}
exptInfo['19. Date and time']= data.getDateStr(format='%Y-%m-%d_%H-%M-%S') ##add the current time

dlg = gui.DlgFromDict(exptInfo, title='Experiment details', 
                    fixed=['19. Date and time'])
if dlg.OK:
    pass
else:
    core.quit() ## the user hit cancel so exit

try:
    rightToUse = [int(i) for i in exptInfo['06. Right fingers to use (1 thumb - 5 pinky)'].split(',')]
except:
    rightToUse = []
try:
    leftToUse = [int(i) for i in exptInfo['07. Left fingers to use (1 thumb - 5 pinky)'].split(',')]
except:
    leftToUse = []

handsToUse = []
arduinoPort = {}
if len(rightToUse) > 0: 
    handsToUse.append('right')
    arduinoPort['right'] = exptInfo['14. Right arduino serial port']
if len(leftToUse) > 0: 
    handsToUse.append('left')
    arduinoPort['left'] = exptInfo['15. Left arduino serial port']
if len(handsToUse) == 0:
    core.quit('You must use at least one motor')
# ----

# -- make folder/files to save data --
if exptInfo['02. Test number (0 for practice)'] > 0:
    dataFolder = './'+exptInfo['09. Folder for saving data']+'/'
    if not os.path.exists(dataFolder):
        os.makedirs(dataFolder)
    fileName = dataFolder + exptInfo['19. Date and time']+'_'+ exptInfo['01. Participant Code']
    infoFile = open(fileName+'_info.csv', 'w') 
    for k,v in exptInfo.iteritems(): infoFile.write(k + ',' + str(v) + '\n')
    infoFile.close()
    accelDataFile = open(fileName+'_accleerometer-data.csv', 'w')
    trialDataFile = open(fileName+'_trial-data.csv', 'w')
    accelDataFile.write('trialNumber,time,x,y,z\n')
    trialDataFile.write('trialNumber,cued-hand,cued-finger,correct,tap-1-ms,tap-1-finger,tap-2-ms,tap-2-finger,tap-3-ms,tap-3-finger\n')
# ----

# -- setup experiment randomisation --
stimList = []
for finger in rightToUse:
    stimList.append({'hand':'right','finger':finger})
for finger in leftToUse:
    stimList.append({'hand':'left','finger':finger})
trials = data.TrialHandler(stimList,exptInfo['05. No. trials per finger'])
trials.data.addDataType('correct')
# ----

# -- setup feedback --
if exptInfo['08. Provide feedback']:
    #pygame.mixer.pre_init() 
    #pygame.mixer.init()
    #sounds = [pygame.mixer.Sound('incorrect.wav'),pygame.mixer.Sound('correct.wav')]
    feedbackText = ['INCORRECT','CORRECT']
# ----

# -- make serial connection to arduino --
arduino = {}
for h in handsToUse:
    arduino[h] = serial.Serial(arduinoPort[h], 
                    exptInfo['16. Serial baud rate'],
                    timeout=exptInfo['17. Serial timeout (sec)'])
    print(h+' ')
    ping(arduino[h],exptInfo['18. Print arduino messages'])
# --

# -- motor settings --
for h in handsToUse:
    motor_duration(arduino[h], exptInfo['10. Motor activation duration (ms)'],
                    exptInfo['18. Print arduino messages'])
    motor_intensity(arduino[h], exptInfo['11. Motor intensity (0 - 255)'],
                    exptInfo['18. Print arduino messages'])
#--

# -- accelerometer settings --
for h in handsToUse:
    accel_range(arduino[h], exptInfo['12. Accelerometer range (2,4,8,16G)'],
                    exptInfo['18. Print arduino messages'])
    accel_threshold(arduino[h], exptInfo['12. Tap threshold (0 - 255)'],
                    exptInfo['18. Print arduino messages'])
    accel_duration(arduino[h], exptInfo['13. Max tap duration (0 - 159 ms)'],
                    exptInfo['18. Print arduino messages'])

# -- setup accelerometers --
for finger in leftToUse:
    setup_accel(arduino['left'], finger, exptInfo['18. Print arduino messages'])
for finger in rightToUse:
    setup_accel(arduino['right'], finger, exptInfo['18. Print arduino messages'])
# --


# -- run the experiment --
correctCount = 0
trialNum = 0
for thisTrial in trials:
    print('\nTap cued on {} {}' .format(
                    thisTrial['hand'], 
                    fingerName[thisTrial['finger']]))
    
    ## cue for a tap 
    tapResults = tap(arduino[thisTrial['hand']], 
                    thisTrial['finger'], 
                    exptInfo['18. Print arduino messages'])
    correct = int(fingerName[thisTrial['finger']] == tapResults['firstThreeTapFingers'][0])
    trials.data.add('correct',correct)
    
    ## provide feedback
    if exptInfo['08. Provide feedback']:
        #feedbackSound = sounds[correct]
        #ch = feedbackSound.play()
        print(feedbackText[correct])
        print('Participant tapped {} finger.' .format(tapResults['firstThreeTapFingers'][0]))
        #while ch.get_busy():
        #    pass
        print('Reaction time {} ms' .format(tapResults['firstThreeTapTimes'][0]))
        
    ## record the data if not practice 
    if exptInfo['02. Test number (0 for practice)'] > 0:
        thisAccel = tapResults['accelData'].transpose()
        for row in range(len(thisAccel)):
            accelDataFile.write('{},{},{},{},{}\n' .format(
                                trialNum+1,
                                thisAccel[row][0],
                                thisAccel[row][1],
                                thisAccel[row][2],
                                thisAccel[row][3]))
        trialDataFile.write('{},{},{},{},{},{},{},{},{},{}\n' .format(
                                trialNum+1,
                                thisTrial['hand'], 
                                fingerName[thisTrial['finger']],
                                correct,
                                tapResults['firstThreeTapTimes'][0],
                                tapResults['firstThreeTapFingers'][0],
                                tapResults['firstThreeTapTimes'][1],
                                tapResults['firstThreeTapFingers'][1],
                                tapResults['firstThreeTapTimes'][2],
                                tapResults['firstThreeTapFingers'][2]))
    
    
    trialNum += 1
    print('{} of {} trials complete\n' .format(trialNum, trials.nTotal))

print('\n=== EXPERIMENT FINISHED ===\n')

## save data to file
if exptInfo['02. Test number (0 for practice)'] > 0:
    accelDataFile.close()
    trialDataFile.close()
    print('Data saved {}\n\n' .format(fileName))
else:
    print('Practice only, no data saved.')
