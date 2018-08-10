
# coding: utf-8

# In[18]:


import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns
get_ipython().run_line_magic('matplotlib', 'inline')

import ipywidgets as widgets
from ipywidgets import interact

# Plotly plotting support
import plotly.offline as py
py.init_notebook_mode()
import plotly.graph_objs as go
import plotly.figure_factory as ff
import cufflinks as cf
cf.set_config_file(offline=True, world_readable=True, theme='ggplot')

# this file attempts to figure out the box walmart would have used and the dimenions of the box

# import all the files i need
wms_cwxl = pd.read_csv('wms_cwxl_with_itemsize.csv')

del wms_cwxl['Unnamed: 0.1']

# figure out the actual box used by walmart
box_type = {'BOXTYPE': ['S1-15', 'S2-18', 'S3-18', 'S4-21', 'S5-24', 'S6-24', 'M1-27', 'M2-27', 'M3-33',
                    'M4-30', 'M5-30', 'M6-36', 'L1-33', 'L2-33', 'L3-45', 'L4-39', 'L5-45', 'L6-45'],
            'height': [4,   5.25, 6.25,  7.5,  5,   11,  8.5,  11.5,  5.25,  10,  12.25,  9,  13,  16,  12.25,  15,  14.125,  18], 
            'length': [9.0, 11,   13,    14,   17,  15,  19,   17,    26,    23,  22,     29, 25,  23,  35,     29,  36,      36], 
            'width' : [6,   8.0,  9,     10,   13,  12,  12,   13,    19,    15,  16,     19, 17,  19,  18,     20,  21,      21]}
type_dimension = pd.DataFrame(data=box_type)

wms_cwxl['Walmart_Box'] = 0

# choose a box for the ones that we can't retrieve information from 
wms_cwxl = get_right_size(wms_cwxl, type_dimension)

# find the ones that doesn't fit and kick it out
wms_cwxl_new = wms_cwxl.where(wms_cwxl['Walmart_Box'] != 'LOL u too big').dropna()

type_dimension = type_dimension.rename(index=str, columns={"BOXTYPE": "Walmart_Box"})
wms_cwxl_new = pd.merge(wms_cwxl_new, type_dimension, on='Walmart_Box', how='left')

# rename
wms_cwxl_new = wms_cwxl_new.rename(index=str, columns={"height": "walbox_h"})
wms_cwxl_new = wms_cwxl_new.rename(index=str, columns={"length": "walbox_l"})
wms_cwxl_new = wms_cwxl_new.rename(index=str, columns={"width": "walbox_w"})

# get to the right units mm
wms_cwxl_new['walbox_h'] = wms_cwxl_new['walbox_h']*25.4
wms_cwxl_new['walbox_w'] = wms_cwxl_new['walbox_w']*25.4
wms_cwxl_new['walbox_l'] = wms_cwxl_new['walbox_l']*25.4

# export this to a csv
wms_cwxl_new.to_csv('wms_cwxl_perfect.csv')


# In[29]:


type_dimension


# In[3]:





# In[4]:





# In[17]:


# this help us to get the right box to use
def get_right_size(df, box_dim):
    for i,row in df.iterrows():
        print(i)
        # identify the ones that dont fit in the box
        # find the right box we should use
        df['Walmart_Box'][i] = find_right_size(df['itemW'][i], df['itemH'][i], df['itemL'][i], box_dim)
    return df
    
    
def find_right_size(itemW, itemH, itemL, type_dimension):
    for i,row in type_dimension.iterrows():
        box = type_dimension['BOXTYPE'][i]
        height, width, length = type_dimension['height'][i]*25.4, type_dimension['width'][i]*25.4, type_dimension['length'][i]*25.4
        info = {'BOXTYPE': [box], 'itemW': [itemW], 'itemH': [itemH], 'itemL': [itemL], 'width': [width], 'height': [height], 'length': [length]}
        df = pd.DataFrame(data=info)
        if fit(df)['fit'][0] == True:
            return box
    print('The item is too big for all boxes')
    return 'LOL u too big'


# In[14]:


import math

# this fuction adds one more col for the dataframe to see if the item would if in the recommended box
def fit(df):
    error = 10
    df['fit'] = True
    # finds the vol of the item and the box
    df['vol_item'] = (df['itemL']+error)*(df['itemH']+error)*(df['itemW']+error)
    df['vol_box'] = ((df['height'])*(df['width'])*(df['length']))
    for i in range(len(df)):
        # sort them so it's easy to rank the dimensions
        item_size = sorted([df['itemW'][i]+error,df['itemH'][i]+error,df['itemL'][i]+error])
        box_size = sorted([(df['height'][i]),(df['width'][i]),(df['length'][i])])
        
        # first do the simpliest check, compare vol
        if (df['vol_item'][i] > df['vol_box'][i]):
            df['fit'][i] = False
            continue
        
        # now we case the problem into three cases
        # we try to lay the biggest side of the item on a side of the box
        # we case on the three different sides of the box
        
        # This way we reduce the 3 dimensional problem to a 2 dimensional one
        
        # because we are definitely laying a side of the item flat
        # the area of that side has to be smaller than the biggest side of the area
        if (b_in_a(box_size[2],box_size[1],item_size[2],item_size[1])):
            if (item_size[0] <= box_size[0]):

                continue
                
            
        # see if the biggest side of the item is smaller than the smallest side of the box or second smallest side
        # aka lay smallest side
        if (b_in_a(box_size[1],box_size[0],item_size[2],item_size[1])):
            if (box_size[2] >= item_size[0]):
                
                continue

        # aka lay second smallest side
        if (b_in_a(box_size[2],box_size[0],item_size[2],item_size[1])):
            if (box_size[1] >= item_size[0]):
                continue

        
        
        
        df['fit'][i] = False
    
        
    return df


# according to a theorm I found online
# suppose an a1*a2 rectangle T is given, with the notation arranged so that a1 >= a2
# then a b1*b2 rectangle R given b1>=b2 fits into T if and only if
# 1. b1 <= a1 and b2 <= a2, or
# 2. b1 > a1, b2 <= a2, and ((a1+a2)/(b1+b2))^2 + ((a1-a2)/(b1-b2))^2 >= 2

# the second part of the theorm comes from sin and xos of the rotating angle theta

def b_in_a (a1, a2, b1, b2):
    statement1 = (b1 <= a1 and b2 <= a2)
    statement2 = (b1 > a1 and b2 <= a2 and ((a1+a2)/(b1+b2))**2 + ((a1-a2)/(b1-b2))**2 >= 2)
    if (statement1 or statement2):
        return True
    return False

