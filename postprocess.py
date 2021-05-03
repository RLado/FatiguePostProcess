import argparse

import numpy as np


def get_minmax(filein,fileout):
    '''
    Groups all maximum and minimum data points belonging to the same cycle and 
    returns them on a new file.

    Arguments:
        filein (file descriptor): Read enabled file descriptor pointing to the 
        CSV to be processed

        fileout (file descriptor): Write enabled file descriptor to output the 
        results to

    Returns:
        None

    '''

    lfpointer=-1
    cycle=None

    while filein.tell()!=lfpointer:
        lfpointer=filein.tell()
        line=filein.readline()
        
        #Split lines by ","
        aline=line.split(',')[:-1]
        
        #Protect against empty columns
        if len(aline)!=7:
            continue
        
        #Convert strings into floating point values
        try:
            for i in range(len(aline)):
                aline[i]=float(aline[i].strip(' '))
        except ValueError:
            continue
        
        #Get max and min values for a given cycle
        if cycle==None:
            cycle_data=[aline]
       
        elif cycle!=aline[1]:
            x=tuple(zip(*cycle_data))
            
            if abs(max(x[5]))>abs(min(x[6])):
                fileout.write(','.join(str(i) for i in cycle_data[x[5].index(max(x[5]))])+'\n')
            else:
                fileout.write(','.join(str(i) for i in cycle_data[x[6].index(min(x[6]))])+'\n')
            
            cycle_data=[]
        
        else:
            cycle_data.append(aline)
        
        #Update cycle
        cycle=aline[1]

def filter_disp(filein, fileout, ple_pointer, max_diff):
    '''
    Filter data file by checking if two adjacent points of data differ by too 
    big of a difference.

    Arguments:
        filein (file descriptor): Read enabled file descriptor pointing to the 
        CSV to be processed

        fileout (file descriptor): Write enabled file descriptor to output the 
        results to

        ple_pointer (integer): File pointer to the end of the pre-load phase

        max_diff (float): Maximum difference between two adjacent points of data
        in percentage

    Returns:
        None

    '''

    filein.seek(ple_pointer, 0)

    lfpointer =- 1
    laline = None

    while filein.tell()!=lfpointer:
        lfpointer=filein.tell()
        line=filein.readline()
        
        #Split lines by ","
        aline=line.split(',')

        #Protect against empty columns
        if len(aline)!=7:
            continue
        
        #Convert strings into floating point values
        try:
            for i in range(len(aline)):
                aline[i]=float(aline[i].strip(' '))
        except ValueError:
            continue

        if laline == None:
            laline = aline
            continue

        if abs((aline[3]-laline[3])/laline[3])*100 > max_diff or abs((aline[4]-laline[4])/laline[4])*100 > max_diff:
            continue
        else:
            fileout.write(','.join(str(strline) for strline in aline)+'\n')
            laline = aline   
        
def detect_preload(filein,eLoad,eLoadTol,min_std,buffer_size=5):
    '''
    Detects preload state ending and returns a file pointer. This function first
    seeks an acceptable min_std then checks against eLoadTol.

    Arguments:
        filein (file descriptor): Read enabled file descriptor pointing to the 
        get_minmax function result

        eLoad (float): Expected load placed on the test piece

        eLoadTol (float): Tolerance on the expected load (%)

        min_std (float): Minimum standard deviation of the load considered acceptable

        buffer_size (int): Sequential buffer size to check the std and mean against

    
    Returns:
        ple_pointer (integer): File pointer to the end of the pre-load phase

    '''
    
    lfpointer=-1
    buffer=[]
    buffer_p=[] #store buffer element pointers

    while filein.tell()!=lfpointer:
        lfpointer=filein.tell()
        line=filein.readline()
        
        #Split lines by ","
        aline=line.split(',')
        #   Protect against empty columns
        if len(aline)!=7:
            continue
        
        #Convert strings into floating point values
        try:
            for i in range(len(aline)):
                aline[i]=float(aline[i].strip('\n'))
        except ValueError:
            continue
        
        buffer.append(aline)
        buffer_p.append(lfpointer)

        if len(buffer)>=buffer_size:
            x=tuple(zip(*buffer))
            
            #Positive load std
            pl_std=np.std(x[5])
            #Negative load std
            nl_std=np.std(x[6])

            #Mean pl and nl then compare
            #print('Standard deviation')
            #print(np.mean((pl_std,nl_std))) #debug
            if pl_std<min_std and nl_std<min_std:

                #Now check if the load is within tolerance margin
                pl_mean=abs(np.mean(x[5]))
                nl_mean=abs(np.mean(x[6]))
                #print('Load check')
                #print(abs(eLoad-np.mean((pl_mean,nl_mean)))*100) #debug
                #print(eLoad*eLoadTol)
                if abs(eLoad-np.mean((pl_mean,nl_mean)))<(eLoad*eLoadTol/100):

                    #Found it, now stop the search and return the current pointer
                    break
            
            #Remove first element from buffer
            buffer.pop(0)
            buffer_p.pop(0)

    #If we reach the end of the file raise an error
    if filein.tell()==lfpointer: 
        raise RuntimeError('Reached EOF while trying to detect the end of the pre-load phase')
    
    #Otherwise return the first pointer in the buffer
    else:
        return buffer_p[0] #ple_pointer

