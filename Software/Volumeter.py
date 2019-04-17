import serial
import pandas as pd
import numpy as np
import time

motionControlPort = '/dev/ttyUSB1'
sensorPort = '/dev/ttyUSB0'
loadCellConstants = None
mcSerial = None
sensorSerial = None

class Volumeter:
    def initSensors(self):
        print("initSensors()")
        self.loadCellConstants = self.readLoadCellCalibration()

        print(sensorPort)
        #sensorSerial = serial.Serial(port=sensorPort, baudrate=115200)

    def temp(self):
        print(self.loadCellConstants)
    
    def readLoadCellCalibration(self):
        cal = np.genfromtxt('loadCellCalibration.csv', delimiter=',')
        return cal

    def __init__(self):
        print(motionControlPort)
        self.initSensors()

