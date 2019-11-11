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

def startup():
    hw.initMotionControl()
    hw.homingCycle()
    hw.initSensors()
    
def selectHolder():
    hw.selectSpecimenHolder()
    
def calibrateLoadCell(weights=1):
    hw.calibrateLoadCell(weights)
    
def calibrateHolder(numTimes=3):
    hw.calibrateHolder(numTimes)
    
def measure():
    hw.measurementCycle()
    
def homing():
    hw.homingCycle()
    
def shutdown():
    hw.closeSerial(hw.mcSerial)
    hw.closeSerial(hw.sensorSerial)
    os.system('sudo ./shutdown.sh')