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
import backend.UI as ui
import glob
import json
import ipywidgets as widgets
from IPython.display import display

global loadCellConstants
global mcSerial
global sensorSerial
global homingDone
global selectedHolderName
global selectedHolder
global holderSelector
global holders
global holderData
global holderLabel
global measurementNamePrefix

print('Test')
holderData = None
selectedHolder = None
measurementNamePrefix = 'default'
base_dir = '/sys/bus/w1/devices/'

try:
    print('Test2')
    device_folder = glob.glob(base_dir + '28*')[0]
    device_file = device_folder + '/w1_slave'
except:
    device_file = None
  
def read_temp_raw():
    print('Test3')
    if device_file is None:
        return None
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines
                   
def read_temp():
    lines = read_temp_raw()
    if lines is None:
        print('Temperature sensor is not working. Using default 20°C.')
        return 20
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

def saveHolder(weight, data):
    name = input('Name: ')
    description = input('Description: ')
    
    outdata = {}
    timestamp = time.time()
    outdata['name'] = '{}_{}'.format(name, datetime.fromtimestamp(timestamp).isoformat())
    outdata['edit_time'] = timestamp
    outdata['description'] = description
    outdata['weight'] = weight
    outdata['cal'] = data.to_json()
    
    if not os.path.isdir('holders/'):
        os.mkdir('/holders')
    
    with open('holders/{}_{}.json'.format(name, datetime.fromtimestamp(timestamp).isoformat()), 'w', encoding='utf-8') as outfile:
        json.dump(outdata, outfile)

def loadHolders():
    global holders
    
    holders = []
    holderFiles = glob.glob('holders/*.json')
    
    for holderFile in holderFiles:
        with open(holderFile, encoding='utf-8') as json_file:
            holder = json.load(json_file)
            holders.append(holder)

    firstHolder = True
    for holder in holders:
        calData = pd.read_json(holder['cal'], convert_axes=False)
        calData.index = calData.index.astype(float)
        calData[calData.columns] = calData[calData.columns].astype(float)
        calData = calData.sort_index()
        holder['cal'] = calData

        if(firstHolder):
            firstHolder = False
            holdersDF = pd.DataFrame(holder['cal'])
            holdersDF.rename(columns={holdersDF.columns[0] : holder['name']}, inplace = True)
        else:
            holdersDF[holder['name']] = holder['cal']
        
    return holders, holdersDF

# UI
def selectSpecimenHolder():
    global holderSelector
    global holders
    global selectedHolder
    global holderLabel
    
    clear_output()
    
    holders, df = loadHolders()
    selectedHolder = holders[0]
    
    holderSelector = widgets.Select(
    options=df.columns,
    value=df.columns[0],
    description='Holder: ',
    disabled=False,
    layout = widgets.Layout(height='100px')
    )
    
    holderLabel = widgets.Label(value=selectedHolder['description'])
    
    selButton = widgets.Button(
    description='Select',
    disabled=False,
    button_style='', # 'success', 'info', 'warning', 'danger' or ''
    tooltip='Apply the specimen holder selection',
    icon='check'
    )
    
    delButton = widgets.Button(
    description='Delete',
    disabled=False,
    button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
    tooltip='Delete the selected holder',
    #icon='check'
    )
    
    buttons = widgets.HBox([selButton, delButton])
    widgets.interact(plotSpecimenHolder, df=widgets.fixed(df), column=holderSelector)
    display(holderLabel)
    display(buttons)
    selButton.on_click(applyHolderSelection)
    delButton.on_click(deleteHolder)
    
def plotSpecimenHolder(df, column):
    global holderLabel
    global selectedHolderName
    fig=plt.figure(column, figsize=(4,3), dpi=80)
    plt.plot(df[column])
    plt.show()
    selectedHolderName = column
    
    for holder in holders:
        if(holder['name'] == selectedHolderName):
            holderLabel.value = holder['description']