def find_disp(filein,ple_pointer,disp):
    '''
    Find the file pointer pointing to the first register that exceeds disp% 
    displacement compared to the end of the preload value.
    Arguments:
        filein (file descriptor): Read enabled file descriptor pointing to the 
        get_minmax function result
        ple_pointer (integer): File pointer to the end of the pre-load phase
        disp (float): Displacement percentage to find with respect to the end of 
        the preload value
    
    Returns:
        df_pointer (integer): Pointer pointing to the first register that exceeds 
        disp% displacement compared to the end of the preload value
    '''

    #Place the file pointer at the end of the pre-load phase
    filein.seek(ple_pointer,0)

    lfpointer=-1
    
    ref=filein.readline().split(',')
    for i in range(len(ref)):
        ref[i]=float(ref[i].strip('\n'))

    while filein.tell()!=lfpointer:
        lfpointer=filein.tell()
        line=filein.readline()
        
        #Split lines by ","
        aline=line.split(',')
        #   Protect against empty columns
        if len(aline)!=7:
            continue
        
        #Convert strings into floating point values
        try:
            for i in range(len(aline)):
                aline[i]=float(aline[i].strip('\n'))
        except ValueError:
            continue

        #Check positive displacement
        if abs(aline[3]-ref[3])/ref[3]*100>disp:
            return lfpointer
        
        #Check negative displacement
        if abs((aline[4]-ref[4])/ref[4])*100>disp:
            return lfpointer

def postprocess(path_in,tmp,eLoad,eLoadTol,min_std,buffer_size=5):
    result=[]

    with open(path_in,'r') as filein:
        with open(tmp,'w') as fileout:
            #Averaging all data points belonging to the same cycle
            get_minmax(filein,fileout)
    
    with open(tmp,'r') as filein:
        #Detect pre-load cycles
        ple_pointer=detect_preload(filein,eLoad,eLoadTol,min_std,buffer_size)
        
        #Move file pointer to ple_pointer
        filein.seek(ple_pointer,0)
        result.append(filein.readline())

        #Filter data
        with open(tmp.split('.')[0] + '_filtered.' + tmp.split('.')[1], 'w') as fileout:
            filter_disp(filein, fileout, ple_pointer, 50)
    
    with open(tmp.split('.')[0] + '_filtered.' + tmp.split('.')[1], 'r') as filein:        
        #Find yield point
        find_disp(filein,0,10)
        result.append(filein.readline())

    return(result)

if __name__=='__main__':
    #Argument parser
    parser=argparse.ArgumentParser(description='Post-process fatigue file')
    parser._action_groups.pop()
    required=parser.add_argument_group('required arguments')
    optional=parser.add_argument_group('optional arguments')

    required.add_argument('-i','--input',type=str,help='Path of the input file',required=True)
    required.add_argument('-t','--tmp',type=str,help='Path of temporal file',required=True)
    required.add_argument('-l','--load',type=float,help='Expected load placed on the test piece',required=True)
    required.add_argument('-lt','--load_tol',type=float,help='Tolerance on the expected load percentage',required=True)
    required.add_argument('-std','--std',type=float,help='Minimum standard deviation of the load considered acceptable',required=True)
    optional.add_argument('--buffer',type=int,default=5,metavar='',help='Sequential buffer size to check the std and mean against')

    args=parser.parse_args()
    
    #Config files
    #path_in='3PF_0F_A 10082020 065303_pvd.CSV'
    path_in=args.input
    tmp=args.tmp
    eLoad=args.load #expected load
    eLoadTol=args.load_tol
    min_std=args.std
    buffer_size=args.buffer
    
    with open(path_in,'r') as filein:
        with open(tmp,'w') as fileout:
            #Averaging all data points belonging to the same cycle
            get_minmax(filein,fileout)
    
    with open(tmp,'r') as filein:
        #Detect pre-load cycles
        ple_pointer=detect_preload(filein,eLoad,eLoadTol,min_std,buffer_size)
        
        #Move file pointer to ple_pointer
        filein.seek(ple_pointer,0)
        print('End of preload')
        print(filein.readline()) #debug

        #Filter data
        with open(tmp.split('.')[0] + '_filtered.' + tmp.split('.')[1], 'w') as fileout:
            filter_disp(filein, fileout, ple_pointer, 50)
    
    with open(tmp.split('.')[0] + '_filtered.' + tmp.split('.')[1], 'r') as filein:        
        #Find yield point
        find_disp(filein,0,10)
        print('Yield point (10% disp)')
        print(filein.readline()) #debug