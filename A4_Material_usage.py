
# coding: utf-8

# In[51]:


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

# this document attempts to figure out the material usage base on dimensions of boxes
# import all the files i need
wms_cwxl = pd.read_csv('wms_cwxl_perfect.csv')

# figure out the vol of items
wms_cwxl['item_vol'] = wms_cwxl['itemH']*wms_cwxl['itemW']*wms_cwxl['itemL']

# figure out vol of walmart boxes
wms_cwxl['walmart_vol'] = wms_cwxl['walbox_h']*wms_cwxl['walbox_l']*wms_cwxl['walbox_w']

# figure out vol of cmc boxes
wms_cwxl['cmc_vol'] = wms_cwxl['SizeL']*wms_cwxl['SizeW']*wms_cwxl['SizeH']

wms_cwxl['walmart_cardboard'] = 0
wms_cwxl['cmc_cardboard'] = 0

# figure out cardboard used by walmart box and cmc box
for i, row in wms_cwxl.iterrows():
    wms_cwxl['walmart_cardboard'][i] = wal_cardboard(wms_cwxl['walbox_h'][i],wms_cwxl['walbox_l'][i],wms_cwxl['walbox_w'][i])
    wms_cwxl['cmc_cardboard'][i] = cmc_cardboard(wms_cwxl['SizeL'][i],wms_cwxl['SizeW'][i],wms_cwxl['SizeH'][i])
    
    
# in order to calculate wastes, we need to separate items that are packed using 1000mm cardboard and 1400mm cardboard
wms_cwxl['1000mm/1400mm'] = 1000
wms_cwxl = cmc1000_cmc1400(wms_cwxl)

wms_cwxl['Cardboard_Waste'] = 0
# this assigns the cardboard waste to the col
for i, row in wms_cwxl.iterrows():
    wms_cwxl['Cardboard_Waste'][i] = waste_cwxl(wms_cwxl['SizeW'][i],wms_cwxl['SizeH'][i],wms_cwxl['SizeL'][i],wms_cwxl['1000mm/1400mm'][i])
    
# this is the final version of the project
wms_cwxl.to_csv('wms_cwxl_perfectperfect.csv')

# unit conversion
mm3_ft3 = 3.531467e-8
mm2_ft2 = 1.07639e-5
in3_ft3 = 0.000578704

# get the total values
total_item_vol = round(sum(wms_cwxl['item_vol'])*mm3_ft3,3)
total_wal_box_vol = round(sum(wms_cwxl['walmart_vol'])*mm3_ft3,3)
total_cmc_box_vol = round(sum(wms_cwxl['cmc_vol'])*mm3_ft3,3)

# figure out the dunnage and vol savings
order_num = len(wms_cwxl)
dunnage = round(total_wal_box_vol-total_item_vol,3)
airbag_vol = 4.2 * 8.2 * 2.6 * in3_ft3
airbags = round(dunnage/airbag_vol,1)

# total corrugate usage
corrugate_wal = round(sum(wms_cwxl['walmart_cardboard'])*mm2_ft2,3)
corrugate_cmc = round(sum(wms_cwxl['cmc_cardboard'])*mm2_ft2,3)

# total corrugate wasted
corrugated_cmc_wasted = round(sum(wms_cwxl['Cardboard_Waste'])*mm2_ft2,3)

print('Number of orders: ', order_num, '\n')

print('Volume')
print('Total volume of the walmart boxes is: ', total_wal_box_vol, ' ft^3')
print('Total volume of the cmc boxes is: ', total_cmc_box_vol, ' ft^3')
print('Total voumne saved by cmc is ', total_wal_box_vol-total_cmc_box_vol, ' ft^3')
print('Save ', (total_wal_box_vol-total_cmc_box_vol)/total_wal_box_vol*100, '% of volume\n')

print('Dunnage')
print('Total dunnage used by walmart is: ', dunnage, ' ft^3')
print('Total dunage used by cmc is: 0 ft^3')
print('That is ', round(dunnage/order_num,3), ' ft^3 per order')
print('This is roughly ', round(dunnage/order_num/airbag_vol,1), ' airbags per order or ', airbags, " airbags totally\n")

