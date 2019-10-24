'''Hardware module'''

import serial
import pandas as pd
import numpy as np
import time
import os
from math import ceil
from matplotlib import pyplot as plt
from IPython.core.display import clear_output
from datetime import datetime
import DataProcessing as dp

global loadCellConstants
global mcSerial
global sensorSerial
global homingDone

def readLoadCellCalibration():
    '''Loads the load cell calibration values from a CSV file called loadCellCalibration.csv.'''
    cal = np.genfromtxt('loadCellCalibration.csv', delimiter=',')
    return cal

def initMotionControl(motionControlPort='/dev/ttyUSB1'):
    '''Initializes the motion control serial port.
    
    Uses a default of /dev/ttyUSB1 but the port can be given as an argument.
    '''
    global mcSerial
    global homingDone
    mcSerial = serial.Serial(port=motionControlPort, baudrate=115200)
    homingDone = False

def initSensors(sensorPort='/dev/ttyUSB0'):
    '''Initializes the sensor serial port.
    
    Uses a default of /dev/ttyUSB0 but the port can be given as an argument.
    '''
    global sensorSerial
    global loadCellConstants
    loadCellConstants = readLoadCellCalibration()
    
    sensorSerial = serial.Serial(port=sensorPort, baudrate=115200)

def closeSerial(serial):
    '''Closes the serial port that was given as an argument'''
    serial.close()

def sendMotionCommand(cmd):
    '''Sends the given gcode command to the motion control serial port.'''
    mcSerial.write('{0}\n'.format(cmd).encode('utf-8'))
    mcSerial.flushInput()
    grbl_out = mcSerial.readline()
    return grbl_out.decode()

def motionFinished(wait=False):
    '''Returns True if the motion control system is idle
    
    Giving wait=True as an argument waits until the motion control system becomes idle and returns True.
    '''
    finished = False
    if(wait):
        while(not finished):
            time.sleep(0.5)
            grbl_out = sendMotionCommand('?')
            finished = 'Idle' in str(grbl_out)
        return True
    else:
        grbl_out = sendMotionCommand(serial, '?')
        return 'Idle' in str(grbl_out)

def homingCycle():
    '''Homes the motion control system axes.'''
    
    global homingDone
    
    cycle = ['?', 'G91', 'G38.2Z2500F2000', 'G1Z-20F1000',
             'G38.2X-560Z-560F600', 'G1X10Z10F600', 'G10L20P1X0Y0Z0',
            'G90', 'G1Z-1650F3000']
    for c in cycle:
        sendMotionCommand(c)
    motionFinished(wait=True)
    homingDone = True

def startup():
    '''Initializes motion control and sensors, runs the homing cycle.'''
    initMotionControl()
    initSensor()
    homingCycle()

def recordSensors(numSamples):
    '''Records the sensors for the given number of samples and return the in a pandas DataFrame.'''
    
    # TODO make the smoothing better, maybe use the smooth function from Data_sync_test
    
    sensorSerial.reset_input_buffer()
    samplesRead = 0
    df = pd.DataFrame(columns=['time', 'loadCell', 'level'], dtype='float')
    while(samplesRead < numSamples):
        try:
            data = np.array(sensorSerial.readline().decode().rstrip().split(','))
            data = data.astype(np.float)
            df.loc[len(df)] = data
            samplesRead += 1
        except:
            pass
        
    return df

def meanLoadCell(numSamples):
    '''Returns the mean load cell value of given number of samples'''
    data = recordSensors(numSamples)
    return data['loadCell'].mean()

def meanWeight(numSamples):
    '''Returns the mean weight in grams of given number of samples'''
    data = recordSensors(numSamples)
    mean = data['loadCell'].mean()
    return loadCellToGrams(mean)

def measurementCycle():
    '''Runs the measurement cycle.'''
    # TODO make a function that is called from calibrateHolder() and measurementCycle(). Put this in the HW module
    
    loweringSpeed = 2000 # mm/min
    topHeigth = 400
    bottomHeigth = -850
    smoothing = 10
    
    if(not homingDone):
        print("Motion control system is not homed. Please run the homingCycle() first.")
        return None
    
    #Record the mean weight of the specimen
    mw = meanWeight(200)
    print('Specimen weight: {:.2f}'.format(mw))
    
    movementsToTopOfTank = ['?', 'G90', 'G1X0Z-1640F6000','G1X0Z-50F4000', 'G1X540Z540F3000','G1X540Z{}F2000'.format(topHeigth)]
    for c in movementsToTopOfTank:
        sendMotionCommand(c)
    motionFinished(wait=True)
    
    # Wait for the movement to stabilize
    time.sleep(5)
    sendMotionCommand('G1X540Z{}F2000'.format(bottomHeigth))
    time.sleep((loweringSpeed/60)/20) # 20mm/s^2 acceleration, start recording data after the acceleration
    data = recordSensors(86*((topHeigth-bottomHeigth)/(loweringSpeed/60) + 2))
    motionFinished(wait=True)
    time.sleep(1)
    sendMotionCommand('G1X540Z{0}F2000'.format(topHeigth))
    
    try:
        df = pd.DataFrame(columns=['depth', 'force'], dtype='float')
        df['depth'] = ((data['time']-data['time'].iloc[int(smoothing/2)])*loweringSpeed/60)/1000.0 + data['level'] - data['level'].iloc[int(smoothing/2)]
        df['force'] = data['loadCell'].apply(loadCellToGrams)
        # To make displacement positive, multiply force by -1.0
        df['force'] *= -1.0
        df['force'] = df['force'].rolling(10, center=True).median()
        df = df.dropna()
        df = df.set_index(['depth'])
        df = resampleDF(df)
        #df['force'] -= mw
        print(df.head(30))
    except:
        print('Data processing failed')
    
    for c in reversed(movementsToTopOfTank):
        sendMotionCommand(c)
    motionFinished(wait=True)  
    
    df.to_pickle('{}_testMeasurement-{}'.format(datetime.now(), mw))
    
    holderData = pd.read_pickle('specimenHolder')
    diff = dp.synchronizeMeasurement(df, holderData)
    diff.index.name = 'Depth'
    #diff.dropna(axis='columns')
    diff.to_csv('{}_testMeasurementDiff-{}.csv'.format(datetime.now(), mw), sep = ';', decimal=",")
    #diff = df.iloc[:,0]-holderData.iloc[:,0]
    smoothDiff = dp.smooth(diff, 55)
    fig=plt.figure()
    plt.plot(diff)
    #plt.plot(smoothDiff)
    #plt.plot(holderData)
    #plt.plot(df)
    plt.show()