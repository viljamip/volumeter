import serial
import pandas as pd
import numpy as np
import time
import os
from math import ceil
from matplotlib import pyplot as plt
from IPython.core.display import clear_output
import import_ipynb
from datetime import datetime
import backend.DataProcessing as dp
import backend.Hardware as hw
import backend.UI as ui

def startup(noHoming=False):
    if(noHoming):
        hw.initMotionControl()
        hw.homingDone = True
        hw.initSensors()
    else:
        hw.initMotionControl()
        hw.homingCycle()
        hw.initSensors()
    
def selectHolder():
    hw.selectSpecimenHolder()
    
def calibrateLoadCell(weights):
    #weights = input('How many weights? (default 3): ')
    try:
        weights = int(weights)
    except:
        print('Using 3 weights')
        weights = 3
    hw.calibrateLoadCell(weights)
    
def calibrateHolder(numAverages):
    '''
    numTimes = input('How many averages? (default 3): ')
    try:
        numTimes = int(numTimes)
    except:
        numTimes = 3
    '''
    hw.calibrateHolder(numAverages)
    
def measure():
    hw.measurementCycle()
    '''
    try:
        hw.measurementCycle()
    except NameError:
        print('Run Startup first')
    '''
    
def homing():
    hw.homingCycle()
    
def reset():
    hw.resetMotionController()
    
def shutdown():
    print('Shutdown')
    try:
        hw.closeSerial(hw.mcSerial)
        hw.closeSerial(hw.sensorSerial)
    except:
        pass
    os.seteuid(1000)
    os.system('sudo sh /home/pi/Desktop/dimensiometer/Software/backend/shutdown.sh')
    
def start():
        ui.runUI()