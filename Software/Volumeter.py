import serial
import pandas as pd
import numpy as np
import time

loadCellConstants = None
mcSerial = None
sensorSerial = None

def initSensors(sensorPort):
    print("initSensors()")
    loadCellConstants = readLoadCellCalibration()

    print(sensorPort)
    #sensorSerial = serial.Serial(port=sensorPort, baudrate=115200)

def temp():
    print(loadCellConstants)

def readLoadCellCalibration():
    cal = np.genfromtxt('loadCellCalibration.csv', delimiter=',')
    return cal

