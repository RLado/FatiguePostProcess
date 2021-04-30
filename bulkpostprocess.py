import os
import pandas as pd
import numpy as np
import postprocess as pp

### Punts a tenir en compte:
#   La funció postprocess i bulkpostprocess han d'estar a la mateixa carpeta que la carpeta amb fitxers d'entrada.
#   El fitxer de LOADS.txt ha de contenir una columna amb noms de provetes i, separat per espai, la càrrega objectiu. 
#   Mateix ordre que crides els fitxers (això ho vull canviar)

# IMPORT .csv FILES FROM EntryFiles FOLDER
from pathlib import Path
script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
entry_file_path = os.path.join(script_dir, '1. EntryFiles')
paths = list(Path(entry_file_path).rglob('*.csv')) # 'abs_file_path' can be replaced by the absolute
# print(os.listdir(os.path.dirname(__file__))) #<--list of files in directory #debug

# CREATE NAMES LIST FROM .csv FILES
names = [] # create empty list
for i in paths:
    file_ext = os.path.basename(i)
    (file, ext) = os.path.splitext(file_ext) # separates file name and file extension
    names.append(file)
#print(names) # debug

# CREATE LIST WITH TARGET LOADS FROM A .txt FILE
rel_path = "appliedLoad.txt" # file with list of loads
load_file_path = os.path.join(script_dir, rel_path)
loads = open(load_file_path,'r') # 'load_file_path' can be replaced by the absolute
load = loads.read()
loads.close() # close opened file once it is assigned to a variable (optional)
load = load.split("\n")
#print(load) # debug

# PRUEBAS BUSCAR NOMBRE EN LOADFILE Y DEVOLVER ÍNDICE
load_list = [item.split() for item in load]
loadName = []
for i in load_list:
    loadName.extend(i)
loadName = loadName[0::2] # get the elements in the even position. start at the first element (0) and skip 1 each time
# print(loadName) # debug

# CREATE HEADERS IN RESULTS TABLE
column_names = ["specimen", "timePL", "cyclesPL", "timeYP", "cyclesYP", "timeBP", "cyclesBP"]
results = pd.DataFrame(columns=column_names)

# CALL POSTPROCESS FUNCTION AND FILL IN RESULTS TABLE
for i in range(len(names)): # range creates iterable object
    index = loadName.index(names[i].split(" ")[0]) # find the name that is being evaluated and return target load from load files
    output = pp.postprocess(os.path.join(entry_file_path,names[i]+'.csv'),os.path.join(script_dir, 'temporary.txt'),
    float(load[index].split(" ")[1]),0.01,0.05,5) #0.01 and 0.05 for all files
    # print(load[index].split(" ")[1]) # debug
    print('aqui' , output)
    preLoadData = list(map(float, output[0].split(",")))[0:2] # get first and second value
    yieldPointData = []
    for j in output[1].split(","):
        if j == '':
            yieldPointData.append('not found')
            yieldPointData.append('not found')
        else: 
            yieldPointData.append(float(j))
    yieldPointData = yieldPointData[0:2]
    breakingPointData = []
    for j in output[2].split(","):
        if j == '':
            breakingPointData.append('not found')
            breakingPointData.append('not found')
        else: 
            breakingPointData.append(float(j))
    breakingPointData = breakingPointData[0:2]
    row = [names[i].split(" ")[0]] # extract name until the first blank space
    row.extend(preLoadData) # extend te alarga la lista
    row.extend(yieldPointData)
    row.extend(breakingPointData)
    row = pd.Series(row, index=results.columns)
    results = results.append(row, ignore_index=True) # append te va añadiendo lo siguiente a nueva línea

print(results)
results.to_csv(os.path.join(script_dir, 'results.csv'))