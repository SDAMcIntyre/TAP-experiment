import serial
import matplotlib.pyplot as plt
import numpy as np
from psychopy import core, data

def tap(arduino, finger, printMessages):
    '''
    arduino: existing serial port connection to arduino
    finger: which finger to test (1-5)
    printMessages: do you want to print messages from the arduino?
    
    '''
    
    fingerName = ['thumb','index','middle','ring','pinky']
    
    # -- prompt for a tap
    arduinoSays = ''
    while not arduinoSays == 'tap':
        arduino.write('tap')
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
    fingerSent = False
    while not fingerSent:
        arduino.write(str(finger))
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
        if int(arduinoSays) == finger: fingerSent = True
    # ----
    
    # -- get data from arduino
    sampleData = []
    while not arduinoSays == "waiting for tap":
        arduinoSays = arduino.readline().strip(); 
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
    gotSampleData = False
    while not arduinoSays == 'sampling finished':
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
        if arduinoSays == 'sampling finished':
            gotSampleData = True
        elif len(arduinoSays)>0:
            sampleData += [arduinoSays]
    
    while not arduinoSays == 'start time':
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
    gotStartTime = False
    while not gotStartTime:
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
        if len(arduinoSays)>0:
            gotStartTime = True
            startTime = int(arduinoSays)
    
    tapTimes = []
    while not arduinoSays == 'tap times':
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
    gotTapTimes = False
    while not gotTapTimes:
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
        if arduinoSays == 'end of data':
            gotTapTimes = True
        elif len(arduinoSays)>0:
            tapTimes += [arduinoSays]
    # ----
    
    allData = process_tap_data(startTime,sampleData,tapTimes, False, '')
    
    allData['promptedFinger'] = fingerName[finger]
    return allData

def process_tap_data(startTime,sampleData,tapTimes,plotData,savePlotName):
    fingerName = ['thumb','index','middle','ring','pinky']
    startTime = int(startTime)/1000.0
    accelData = []
    for sample in range(len(sampleData)):
        accelData += [[int(i) for i in sampleData[sample].split(',')]]
        accelData[sample][0] = round(accelData[sample][0]/1000.0 - startTime, 3)
    accelData = np.array(accelData)
    accelData = accelData.transpose()
    
    tapData = {}
    for f in fingerName:
        tapData[f] = []
    for sample in range(len(tapTimes)):
        thisTap = [i for i in tapTimes[sample].split(',')]
        tapData[thisTap[0]] += [round(float(thisTap[1])/1000.0 - startTime, 3)]
    allTapTimes = []
    for f in fingerName:
        allTapTimes += tapData[f]
    orderedTapTimes = sorted(allTapTimes)
    orderedTapFingers = []
    for n in range(len(orderedTapTimes)):
        for f in fingerName:
            if orderedTapTimes[n] in tapData[f]: 
                orderedTapFingers+= [f]
    for n in range(3):
        if len(orderedTapTimes) == n:
            orderedTapTimes += ['NA']
            orderedTapFingers += ['NA']

    if plotData:
        fig = plt.figure()
        fig, ax = plt.subplots(1,1)
        plt.plot(accelData[0], accelData[1], label='x-axis')
        plt.plot(accelData[0], accelData[2], label='y-axis')
        plt.plot(accelData[0], accelData[3], label='z-axis')
        for f in fingerName:
            if len(tapData[f]) > 0:
                y = np.zeros([len(tapData[f])])
                plt.plot(tapData[f], y, label=f, marker = '|', markersize=100, linestyle='None')
        plt.xlabel('time (ms)')
        plt.ylabel('accelerometer output')
        plt.legend()
        plt.show()
        if len(savePlotName) > 0:
            plt.savefig('./'+savePlotName+'.pdf')
    
    processedData = {'dateTime' : data.getDateStr(format='%Y-%m-%d_%H-%M-%S'),
                        'accelData': accelData,
                        'tapData': tapData, 
                        'firstThreeTapTimes': orderedTapTimes[0:3],
                        'firstThreeTapFingers' : orderedTapFingers[0:3]}
    return processedData

