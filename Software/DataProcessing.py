import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from math import ceil

# Requirements for Excel export
#from openpyxl import Workbook
#from openpyxl.chart import ScatterChart, Reference, Series
#from openpyxl import load_workbook

def smooth(df,window_len=11,window='hanning'):
    x = df.iloc[:,0]
    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")
        
    if window_len % 2 != 1:
        raise ValueError("use an odd integer for the window_len.")
        
    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")

    if window_len<3:
        return x

    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")

    
    s=np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='valid')
    #return y
    #return y[(ceil(window_len/2)-1):-(ceil(window_len/2))]
    dfSmooth = pd.DataFrame()
    dfSmooth['smooth'] = y[(ceil(window_len/2)-1):-(ceil(window_len/2))]
    dfSmooth.index = df.index
    return dfSmooth

def resampleDF(df, resolution=0.5):
    '''Resamples the data to 0.5 resolution by default on the index axis.'''
    idx = pd.Index(np.arange(0, ceil(df.index.values.max()), resolution))
    newIdx = idx.union(df.index)
    dfR = df.reindex(newIdx).interpolate(method='index')
    dfR = dfR.reindex(idx)
    return dfR

def rms(x):
    return np.sqrt(x.dot(x)/x.size)

def findSyncPoint(data):
    threshold = 10 * rms(data.iloc[:,0].head(200))
    
    index = 0
    
    while(index < (len(data.iloc[:,0]) -1)):
        val = data.iloc[:,0][index]
        if(val >= threshold):
            prevVal = val
            index += 1
            val = data.iloc[:,0][index]
            while(val > prevVal):
                index += 1
                prevVal = val
                val = data.iloc[:,0][index]
                
            return index - 1
        
        index += 1
    return None

def synchronizeMeasurement(measurementData, holderData):
    holderStartMean = holderData.iloc[:,0][:100].mean()
    measurementStartMean = measurementData.iloc[:,0][:100].mean()
    holderData.iloc[:,0] -= holderStartMean
    measurementData.iloc[:,0] -= measurementStartMean
    print("Specimen mean weight: {:.2f} g".format(-measurementStartMean))
    
    smoothHolder = smooth(holderData, 77)
    smoothMeasurement = smooth(measurementData, 77)
    dHolder = np.diff(smoothHolder.iloc[:,0], 2)
    dMeasurement = np.diff(smoothMeasurement.iloc[:,0], 2)
    dHolder = pd.DataFrame(dHolder, holderData.index[:-2])
    dMeasurement = pd.DataFrame(dMeasurement, measurementData.index[:-2])
    
    measurementSyncPoint = findSyncPoint(dMeasurement)
    holderSyncPoint = findSyncPoint(dHolder)
    print("Measurement SP: {}, Holder SP: {}".format(measurementSyncPoint, holderSyncPoint))
    
    measurementData.index -= (measurementSyncPoint-holderSyncPoint)
    smoothMeasurement.index -= (measurementSyncPoint-holderSyncPoint)
    diff = pd.DataFrame(columns=['depth', 'force'], dtype='float')
    diff['Force'] = measurementData.iloc[:,0]-holderData.iloc[:,0]
    diff = resampleDF(diff)
    
    #DEBUG
    fig=plt.figure()
    dHolder.index += (measurementSyncPoint-holderSyncPoint)
    plt.plot(dHolder[(holderSyncPoint - 100):(holderSyncPoint+100)])
    plt.plot(dMeasurement[(measurementSyncPoint-100):(measurementSyncPoint+100)])
    plt.show()
    
    fig=plt.figure()
    #smoothHolder.index += (measurementSyncPoint-holderSyncPoint)
    plt.plot(smoothHolder[(holderSyncPoint - 50):(holderSyncPoint+50)])
    plt.plot(smoothMeasurement[(measurementSyncPoint-50):(measurementSyncPoint+50)])
    plt.show()
    
    return diff

'''
def toExcel(df, name):
    df.index.name = 'depth'
    df.to_excel('{}.xlsx'.format(name))
    workbook = load_workbook(filename='{}.xlsx'.format(name))
    sheet = workbook.active
    chart = ScatterChart()
    chart.title = 'Measurement'
    chart.style = 1
    chart.x_axis.title = 'Depth (mm)'
    chart.y_axis.title = 'Volume (ml)'

    num_rows = len(sheet['A'])
    xvalues = Reference(sheet, min_col=1, min_row=1, max_row=num_rows)
    values = Reference(sheet, min_col=2, min_row=1, max_row=num_rows)
    series = Series(values, xvalues, title_from_data=True)
    chart.series.append(series)
    chart.legend = None
    sheet.add_chart(chart, "C1")

    workbook.save('{}.xlsx'.format(name))
'''