def applyHolderSelection(b):
    global holderData
    global holders
    global selectedHolderName
    global selectedHolder
    
    clear_output()
    print('Selected holder: {}'.format(selectedHolderName))
    ui.start()
    
    for holder in holders:
        if(holder['name'] == selectedHolderName):
            holderData = holder['cal']
            selectedHolder = holder
    
def deleteHolder(b):
    global holders
    holderFiles = glob.glob('holders/*.json')
    for file in holderFiles:
        if selectedHolderName in file:
            os.remove(file)
    holders, holdersDF = loadHolders()
    holderSelector.options = holdersDF
    
def calibrateLoadCell(numWeights=1):
    # TODO Interpolate depth data to 0,5mm resolution for example
    '''Runs a load cell calibration wizard.
    
    numWeights argument can be used to tell how many calibration weights you want to use.
    The calibration values are saved to loadCellCalibration.csv if the user accepts the new calibration values.
    '''
    sendMotionCommand('G1Z-1620F1000')
    motionFinished(True)
    
    grams = []
    values = []
    print("Load Cell Calibration")
    print("Leave the specimen holder empty")
    input("Hit enter when the specimen holder is stationary")
    print("Wait for 5 seconds...")
    grams.append(0.0)
    values.append(meanLoadCell(80*5))
    while(numWeights > 0):
        numWeights -= 1
        while(True):
            try:
                calWeight = input("Mass of the calibration weight in kg: ").rstrip().replace(',', '.')
                grams.append(float(calWeight)*1000.0)
                break
            except:
                print("Insuitable mass value")

        print("Add the calibratrion weight to the specimen holder")
        input("Hit enter when the specimen holder is stationary")
        print("Wait for 5 seconds...")
        values.append(meanLoadCell(80*5))
    calibrationConstants = np.polyfit(values, grams, 1)
    calibrationConstants[1] = 0.0
    print("Calibration: y = {:.2f}x+{:.2f}".format(calibrationConstants[0], calibrationConstants[1]))
    save = input("Save calibration (y/n)")
    if('y' in save.lower()):
        np.savetxt('holders/loadCellCalibration.csv', calibrationConstants, delimiter=',')
        clear_output()
        print('Calibration saved')
    else:
        print('Calibration cancelled')

def readLoadCellCalibration():
    '''Loads the load cell calibration values from a CSV file called loadCellCalibration.csv.'''
    cal = np.genfromtxt('holders/loadCellCalibration.csv', delimiter=',')
    return cal

def loadCellToRelativeGrams(value):
    '''Converts a load cell reading to grams based on the calibration values.'''
    return value*loadCellConstants[0] + loadCellConstants[1]

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
    sensorSerial = serial.Serial(port=sensorPort, baudrate=115200)
    
    try:
        loadCellConstants = readLoadCellCalibration()
    except:
        print('Load cell calibration not found. Please recalibrate.')
    

def closeSerial(serial):
    '''Closes the serial port that was given as an argument'''
    serial.close()

def sendMotionCommand(cmd):
    '''Sends the given gcode command to the motion control serial port.'''
    mcSerial.write('{0}\n'.format(cmd).encode('utf-8'))
    mcSerial.flushInput()
    grbl_out = mcSerial.readline()
    return grbl_out.decode()

def resetMotionController():
    try:
        closeSerial(mcSerial)
        closeSerial(sensorSerial)
    except:
        pass
    initMotionControl()
    initSensors()
    mcSerial.write(b'\x18')
    time.sleep(2)
    sendMotionCommand('$X')
    sendMotionCommand('G91')
    sendMotionCommand('G1Z-40F1000')
    sendMotionCommand('G1X20F1000')
    sendMotionCommand('G90')
    motionFinished(True)
    startup()
    print('Reset done')

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
             'G38.2X-580Z-580F600', 'G1X10Z10F600', 'G10L20P1X0Y0Z0',
            'G90', 'G1Z-1640F3000']
    for c in cycle:
        sendMotionCommand(c)
    motionFinished(wait=True)
    homingDone = True

