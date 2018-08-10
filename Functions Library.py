
# coding: utf-8

# In[1]:


## Do not change this part of the file pls
#############################################
import numpy as np 
import pandas as pd 
#############################################


# In[3]:


##################
## function #1: ##
##################
def reformat_csv(df):
    len_cwxl = len(df)
    count = 0
    dash_line = []
    for i in range(len(df)):
        if (df.loc[i, df.columns[0]] == '------------------------------------------------------------------'):
            dash_line.append(i)

    temp = df

    for i in range(0, len(dash_line), 2):
        standard = 0
        if i != 0:
            standard = dash_line[i-1]+1
        temp = temp.append(df.iloc[standard:dash_line[i]])
    df = temp[len_cwxl:]
    df = df.rename(index=str, columns={"Reference": "PACKORDERID"})
    # convert to int
    df['PACKORDERID'] = pd.to_numeric(df['PACKORDERID'], errors='coerce')
    df['SizeW'] = pd.to_numeric(df['SizeW'], errors='coerce')
    df['SizeH'] = pd.to_numeric(df['SizeH'], errors='coerce')
    df['SizeL'] = pd.to_numeric(df['SizeL'], errors='coerce')
    df['Weight'] = pd.to_numeric(df['Weight'], errors='coerce')
    return df


# In[5]:


##################
## function #2: ##
##################
def get_wms_dimensions(cwxl_out, wms_packorder, stock_item, upc_dim):
    # get rid of duplicates
    cwxl_out = cwxl_out.drop_duplicates(subset=['PACKORDERID'], keep=False)
    wms_packorder = wms_packorder.drop_duplicates(subset=['PACKORDERID'])

    # merge the two files to get walmart shipping lu id
    wms_cwxl = pd.merge(wms_packorder, cwxl_out, on='PACKORDERID', how='right')

    # remove the duplicates from wms_stockitem
    stock_item = stock_item.drop_duplicates(subset=['PACKORDERID'], keep='first')

    # join the two table
    wms_cwxl_upc = pd.merge(wms_cwxl, stock_item, on='PACKORDERID', how='inner')

    # rename to upc
    wms_cwxl_upc = wms_cwxl_upc.rename(index=str, columns={"MATERIALUPC": "UPC"})

    # drop duplicated UPC's
    upc_dim = upc_dim.drop_duplicates(subset=['UPC'])

    # merge to get the dimensions
    wms_cwxl_dim = pd.merge(wms_cwxl_upc, upc_dim, on='UPC', how='left')

    # only keep the cols that we need
    wms_cwxl_dim = wms_cwxl_dim[['PACKORDERID', 'SizeH', 'SizeW', 'SizeL', 'UPC', 'DEPTH', 'HEIGHT', 'WIDTH', 'WEIGHT']]
    wms_cwxl_dim = wms_cwxl_dim.dropna()

    return wms_cwxl_dim


# In[13]:


##################
## function #3: ##
##################
def estimate_itemSize(wms_cwxl):
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
    return wms_cwxl


# In[8]:


##################
## function #4: ##
##################
def find_wal_box(wms_cwxl):
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
    return wms_cwxl_new


# In[22]:


##################
## function #5: ##
##################
def material_usage(wms_cwxl):
    # figure out the vol of items
    wms_cwxl['item_vol'] = wms_cwxl['itemH']*wms_cwxl['itemW']*wms_cwxl['itemL']

    # figure out vol of walmart boxes
    wms_cwxl['walmart_vol'] = wms_cwxl['walbox_h']*wms_cwxl['walbox_l']*wms_cwxl['walbox_w']

    # figure out vol of cmc boxes
    wms_cwxl['cmc_vol'] = wms_cwxl['SizeL']*wms_cwxl['SizeW']*wms_cwxl['SizeH']

    wms_cwxl['walmart_cardboard'] = 0
    wms_cwxl['cmc_cardboard'] = 0

    count = 1
    size = len(wms_cwxl)
    # figure out cardboard used by walmart box and cmc box
    for i, row in wms_cwxl.iterrows():
        print(count/size*33, '%')
        wms_cwxl['walmart_cardboard'][i] = wal_cardboard(wms_cwxl['walbox_h'][i],wms_cwxl['walbox_l'][i],wms_cwxl['walbox_w'][i])
        wms_cwxl['cmc_cardboard'][i] = cmc_cardboard(wms_cwxl['SizeL'][i],wms_cwxl['SizeW'][i],wms_cwxl['SizeH'][i])
        count += 1


    # in order to calculate wastes, we need to separate items that are packed using 1000mm cardboard and 1400mm cardboard
    wms_cwxl['1000mm/1400mm'] = 1000
    wms_cwxl = cmc1000_cmc1400(wms_cwxl)

    wms_cwxl['Cardboard_Waste'] = 0
    # this assigns the cardboard waste to the col
    count = 1
    for i, row in wms_cwxl.iterrows():
        print(count/size*33+67,'%')
        wms_cwxl['Cardboard_Waste'][i] = waste_cwxl(wms_cwxl['SizeW'][i],wms_cwxl['SizeH'][i],wms_cwxl['SizeL'][i],wms_cwxl['1000mm/1400mm'][i])
        count+=1

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


