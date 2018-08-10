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

# this file attempts to get the walmart dimensions of all the cmc boxes (from schaefer wms)

# load our csv files
cwxl_out = pd.read_csv('cwxl_out.csv')
wms_packorder = pd.read_csv('wms_packorderid.csv')

# reformat the csv file

# reformat the cwxl_out to get rid of the rubbish ('---', '2017 3:14:25'...)
len_cwxl = len(cwxl_out)
count = 0
dash_line = []
for i in range(len(cwxl_out)):
    if (cwxl_out.loc[i, 'Unnamed: 0'] == '------------------------------------------------------------------'):
        dash_line.append(i)

temp = cwxl_out

for i in range(0, len(dash_line), 2):
    standard = 0
    if i != 0:
        standard = dash_line[i-1]+1
    temp = temp.append(cwxl_out.iloc[standard:dash_line[i]])
cwxl_out = temp[len_cwxl:]         

# del unneccesary cols
del cwxl_out['Unnamed: 0']
del cwxl_out['Unnamed: 8']

# rename referece to packorderid
cwxl_out = cwxl_out.rename(index=str, columns={"Reference": "PACKORDERID"})

# convert to int
cwxl_out['PACKORDERID'] = pd.to_numeric(cwxl_out['PACKORDERID'], errors='coerce')
cwxl_out['SizeW'] = pd.to_numeric(cwxl_out['SizeW'], errors='coerce')
cwxl_out['SizeH'] = pd.to_numeric(cwxl_out['SizeH'], errors='coerce')
cwxl_out['SizeL'] = pd.to_numeric(cwxl_out['SizeL'], errors='coerce')
cwxl_out['Weight'] = pd.to_numeric(cwxl_out['Weight'], errors='coerce')

# save it
cwxl_out.to_csv('cwxl_out_good.csv')

# get rid of duplicates
cwxl_out = cwxl_out.drop_duplicates(subset=['PACKORDERID'], keep=False)
wms_packorder = wms_packorder.drop_duplicates(subset=['PACKORDERID'])

# merge the two files to get walmart shipping lu id
wms_cwxl = pd.merge(wms_packorder, cwxl_out, on='PACKORDERID', how='right')

# load this file for upc
stock_item = pd.read_csv('wms_stockitem.csv')

# remove the duplicates from wms_stockitem
stock_item = stock_item.drop_duplicates(subset=['PACKORDERID'], keep='first')

# join the two table
wms_cwxl_upc = pd.merge(wms_cwxl, stock_item, on='PACKORDERID', how='inner')

# import upc with dimension
upc_dim = pd.read_csv('upc_dim.csv')

# rename to upc
wms_cwxl_upc = wms_cwxl_upc.rename(index=str, columns={"MATERIALUPC": "UPC"})

# drop duplicated UPC's
upc_dim = upc_dim.drop_duplicates(subset=['UPC'])

# merge to get the dimensions
wms_cwxl_dim = pd.merge(wms_cwxl_upc, upc_dim, on='UPC', how='left')

# only keep the cols that we need
wms_cwxl_dim = wms_cwxl_dim[['PACKORDERID', 'SizeH', 'SizeW', 'SizeL', 'UPC', 'DEPTH', 'HEIGHT', 'WIDTH', 'WEIGHT']]
wms_cwxl_dim = wms_cwxl_dim.dropna()

# save as a csv file
wms_cwxl_dim.to_csv('wms_cwxl.csv')


# In[102]:



print(len(wms_cwxl))
print(len(wms_cwxl_upc))
print(len(wms_cwxl_dim))

print(len(wms_cwxl_dim))


# In[114]:


a = wms_cwxl_upc.sample(n=1000)
sns.distplot(a['SizeW'], rug=True)


# In[112]:


b = wms_cwxl_dim.sample(n=1000)
sns.distplot(b['SizeL'], rug=True)