def startup():
    '''Initializes motion control and sensors, runs the homing cycle.'''
    print('Startup painettu')
    initMotionControl()
    initSensors()
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
    return loadCellToRelativeGrams(mean)

def calibrateHolder(numTimes=3):
    '''Runs a specimen holder calibration cycle and asks the user for a name of the calibration.

    Calibration values are saved to holderCalibrations.csv file whose column specifies the name of the holder.
    '''
    
    loweringSpeed = 2000 # mm/min
    topHeigth = 400
    bottomHeigth = -850
    smoothing = 10
    
    if(not homingDone):
        print("Motion control system is not homed. Please run the homingCycle() first.")
        return None

    motionFinished(wait=True)

    # Move on top of the water tank
    movementsToTopOfTank = ['?', 'G90', 'G1X0Z-1640F6000','G1X0Z-50F4000', 'G1X540Z540F3000','G1X540Z{}F2000'.format(topHeigth)]
    for c in movementsToTopOfTank:
        sendMotionCommand(c)
    motionFinished(wait=True)
    
    weight = meanWeight(5 * 80)
    #print('Weight: {}'.format(weight))
    
    temperature = read_temp()
    
    # Dip the holder to the water to make it wet
    sendMotionCommand('G1X540Z{}F2000'.format(bottomHeigth))
    sendMotionCommand('G1X540Z{0}F2000'.format(topHeigth))
    motionFinished(wait=True)
    
    cal = pd.DataFrame(columns=['depth', 'force'], dtype='float')
    
    firstMeasurement = True
    while(numTimes > 0):
        numTimes -= 1
        # Wait for the movement to stabilize
        time.sleep(5)
        sendMotionCommand('G1X540Z{}F2000'.format(bottomHeigth))
        time.sleep((loweringSpeed/60)/20) # 20mm/s^2 acceleration, start recording data after the acceleration
        data = recordSensors(86*((topHeigth-bottomHeigth)/(loweringSpeed/60) + 2))
        motionFinished(wait=True)
        time.sleep(1)
        sendMotionCommand('G1X540Z{0}F2000'.format(topHeigth))
        
        df = pd.DataFrame(columns=['depth', 'force'], dtype='float')
        # TODO This should be its own function?
        df['depth'] = ((data['time']-data['time'].iloc[int(smoothing/2)])*loweringSpeed/60)/1000.0 + data['level'] - data['level'].iloc[int(smoothing/2)]
        df['force'] = data['loadCell'].apply(loadCellToRelativeGrams)
        # To make displacement positive, multiply force by -1.0
        df['force'] *= -1.0
        df['force'] = df['force'].rolling(10, center=True).median()
        df = df.dropna()
        df = df.set_index(['depth'])
        df = dp.resampleDF(df)
        df['force'] = df['force'].apply(dp.forceToVolume, tempC=temperature)
        
        if(firstMeasurement):
            cal = df.copy()
        else:
            cal = pd.DataFrame(pd.concat((cal, df), axis=1).mean(axis=1), columns=['holder'])
        
        motionFinished(wait=True)
        firstMeasurement = False
    
    for c in reversed(movementsToTopOfTank):
        sendMotionCommand(c)
    motionFinished(wait=True)  
    
    saveHolder(weight, cal)