print('Corrugate')
print('Total cardboard used by walmart is: ', corrugate_wal, ' ft^2')
print('Total cardboard used by cmc is: ', corrugate_cmc, 'ft^2')
print('Total cardboard saved by cmc is: ', corrugate_wal-corrugate_cmc, ' ft^2')
print('Total cardboard wasted by cmc is: ', corrugated_cmc_wasted, ' ft^2')
print('Walmart uses ', round(corrugate_wal/order_num,3), 'ft^2 per order')
print('CMC uses ', round(corrugate_cmc/order_num,3), 'ft^2 per order')
print('CMC wastes ', round(corrugated_cmc_wasted/order_num,3), 'ft^2 per order')
print('Use ', (corrugate_cmc-corrugate_wal)/corrugate_wal*100, '% more corrugate area using the CMC Machines')
print('Use ', (corrugate_cmc-corrugate_wal+corrugated_cmc_wasted)/corrugate_wal*100, '% more corrugate area using the CMC Machines if including waste\n')

# figure out the actual box used by walmart
box_type = {'Walmart_Box': ['S1-15', 'S2-18', 'S3-18', 'S4-21', 'S5-24', 'S6-24', 'M1-27', 'M2-27', 'M3-33',
                    'M4-30', 'M5-30', 'M6-36', 'L1-33', 'L2-33', 'L3-45', 'L4-39', 'L5-45', 'L6-45'],
            #'height': [4,   5.25, 6.25,  7.5,  5,   11,  8.5,  11.5,  5.25,  10,  12.25,  9,  13,  16,  12.25,  15,  14.125,  18], 
            #'length': [9.0, 11,   13,    14,   17,  15,  19,   17,    26,    23,  22,     29, 25,  23,  35,     29,  36,      36], 
            #'width' : [6,   8.0,  9,     10,   13,  12,  12,   13,    19,    15,  16,     19, 17,  19,  18,     20,  21,      21],
            'wal_cost'  : [0.14,0.23, 0.29,  0.37, 0.47,0.54,0.55, 0.78,  0.99,  1.01,1.16,   1.45,1.35,1.72,1.86,1.98,  2.68,    2.92] 
           }
type_cost = pd.DataFrame(data=box_type)

# get the cost of each walmart box
wms_cwxl = pd.merge(wms_cwxl, type_cost, on='Walmart_Box', how='left')

# cost per square foot of cmc cardboard
cmc_cardboard_cost = 0.05

# get the total cardboard cost
total_walmart_box_cost = sum(wms_cwxl['wal_cost'])
total_cmc_box_cost = (corrugate_cmc+corrugated_cmc_wasted)*cmc_cardboard_cost

print('Cost')
print('Each box costs walmart ', round(total_walmart_box_cost/order_num,2), '$')
print('Each box costs cmc ', round(total_cmc_box_cost/order_num,2), '$')


# In[50]:


wms_cwxl


# In[22]:


# this alg finds the carboard used of a walmart box given the three dimensions
def wal_cardboard(dim1, dim2, dim3):
    gaps = 10 # this is just 1cm
    # extra is the final part that connects the cardboards
    # they glue around this
    extra = 40 # this is 4cm
    
    dims = sorted([dim1, dim2, dim3])
    h, w, l = dims[0], dims[1], dims[2]
    
    cardboard = h*(w*2+l*2+gaps*3+extra) + w*(2*w+2*l)
    
    return cardboard

# this alg finds the cardboard used by a cm machine given the three dimensions
def cmc_cardboard(l,w,h):
    gaps = 10
    # dent is the extra on width
    dent = 20 # 2cm
    # constant is the constant extra from the height
    constant = 70 # 7cm
    # this is the closing fold on the final part
    extra = 35 #3.5cm
    
    cardboard = w*(2*h+2*l+extra+3*gaps)+2*(h+constant+dent)*(h*2+l*2)
    
    return cardboard


# In[45]:


# this fuction figures out either the box is packed by 1000mm or 1400mm
def cmc1000_cmc1400(df):
    dent = 20
    constant = 70
    gap = 10
    for i,row in df.iterrows():
        w,l,h = df['SizeW'][i], df['SizeL'][i], df['SizeH'][i]
        if (w+2*h+2*dent+2*constant > 1000):
            df['1000mm/1400mm'][i] = 1400
    return df

# this function finds the total wasted cardboard for each box
def waste_cwxl(SizeW, SizeH, SizeL, cardboard_width):
    dent = 20
    constant = 70
    gap = 10
    vertical_waste = (cardboard_width - SizeW - 2*dent - 2*SizeH - 2*constant)*(2*SizeH+2*SizeL+3*gap)
    return vertical_waste


# In[44]:


wms_cwxl.where(wms_cwxl['1000mm/1400mm']==1000).dropna()

