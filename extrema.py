import numpy as np

def max_data(data,date):
    #δέχεται np array
    max = np.nanmax(data)
    max_index = np.nanargmax(data)
    max_date = date[max_index]
    
    return max,max_date

def min_data(data,date):
    #δέχεται np array
    min = np.nanmin(data)
    min_index = np.nanargmin(data)
    min_date = date[min_index]
    
    return min,min_date