# In[24]:


##################
## function #6: ##
##################
def material_cost(wms_cwxl):
    order_num = len(wms_cwxl)
    # unit conversion
    mm3_ft3 = 3.531467e-8
    mm2_ft2 = 1.07639e-5
    in3_ft3 = 0.000578704
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

    # total corrugate usage
    corrugate_wal = round(sum(wms_cwxl['walmart_cardboard'])*mm2_ft2,3)
    corrugate_cmc = round(sum(wms_cwxl['cmc_cardboard'])*mm2_ft2,3)

    # total corrugate wasted
    corrugated_cmc_wasted = round(sum(wms_cwxl['Cardboard_Waste'])*mm2_ft2,3)
    
    # get the total cardboard cost
    total_walmart_box_cost = sum(wms_cwxl['wal_cost'])
    total_cmc_box_cost = (corrugate_cmc+corrugated_cmc_wasted)*cmc_cardboard_cost

    print('Cost')
    print('Each box costs walmart ', round(total_walmart_box_cost/order_num,2), '$')
    print('Each box costs cmc ', round(total_cmc_box_cost/order_num,2), '$')


# In[21]:


## helper functions for main functions #1, #2, #3
##

import math

#########################
## helper function #1: ##
#########################
# this fuction matches the height, len and width with the correct dimension
# given the datafram
def standardize(df):
    # this standardizes the len, width, and height
    # made sure that they are measuring the same dimension
    count = 1
    size = len(df)
    for i,row in df.iterrows():
        print(count/size*100, '%')
        count += 1
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


#########################
## helper function #2: ##
#########################
# according to a theorm I found online
# suppose an a1*a2 rectangle T is given, with the notation arranged so that a1 >= a2
# then a b1*b2 rectangle R given b1>=b2 fits into T if and only if
# 1. b1 <= a1 and b2 <= a2, or
# 2. b1 > a1, b2 <= a2, and ((a1+a2)/(b1+b2))^2 + ((a1-a2)/(b1-b2))^2 >= 2

# the second part of the theorm comes from sin and xos of the rotating angle theta
# Sunada and David also proved this theorm 

def b_in_a (a1, a2, b1, b2):
    statement1 = (b1 <= a1 and b2 <= a2)
    statement2 = (b1 > a1 and b2 <= a2 and ((a1+a2)/(b1+b2))**2 + ((a1-a2)/(b1-b2))**2 >= 2)
    if (statement1 or statement2):
        return True
    return False


#########################
## helper function #3: ##
#########################
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

#########################
## helper function #4: ##
#########################
# this help us to get the right box to use
def get_right_size(df, box_dim):
    size = len(df)
    count = 1
    for i,row in df.iterrows():
        print(count/size*100, '%')
        # identify the ones that dont fit in the box
        # find the right box we should use
        df['Walmart_Box'][i] = find_right_size(df['itemW'][i], df['itemH'][i], df['itemL'][i], box_dim)
        count += 1
    return df
    
    
#########################
## helper function #5: ##
#########################
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

#########################
## helper function #6: ##
#########################
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

#########################
## helper function #7: ##
#########################
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

#########################
## helper function #8: ##
#########################
# this fuction figures out either the box is packed by 1000mm or 1400mm
def cmc1000_cmc1400(df):
    dent = 20
    constant = 70
    gap = 10
    count = 1
    size = len(df)
    for i,row in df.iterrows():
        print(count/size*33+33,'%')
        w,l,h = df['SizeW'][i], df['SizeL'][i], df['SizeH'][i]
        if (w+2*h+2*dent+2*constant > 1000):
            df['1000mm/1400mm'][i] = 1400
        count += 1
    return df

#########################
## helper function #9: ##
#########################
# this function finds the total wasted cardboard for each box
def waste_cwxl(SizeW, SizeH, SizeL, cardboard_width):
    dent = 20
    constant = 70
    gap = 10
    vertical_waste = (cardboard_width - SizeW - 2*dent - 2*SizeH - 2*constant)*(2*SizeH+2*SizeL+3*gap)
    return vertical_waste

