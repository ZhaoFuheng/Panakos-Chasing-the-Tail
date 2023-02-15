import sys
import math 
from EM import EMFSD
from collections import defaultdict
import collections
import matplotlib.pyplot as plt
import bisect

if len(sys.argv) < 6:
    print("Provide five arguments as file names of results: groundTruth bitmap countminTable1 countminTable2 Cocosketch")
    print("i.e python eveluate.py file1.txt file2.txt file3.txt file4.txt file5.txt")
    exit()

T = 16
convergThreshold = 10
a = 1
bitmapLen = 131072

groundTruth = sys.argv[1]
bitmap = sys.argv[2]
countmin1 = sys.argv[3]
countmin2 = sys.argv[4]
cocosketch = sys.argv[5]


f1 = open(groundTruth, "r")
f2 = open(bitmap, "r")
f3 = open(countmin1, "r")
f4 = open(countmin2, "r")
f5 = open(cocosketch, "r")

# Some Error Functions
def max_quantile_diff(q1, q2):
    i = 0
    result = 0
    while i<len(q1) and i <len(q2):
        result = max(result, abs(q1[i] - q2[i]))
        i+=1
    while i<len(q1):
        result = max(result, abs(q1[i] - q2[-1]))
        i+=1
    while i<len(q2):
        result = max(result, abs(q1[-1] - q2[i]))
        i+=1
    return result

def ARE_freq_diff(true_q, estimated_q):
    prevPhi = 0
    ans = []
    for freq, phi in enumerate(true_q):
        if freq != 0 and prevPhi != phi: # query only once for each phi
            prevPhi = phi
            estimated_freq = bisect.bisect_left(estimated_q, phi) - 1
            ans.append( abs(freq - estimated_freq) / freq)
    return 1.0 * sum(ans) / len(ans)



# Processing Ground Truth

truthdict = {}
while(True):
    line = f1.readline()
    if not line:
        break
    line = line.split()
    if line[0] in truthdict:
        truthdict[line[0]] += int(line[1])
    else:
        truthdict[line[0]] = int(line[1])

max_freq = max(truthdict.values())
true_vector = [0 for i in range(max_freq+1)]
for key, val in truthdict.items():
    true_vector[val] += 1
prev = 0
q_vector = []
for count in true_vector:
    prev += count
    q_vector.append(prev/sum(true_vector))

# Processing CocoSketch

cocoSketch = {}
while(True):
    line = f5.readline()
    if not line:
        break
    line = line.split()
    if line[0] in cocoSketch:
        cocoSketch[line[0]] += int(line[1])
    else:
        cocoSketch[line[0]] = int(line[1])

heavyFlows = defaultdict(list)
for key in cocoSketch:
    freq = cocoSketch[key]
    if freq in heavyFlows:
        heavyFlows[freq][0] += 1
    else:
        heavyFlows[freq].append(1)
    heavyFlows[freq].append(key)

maxFlow = 2+T+max(heavyFlows.keys())
ans = [0 for i in range(maxFlow + 1)]

for freq, times in heavyFlows.items():
    ans[2+T+freq] += times[0] 
heavyFlowCardinality = sum(ans)

# Processing bitmap
bitmap = []
while(True):
    line = f2.readline()
    if not line:
        break
    bitmap.append(int(line))

EM = EMFSD()
bitmap += [0]*(bitmapLen - len(bitmap))
EM.set_counters(len(bitmap), bitmap)
for epo in range(convergThreshold):
    EM.next_epoch()

cardinality = EM.card_init
ans[1] = EM.ns[1]
ans[2] = EM.ns[2]

# Processing Countmin
countminTables = [[],[]]
while(True):
    line = f3.readline()
    if not line:
        break
    countminTables[0].append(int(line))
while(True):
    line = f4.readline()
    if not line:
        break
    countminTables[1].append(int(line))

temp = []	
for table in countminTables:
    temp += list(table)
temp_dict = collections.Counter(temp)

counters = []
for freq, val in temp_dict.items():
    for i in range( math.ceil(val/2) ): # to obtain better result, use the average number of apperance
        counters.append(freq)

EM_CM = EMFSD()
EM_CM.set_counters(len(counters), counters, cardinality-ans[1]-ans[2]-heavyFlowCardinality)
for epo in range(convergThreshold):
    EM_CM.next_epoch()

CM_NS = EM_CM.ns[:]
CMCard = cardinality-ans[1]-ans[2]-heavyFlowCardinality
prevCard = sum(CM_NS)
for i in range(len(CM_NS)):
    CM_NS[i] = 1.0 * CM_NS[i] * CMCard / prevCard

for i in range(1, len(CM_NS)):
    ans[i+2] += CM_NS[i]

finalDistribution = []
for i in ans:
    finalDistribution.append(1.0*i/sum(ans))

pmf_arr = finalDistribution
quantile = [0]
for density in pmf_arr:
    quantile.append(density+quantile[-1])
quantile.pop(0)

print("Max Quantile Difference: ", max_quantile_diff(quantile, q_vector))
print("ARE Frequency Difference: ", ARE_freq_diff(quantile, q_vector))

plt.title("Zipf("+str(a)+") Stream CDF", fontsize=16) 
                
            
plt.xlabel('Frequency', fontsize=14)
plt.ylabel('Quantile', fontsize=14)

    
plt.plot([i for i in range(len(q_vector))], q_vector, label='True Distribution')   
plt.plot([i for i in range(len(quantile))], quantile, 'bv--', label='Panakos Estimate Distribution')

plt.legend(prop={ 'size': 10 })

plt.show()

plt.title("Zipf("+str(a)+") Stream CDF", fontsize=16) 
            
        
plt.xlabel('Frequency', fontsize=14)
plt.ylabel('Quantile', fontsize=14)

l = 20
r = 30


plt.plot([i for i in range(l, r)], q_vector[l:r], label='True Distribution')
    
plt.plot([i for i in range(l, r)], quantile[l:r], 'bv--', label='Panakos Estimate Distribution')

plt.show()

plt.title("Zipf("+str(a)+") Stream CDF", fontsize=16) 
            
        
plt.xlabel('Frequency', fontsize=14)
plt.ylabel('Quantile', fontsize=14)

l = len(true_vector) - 5000
r = len(true_vector)


plt.plot([i for i in range(l, r)], q_vector[l:r], label='True Distribution')
    
plt.plot([i for i in range(l, r)], quantile[l:r], 'bv--', label='Panakos Estimate Distribution')

plt.show()