def ping(arduino, printMessages):
    arduinoSays = ''
    while not arduinoSays == 'ack':
        arduino.write('ping')
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
    return arduinoSays

def sampling_time(arduino, samplingTime, printMessages):
    arduinoSays = ''
    while not arduinoSays == 'samplingTime':
        arduino.write('samplingTime')
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
    samplingTimeSent = False
    while not samplingTimeSent:
        arduino.write(str(int(samplingTime)))
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
        if int(arduinoSays) == int(samplingTime): samplingTimeSent = True
    return arduinoSays

def tap_debounce(arduino, tapDebounce, printMessages):
    arduinoSays = ''
    while not arduinoSays == 'tapDebounce':
        arduino.write('tapDebounce')
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
    tapDebounceSent = False
    while not tapDebounceSent:
        arduino.write(str(int(tapDebounce)))
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
        if int(arduinoSays) == int(tapDebounce): tapDebounceSent = True
    return arduinoSays

def motor_duration(arduino, duration, printMessages):
    arduinoSays = ''
    while not arduinoSays == 'motorduration':
        arduino.write('motorduration')
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
    durationSent = False
    while not durationSent:
        arduino.write(str(int(duration)))
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
        if int(arduinoSays) == int(duration): durationSent = True
    return arduinoSays

def motor_intensity(arduino, intensity, printMessages):
    minintensity = 0
    maxintensity = 255
    if intensity > maxintensity:
        warning('max intensity is {}' .format(maxintensity))
        intensity = 255
    elif intensity <= minintensity:
        warning('setting motor to {} means it will not activate' .format(minintensity))
        intensity = 0
    arduinoSays = ''
    while not arduinoSays == 'intensity':
        arduino.write('intensity')
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
    intensitySent = False
    while not intensitySent:
        arduino.write(str(int(intensity)))
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
        if int(arduinoSays) == int(intensity): intensitySent = True
    return arduinoSays

def accel_range(arduino, range, printMessages):
    defaultRange = 16
    if range not in [2,4,8,16]:
        warning('{} not a valid accelerometer range. Set to default ({}G)' .format(range,defaultRange))
        range = 16
    arduinoSays = ''
    while not arduinoSays == 'range':
        arduino.write('range')
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
    rangeSent = False
    while not rangeSent:
        arduino.write(str(range))
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
        if int(arduinoSays) == range: rangeSent = True
    return arduinoSays

def accel_threshold(arduino, threshold, printMessages):
    threshold = ms_to_increment(threshold)
    arduinoSays = ''
    while not arduinoSays == 'threshold':
        arduino.write('threshold')
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
    thresholdSent = False
    while not thresholdSent:
        arduino.write(str(threshold))
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
        if int(arduinoSays) == threshold: thresholdSent = True
    return arduinoSays

def accel_duration(arduino, duration, printMessages):
    arduinoSays = ''
    while not arduinoSays == 'threshduration':
        arduino.write('threshduration')
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
    durationSent = False
    while not durationSent:
        arduino.write(str(int(duration)))
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
        if int(arduinoSays) == int(duration): durationSent = True
    return arduinoSays

def ms_to_increment(ms):
    maxms = 159.375
    minms = 0
    scale = 0.625
    if ms > maxms:
        warning('max is {} ms' .format(maxms))
        return 255
    elif ms < 0:
        warning('min is {} ms but you should probably use a higher number' .format(minms))
        return 0
    else:
        return int(round(ms/scale))

def setup_accel(arduino, finger, printMessages):
    arduinoSays = ''
    while not arduinoSays == 'setup':
        arduino.write('setup')
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
    fingerSent = False
    while not fingerSent:
        arduino.write(str(finger))
        arduinoSays = arduino.readline().strip()
        if printMessages and len(arduinoSays)> 0: print('arduino: {}' .format(arduinoSays))
        if int(arduinoSays) == finger: fingerSent = True
    return arduinoSays

if __name__ == "__main__":
    arduino = serial.Serial('COM3', 9600, timeout=0.05); core.wait(2)
    finger = 2
    
    ping(arduino, True)
    setup_accel(arduino, finger, True)
    tapResults = tap(arduino, finger, False)
    print tapResults