import random
import sys
import numpy as np
import seaborn as sns
import scipy.stats as stats

if len(sys.argv) < 3:
    print("Need two argumnets: outputfile, cases")
    print("i.e python create_test.py test.txt 1000000")
    exit()

outputFile = sys.argv[1]
cases = int(sys.argv[2])

# some other variables that can be changed to create 
# different kind of test cases

threshold = 5
maxCount = 60
universe = 2 ** 16
a = 1.0

# cases = int((percentage/100)*totalSize)

f = open(outputFile, "w")

range_x = np.arange(1,universe)
weights = range_x ** (-a)
weights /= weights.sum()
bounded_zipf = stats.rv_discrete(name='bounded_zipf', values=(range_x, weights))
insertions = bounded_zipf.rvs(size=cases) 

for i in insertions:
    f.write(str(i) + " 1" + "\n")

f.close()
