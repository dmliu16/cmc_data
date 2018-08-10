HOW_TO_CMC101

Author: David Liu

WARNINGS:
	- put all the files in the same folder


General Steps Summary:
	1) get formatted cmc stat file as a csv
	2) get the upc and Shaefer provided item dimensions for each packorder
	3) figure out a more accurate estimation for item size base on CMC box size and WMS item size
	4) calulate the minimum Walmart box each items can be placed in
	5) calulate the dunnage, volumne, corrugate usage and waste for each packorder
	6) calulate material VCPU savings

Details:

	1) get formatted cmc stat file as a csv
		a) put all the stat.txt files from CMC local machine into one folder; let's call the folder 'cwxl_stats'
		b) export the folder as a single txt file
			For mac users
				- open terminal ('command + space' and type in terminal)
				- change directory to the folder 'cwxl_stats' (type cd followed by directory to change directory)
				- after getting to desired directory, type "cat * > merged-file.txt", and we will get a txt file with all concatenated information from all text files
			For windows users
				- look up online pls (not exactly sure)
		c) convert merged-file.txt to a csv file
			- open excel
			- click on data on the top right
			- click on 'From Text'
			- upload the text file
			- choose 'Delimited' and hit next
			- choose Space as the delimiters instead of tabs
			- also click on 'Treat consecutive delimiters as one' and hit next
			- hit Finish and save file as a csv file 'merged-file.csv'
		Note: after step c), the file would be saved as a csv but still malformated bc of the extra info like daily performance
		d) get rid of the header for the first day and make some changes to the csv file
			- open the csv file we just saved 'merged-file.csv'
			- look for the first appearance of '------------------------------------------------------------------', there should be two of those dashes for everyday; two rows above that you would see the headers; 'Num', 'Time', 'SizeH'...
			- delete everything above the header, and choose to shift cell up
			- delete everything in the row of '------------------------------------------------------------------' and the row above that which has info about units and some other stuff; also shift cell up
			- now we should be left with the header ('Num', 'TIme', 'SizeH', 'SizeL'...) and the stats info for the first day
			- save the file
		e) get rid of headers for everyday using python
			- export the csv file into python as a datafram df (Sunada should know how to do this)
			- look at the functions library and run funciton #1 on the df
			- this would give you a nicely organized df with only stats left
			- save the df as a csv file "df.to_csv('formated_cmc.csv')"

	2) get the upc and Shaefer provided item dimensions for each packorder
	Note1: now we only have the cmc stats file with all the packorder id (reference barcode), dimensions and weight of the cmc boxes
	Note2: within the folder, we have three csv files from the Schaefer database: 'wms_packorderid.csv', 'wms_stockitem.csv', 'upc_dim.csv'; in order to find the Schaefer provided item size for each order, we need to merge all three files (Sunada might have a better way of doing this; this is just the way I thought of)
		a) load all three files: 'wms_packorderid.csv', 'wms_stockitem.csv', 'upc_dim.csv', and the file we just made 'formated_cmc.csv'; try to only load it once bc the files are big
		b) look at the function library and run function #2 on the dataframes with order - 'formated_cmc.csv', 'wms_packorderid.csv', 'wms_stockitem.csv', 'upc_dim.csv'
		c) the function would return to us a data frame with the upc and item dimensions measured by WMS
		d) save this as a csv file; let's call it "wms_cwxl.csv"

	3) figure out a more accurate estimation for item size base on CMC box size and WMS item size
		a) import the files we just saved "wms_cwxl.csv"
		b) look at the function library and run function #3 (make sure run helper function #1 first: standardize(df))
		(what the function does)
			- convert the dimensions to mm instead of 1/10 mm
			- change the names of cols to wal_l(length), wal_w(width), wal_h(height)
			- standardize the dimensions - make sure walmart and cmc data is referring to the same dimenions (e.g. cmc has width as the longest dimension -> walmart should also have width as the longest dimension) (this is necessary so that we can estimate the item size based on wms data)
			- separate the boxes into two: normal sized and small (with at least one dimension smaller than min dimension)
			For normal sized boxes
				- subtract a constant from each dimension (width with a bigger constant bc of the dent) to get item dimension
			For small boxes
				- we can subtract a constant from height since the mechanical limitation for height is 30mm and almost nothing is as small as that
				- for length and width, we look at if they are hitting the mechanical min of cmc; if it is, we just use the min of either the dimension size wms provided or the maximum size the dimension can be (if the dimension wms provided is bigger than the box dimension which shouldn't be possible)
		c) save the output of the function (let's say 'wms_cwxl_with_itemsize.csv')

	4) calulate the minimum Walmart box each items can be placed in
		a) import 'wms_cwxl_with_itemsize.csv' as wms_cwxl
		b) run function #4 to find the walmart box
		(what the function does)
			- enter a dataframe of all the 18 walmart boxes and their info
			- run helper funciton get_right_size to get the right size for each packorder
				- starting from the smallest 18 boxes and see if the item would fit
					- check fit by assuming at least my side of the item would be touching one side of the box
					- the items can be put vertically or anything as long as one side touching
			- get rid of the ones that can't be fit in walmart boxes
			- convert the unit of walmart boxes from inches to mm
		c) save the output of the function (let's say 'wms_cwxl_new.csv')

	5) calulate the dunnage, volumne, corrugate usage and waste for each packorder
		a) import 'wms_cwxl_new.csv' as wms_cwxl
		b) run funciton #5 to find the material usage
		(what the function does)
			- calculate vol of item for each packorder
			- calculate vol for walmart and cmc boxes
			- figure out cardboard usage for walmart and cmc boxes based on dimensions
			- figure out if the item is produced using the 1000mm cardboard or 1400mm cardboard
			- calculate the waste based on the dimensions and the size of the cardboard used (1000mm or 1400mm)
			- after all the calculation, the file saves as 'wms_cwxl_perfectperfect.csv' automatically; this gives you all the info you need for this project, and it is the final csv file
			- sum everything, and math it to get outcome

	6) calulate material VCPU savings
		a) import 'wms_cwxl_perfectperfect.csv' as wms_cwxl_perfect
		b) run function #6 to find the cost of cardboard
		(what the function does)
			- merge the costs of each walmart box to the table
			- math to figure out the money needed for each walmart and cmc box
			- average the price in terms of cardboard
		c) the cost of dunnage is simply one cent per airbag and we know the number of airbags saved from step 5)
		d) the cost of transportation savings would have to be calculated by Albert and his team
