def measurementCycle():
    '''Runs the measurement cycle.'''
    # TODO make a function that is called from calibrateHolder() and measurementCycle(). Put this in the HW module
    
    global holderData
    global selectedHolder
    global measurementNamePrefix
    
    loweringSpeed = 2000 # mm/min
    topHeigth = 400
    bottomHeigth = -850
    smoothing = 10
    
    if(not homingDone):
        print("Motion control system is not homed. Please run the homingCycle() first.")
        return None
    
    if holderData is None:
        print('Select specimen holder first')
        return
    
    clear_output()
    ui.start()
    
    #Record the mean weight of the specimen
    mw = meanWeight(2 * 80)
    mw -= selectedHolder['weight']
    
    temperature = read_temp()
    
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
    
    specimenVolume = meanWeight(2 * 80) - mw - selectedHolder['weight']
    specimenVolume -= dp.forceToVolume(specimenVolume, temperature)
    
    sendMotionCommand('G1X540Z{0}F2000'.format(topHeigth))
    
    try:
        df = pd.DataFrame(columns=['depth', 'force'], dtype='float')
        df['depth'] = ((data['time']-data['time'].iloc[int(smoothing/2)])*loweringSpeed/60)/1000.0 + data['level'] - data['level'].iloc[int(smoothing/2)]
        df['force'] = data['loadCell'].apply(loadCellToRelativeGrams)
        # To make displacement positive, multiply force by -1.0
        df['force'] *= -1.0
        df['force'] = df['force'].rolling(10, center=True).median()
        df = df.dropna()
        df = df.set_index(['depth'])
        df = dp.resampleDF(df)
        df['force'] = df['force'].apply(dp.forceToVolume, tempC=temperature)
        #print(df.head(30))
    except:
        print('Data processing failed')
    
    #holderData = pd.read_pickle('specimenHolder')
    
    diff = dp.synchronizeMeasurement(df, holderData)
    smoothDiff = dp.smooth(diff, 21)
    
    volume = dp.calculateVolume(diff)
    print('Total volume: {:.2f} l'.format(volume))
    print('Specimen weight: {:.2f} g'.format(mw))
    print('Specimen density: {:.2f} kg/m^3'.format((mw/1000.0) / (volume/1000.0)))
    print('Water temperature: {:.2f}°C'.format(temperature))
    
    diff.index.name = 'depth'
    diff.to_pickle('{}_testMeasurement_diff-{}'.format(datetime.now(), mw))
    #diff.to_csv('{}_testMeasurementDiff-{}.csv'.format(datetime.now(), mw), sep = ';', decimal=",")
    dp.toExcel(diff, '{}_{}_{:.2f}'.format(measurementNamePrefix, datetime.now(), mw))
    
    #get_ipython().run_line_magic('matplotlib', 'inline')
    fig=plt.figure()
    plt.plot(smoothDiff)
    # Plot total volume as dashed horizontal line
    plt.ylabel('Volume (l)')
    plt.xlabel('Depth (mm)')
    plt.show()
    
    plt.pause(0.1)
    
    for c in reversed(movementsToTopOfTank):
        sendMotionCommand(c)
    motionFinished(wait=True)

def startup(noHoming=False):
    if(noHoming):
        initMotionControl()
        homingDone = True
        initSensors()
    else:
        initMotionControl()
        homingCycle()
        initSensors()
    
def selectHolder():
    selectSpecimenHolder()
    
def calibrateLoadCell(weights):
    #weights = input('How many weights? (default 3): ')
    try:
        weights = int(weights)
    except:
        print('Using 3 weights')
        weights = 3
    calibrateLoadCell(weights)
    
def calibrateHolder(numAverages):
    '''
    numTimes = input('How many averages? (default 3): ')
    try:
        numTimes = int(numTimes)
    except:
        numTimes = 3
    '''
    calibrateHolder(numAverages)
    
def measure():
    measurementCycle()
    '''
    try:
        hw.measurementCycle()
    except NameError:
        print('Run Startup first')
    '''
    
def homing():
    homingCycle()
    
def reset():
    resetMotionController()
    
def shutdown():
    print('Shutdown')
    try:
        closeSerial(hw.mcSerial)
        closeSerial(hw.sensorSerial)
    except:
        pass
    os.seteuid(1000)
    os.system('sudo sh /home/pi/Desktop/dimensiometer/Software/backend/shutdown.sh')
    
def start():
        ui.runUI()