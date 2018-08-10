
# coding: utf-8

# In[49]:


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

# this file attempts to figure out the item size

# import files
wms_cwxl = pd.read_csv('wms_cwxl.csv')

# convert walmart dimensions to mm
wms_cwxl['DEPTH'] = wms_cwxl['DEPTH']/10
wms_cwxl['HEIGHT'] = wms_cwxl['HEIGHT']/10
wms_cwxl['WIDTH'] = wms_cwxl['WIDTH']/10

# rename the depth
wms_cwxl = wms_cwxl.rename(index=str, columns={"DEPTH": "LENGTH"})

# rename
wms_cwxl = wms_cwxl.rename(index=str, columns={"LENGTH": "wal_l"})
wms_cwxl = wms_cwxl.rename(index=str, columns={"WIDTH": "wal_w"})
wms_cwxl = wms_cwxl.rename(index=str, columns={"HEIGHT": "wal_h"})

# the minimum dimensions
# some of them are different from the mechanical min bc of the labels
min_h = 30
min_l = 160
min_w = 250

# make sure we are talking about the same dimensions
# aka dimensions are standardized btw walmart and cmc
wms_cwxl = standardize(wms_cwxl)

# get rid of small items only left with normal sized items
cwxl_normal = wms_cwxl.where(np.logical_and(np.logical_and(wms_cwxl['SizeW'] > min_w, wms_cwxl['SizeH'] > min_h), wms_cwxl['SizeL'] > min_l))
cwxl_normal = cwxl_normal.dropna()

# an estimated space that the item can move around in each direction
freeSpace = 13 # this is about half an inch
boxThickness = 3

# the extra width for the built of the box 
extra_width = 20*2 # 2cm on each side
cwxl_normal['itemW'] = cwxl_normal['SizeW'] - freeSpace - 2*boxThickness - extra_width
cwxl_normal['itemH'] = cwxl_normal['SizeH'] - freeSpace - 2*boxThickness
cwxl_normal['itemL'] = cwxl_normal['SizeL'] - freeSpace - 2*boxThickness

# this gets us the items of normal size
#cwxl_normal.to_csv('cwxl_normal.csv')

# find small items
cwxl_small = wms_cwxl.where(np.logical_or(np.logical_or(wms_cwxl['SizeW'] <= min_w, wms_cwxl['SizeH'] <= min_h), wms_cwxl['SizeL'] <= min_l))
cwxl_small = cwxl_small.dropna()

# these are the default item size
cwxl_small['itemW'], cwxl_small['itemL'], cwxl_small['itemH'] = cwxl_small['wal_w'], cwxl_small['wal_l'], cwxl_small['wal_h']

# we know the height is nvr minimized bc min of the table is 35 which is bigger than the min dim cmc can make
cwxl_small['itemH'] = cwxl_small['SizeH'] - freeSpace - 2*boxThickness

# figure out the dimensions of length and width for cwxl_small
for index, row in cwxl_small.iterrows():
    # the max width and length we can have
    max_width = cwxl_small['SizeW'][index] - freeSpace - 2*boxThickness - extra_width
    max_length = cwxl_small['SizeL'][index] - freeSpace - 2*boxThickness
    # if the width is bigger than min
    if cwxl_small['SizeW'][index] != min_w:
        cwxl_small['itemW'][index] = max_width
    # see if the walmart measurement is bigger than the max
    elif (cwxl_small['itemW'][index] > max_width):
        cwxl_small['itemW'][index] = max_width

    # if the length is bigger than min
    if cwxl_small['SizeL'][index] != min_l:
        cwxl_small['itemL'][index] = max_length
    # see if the walmart length measurement is bigger than the max length
    elif (cwxl_small['itemL'][index] > max_length):
        cwxl_small['itemL'][index] = max_length
        
# get the info we need
wms_cwxl = pd.concat([cwxl_normal, cwxl_small], sort=True)

# save to csv
wms_cwxl.to_csv('wms_cwxl_with_itemsize.csv')


# In[48]:


# this fuction matches the height, len and width with the correct dimension
# given the datafram
def standardize(df):
    #df = df.rename(index=str, columns={"DEPTH_FT": "LENGTH_FT"})
    # this standardizes the len, width, and height
    # made sure that they are measuring the same dimension
    for i,row in df.iterrows():
        width, length = 0, 0
        l_ft = df['wal_l'][i]
        w_ft = df['wal_w'][i]
        h_ft = df['wal_h'][i]
        iW = df['SizeW'][i]-40 # minus 40 for the dent
        iL = df['SizeL'][i]
        iH = df['SizeH'][i]
        fts = sorted([l_ft, w_ft, h_ft])
        i_s = sorted([iW, iL, iH])
        # min values
        min_ft = fts[0]
        min_i = i_s[0]
        # second smallest
        min2_ft = fts[1]
        min2_i = i_s[1]
        # third smallest aka largest
        min3_ft = fts[2]
        min3_i = i_s[2]
        # rank the dimensions and match them
        # smallest ft is width
        if (min_i == iW):
            df['wal_w'][i] = min_ft
            if (min2_i == iL):
                df['wal_l'][i] = min2_ft
                df['wal_h'][i] = min3_ft
            else:
                df['wal_h'][i] = min2_ft
                df['wal_l'][i] = min3_ft
        # smallest ft is length
        elif (min_i == iL):
            df['wal_l'][i] = min_ft
            if (min2_i == iW):
                df['wal_w'][i] = min2_ft
                df['wal_h'][i] = min3_ft
            else:
                df['wal_h'][i] = min2_ft
                df['wal_w'][i] = min3_ft
        # smallest ft is height
        else:
            df['wal_h'][i] = min_ft
            if (min2_i == iW):
                df['wal_w'][i] = min2_ft
                df['wal_l'][i] = min3_ft
            else:
                df['wal_l'][i] = min2_ft
                df['wal_w'][i] = min3_ft
                
    return df


# In[23]:


wms_cwxl.where(wms_cwxl['SizeH'] == 35).dropna()


# In[39]:



print(len(cwxl_small)+len(cwxl_normal))
print(len(wms_cwxl))


# In[51]:


wms_cwxl['diff_h'], wms_cwxl['diff_l'], wms_cwxl['diff_w'] = wms_cwxl['itemH']-wms_cwxl['wal_h'],wms_cwxl['itemL']-wms_cwxl['wal_l'],wms_cwxl['itemW']-wms_cwxl['wal_w']


# In[53]:


print(sum(wms_cwxl['diff_h']))
print(sum(wms_cwxl['diff_l']))
print(sum(wms_cwxl['diff_w']))

