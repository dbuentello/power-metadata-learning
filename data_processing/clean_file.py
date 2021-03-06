#the goal of this file is to take a tab separated output file from the SQL database
#then store it in a numpy array.

#it should be cleaned such that data appears every second

#it will be stored such that data is 24 hour aligned

import numpy as np
import sys
import argparse
from datetime import datetime, date, timedelta


parser = argparse.ArgumentParser(description='Process data input files')
parser.add_argument('inputfile', metavar='I', type=str, nargs='+',
                    help='input file to parse')
parser.add_argument('outputfile', metavar='O', type=str, nargs='+',
                    help='output file to save')
parser.add_argument('id', metavar='O', type=int, nargs='+',
                    help='id of device')

args = parser.parse_args()

#open the input file
reportFname = args.outputfile[0][:-3] + 'rpt'
infile = open(args.inputfile[0],'r')
report = open(reportFname,'w')

#figure out how long the input file is to create a numpy array for it
infile.readline()
time1 = infile.readline().split('\t')[1]

infile.seek(-100,2)
line = infile.readlines()
time2 = line[-1].split('\t')[1]

#no calculate the number of days of data we need
time_start = datetime.strptime(time1,"%Y-%m-%d %H:%M:%S")
time_end = datetime.strptime(time2,"%Y-%m-%d %H:%M:%S")

#round the first day back to midnight
end_start_day = time_start.replace(hour = 0, minute = 0, second = 0)

#round the end time up to the second before midnight
end_end_day = time_end.replace(hour=23,minute=59,second=59)

#now subtract the two days
difference = end_end_day - end_start_day
size_of_array = difference.total_seconds() + 1

daysdiff = difference + timedelta(seconds=1)

print "Cleaning ID {} with {} days of data from {} to {}".format(args.id,daysdiff.days,end_start_day.strftime("%Y-%m-%d %H:%M:%S"),end_end_day.strftime("%Y-%m-%d %H:%M:%S"))
print "{} total data points".format(size_of_array)

#make a numpy array
array_to_store = np.zeros((int(size_of_array),2))

#seek back to beginning of file
infile.seek(0)
infile.readline()

#find the first date that matches the start date
last_time = None
last_seq = None
it = 0

seq,time,power,pf = infile.readline().split('\t')
time = datetime.strptime(time,"%Y-%m-%d %H:%M:%S")

td = timedelta(seconds=0)

while(end_start_day + td < time):
    td = td + timedelta(seconds=1)
    it = it+1

last_time = time
last_seq = int(seq)
array_to_store[it,0] = float(power)
array_to_store[it,1] = float(pf)

interpolated = 0
off = 0
skipped = 0
for line in infile:
	seq,time,power,pf = line.split('\t')
	time = datetime.strptime(time,"%Y-%m-%d %H:%M:%S")
        
        if(time > end_end_day):
            #we are done
            break;

	time_diff = time-last_time
        if(last_seq <= int(seq)):
            seq_diff = int(seq)-last_seq
        else:
            #we have probably wrapped
            #or we have been off for a long period of time
            seq_diff = -1

        diff = time-last_time
	if(diff.total_seconds() == 1):
	    #everything is fine
	    array_to_store[int(it),0] = float(power)
	    array_to_store[int(it),1] = float(pf)
	    it = it+1
	elif(diff.total_seconds() < 1):
	    #just ignore this point
            if(seq_diff == 1):
                pass
            else:
                skipped = skipped + 1
	else:
            if(diff.total_seconds() < 20):
	        sec = diff.total_seconds()
                
	        for i in range(0,int(sec)):
	        	newit = it+i
	        	array_to_store[int(newit),0] = float(power)
	        	array_to_store[int(newit),1] = float(pf)

                interpolated = interpolated + sec

	        it = it+sec
            else:
                sec = diff.total_seconds()
	        for i in range(0,int(sec)):
	        	newit = it+i
	        	array_to_store[int(newit),0] = 0
	        	array_to_store[int(newit),1] = 0
	        it = it+sec
                off = off + sec

	last_time = time
        last_seq = int(seq)

print "Interpolated {} data points".format(interpolated)
print "Off {} data points".format(off)
print "Skipped {} data points".format(skipped)
np.save(args.outputfile[0],array_to_store)	

report.write("{},{},{}%,{}%,{}%\n".format(args.id[0],difference.days,int(float(interpolated)/size_of_array*100),int(float(off)/size_of_array*100),int(float(skipped)/size_of_array*100)))
