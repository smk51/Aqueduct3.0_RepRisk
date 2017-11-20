##---------------------------------------------------------------------
## repRisk_Indicator_creation.py
##
## Description: Selects the most recent RepRisk data export, then formats it into a
##              CSV that is ready to join with the WRI Aqueduct 3.0 database
##
##
## Created: 06/22/2017
## Editor: Samantha Kuzma - samantha.kuzma@wri.org
## World Resources Institute - Aqueduct Project
##---------------------------------------------------------------------

### - - - - - - - - - - - - - - - - - - - - - - - - ###
## Import modules
import sys
import os
import numpy as np
import pandas as pd
import datetime
## Define workspace paths
##
scriptPath = sys.argv[0]
scriptFolder = os.path.dirname(scriptPath)
rootFolder = os.path.dirname(scriptFolder)
allDataFolder = os.path.join(rootFolder, "Data")
rawFolder = os.path.join(allDataFolder, "raw")  # location of raw data to be process
finalFolder = os.path.join(allDataFolder, "final") # location where processed data will be saved
### - - - - - - - - - - - - - - - - - - - - - - - - ###
#     STEP 1: FIND MOST RECENT RRI DATA
### - - - - - - - - - - - - - - - - - - - - - - - - ###
## Select most recent Peak RRI export file from RepRisk database
exportDate = None                   # set export date as null
rawFiles = os.listdir(rawFolder)    # read in list of all data export files
for i in rawFiles:                  # loop through all files to find most recent Peak export
    rriType = i[4:8]
    fileDate = i[9:17]
    if rriType == 'Peak':
        if fileDate > exportDate:
            fileName = i

### - - - - - - - - - - - - - - - - - - - - - - - - ###
#     STEP 2: READ IN DATA
### - - - - - - - - - - - - - - - - - - - - - - - - ###
## Read data into dataframe
# Open Reprisk data
fopen = os.path.join(rawFolder, fileName)  # file location
df_r = pd.read_csv(fopen,encoding='utf-8') # open RepRisk data
df_r['Name'] = df_r['Name'].str.lower()     #Make country names lower case (for lookup)
# Open Country look-up table (will be used to assign ISO country code to RepRisk data)
copen = os.path.join(rawFolder, "pyCountry.xlsx")  #file location
df_c = pd.read_excel(copen, sheetname= "lookUp", encoding='utf-8')  # open country lookup data

### - - - - - - - - - - - - - - - - - - - - - - - - ###
#     STEP 3: MATCH REPRISK DATA TO ISO CODES
### - - - - - - - - - - - - - - - - - - - - - - - - ###
## Combine RepRisk score with ISO codes
dflook = pd.merge(df_r, df_c, how='left', left_on='Name', right_on='RepRisk')
# Remove any countries that are not included in WRI's official country list
df_filt = dflook.loc[dflook["Exclude"]=="No"]
# Create dataframe for final data to output
finalHeader = ["ISO", "WRI_ISO", "Peak_RRI"] # Header for CSV
df_final = df_filt[finalHeader].copy()    # Copy data from filt dataframe

### - - - - - - - - - - - - - - - - - - - - - - - - ###
#     STEP 4: DEFINE RISK CATEGORIES
### - - - - - - - - - - - - - - - - - - - - - - - - ###
## Set risk thresholds
def threshold(row):
    x = float(row["Peak_RRI"])
    if x <= 50:
        val = max(0,((x - 25)/ 25 + 1))
    elif x <= 60:
        val = (x - 60)/ 10 + 3
    elif x <= 75:
        val = (x - 75)/ 15 + 4
    else:
        val = min(5,((x - 100)/ 25 + 5))
    return val

## Set risk category names
def cat(row):
    if row["RRI_s"] >= 4:
        val = "Extremely High (>75%)"
    elif  row["RRI_s"] >= 3:
        val  = "High (60 - 74%)"
    elif row["RRI_s"] >= 2:
        val = "Medium - High (50 - 59%)"
    elif row["RRI_s"] >= 1:
        val = "Low - Medium (26 - 49%)"
    else:
        val = "Low (0 - 25%)"
    return val

# Apply the category function to the data
df_final['RRI_s'] = df_final.apply(threshold, axis = 1)
df_final['RRI_Cat'] = df_final.apply(cat, axis = 1)

### - - - - - - - - - - - - - - - - - - - - - - - - ###
#     STEP 5: SAVE FINAL DATA TO CSV
### - - - - - - - - - - - - - - - - - - - - - - - - ###
# Export the data
procPath = os.path.join(finalFolder, "final_"+fileName) # location of CSV export
df_final.to_csv(procPath) # Write dataframe to CSV

### - - - - - - - - - - - - - - - - - - - - - - - - ###
#     STEP 6: WRITE README FILE
### - - - - - - - - - - - - - - - - - - - - - - - - ###
## Output README file with results
fYear = fileName[9:13] ; fMonth = fileName[13:15]; fDay = fileName[15:17]
fDate = fMonth+'/'+fDay+'/'+fYear
pDate = str(datetime.date.today())


intro = "DATA EXPLAINATION\nCountry-level data were exported from RepRisk's database and given to WRI on " + fDate\
    +".\nWRI's indicator is based on RepRisk's Peak RepRisk Index, and represents a"\
     +"\ncountry's highest level of criticism in the past two years. The indicator "\
      +"\nis used to gage a country's overall environmental, social, and governance "\
       +"\n(ESG)risk exposure."
proc1 = "\n\nPROCESSING STEPS\nRaw data was processed into an indicator on " + pDate
proc2 = ".\n\nRepRisk's Peak RRI data was joined to WRI's list of official countries"\
    +"\nso that it could be incorportated into the Aqueduct 3.0 database. RRI values were"\
    +"\nthen normalized along a scale from 0 to 5. Normalized scores can later be included"\
    +"\ninto WRI's overal Water Risk score. Finally, the indicator was organized into 5"\
    +"\ncategories: 'Low' exposure, 'Low - Medium' exposure, 'Medium - High' exposire, and"\
    +"'Very High' \nexposure. Category thresholds were based on RepRisk guidance (found in "\
    +"\n'The RepRisk Index: A quantitative measure of ESG risk exposure (page 3)."

readMe = intro + proc1 + proc2
readPath = open(os.path.join(finalFolder, "README.txt"),'w') # location of CSV export
readPath.write(readMe)
readPath.close()