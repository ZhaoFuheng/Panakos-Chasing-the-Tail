from SpaceSaving import SpaceSaving
from githubCountMin import CountMinSketch
from EM import EMFSD
import math
import collections
from collections import defaultdict
from cocoSketch import CocoSketch
import hashlib
import copy
from statistics import mean


convergThreshold = 10

class Panakos():
    def __init__(self, bitVectorLength = 10000, SpaceSaving_epsilon = 1.0/500, CountMin_epsilon = 0.001, T = 17,  useSpaceSaving = True):
        self.SpaceSaving_epsilon = SpaceSaving_epsilon
        self.CountMin_epsilon = CountMin_epsilon

        self.SpaceSaving = None
        if useSpaceSaving:
            self.SpaceSaving = SpaceSaving(SpaceSaving_epsilon)
        else:
            self.SpaceSaving = CocoSketch( math.ceil(1.0/SpaceSaving_epsilon))
        self.bitmapLen = int(bitVectorLength)
        #self.bitmapLen = int(  32 / (2 * self.epsilon) )
        self.bitmap = [0 for x in range(self.bitmapLen)]
        self.countMinRows = 2
        self.CountMin = CountMinSketch(1.0/CountMin_epsilon, self.countMinRows, T-2)
        #self.CountMin = CountMinSketch( (32/math.log2(T)) / accuracy, 3)
        self.T = T
        self.dist = []

    def _hash(self, x):
        md5 = hashlib.md5(str(hash(x)).encode('utf-8'))
        return int(md5.hexdigest(), 16) % self.bitmapLen

    def update(self, x):
        bit_position = self._hash(x)
        if self.bitmap[bit_position] < 2:
            self.bitmap[bit_position] += 1
            return

        if self.bitmap[bit_position] == 2:
            # a 3 in the bitmap indicate the counter is overflowed
            self.bitmap[bit_position] += 1

        if self.CountMin.query(x) < self.T - 2:
            self.CountMin.add(x)
            return
        self.SpaceSaving.update(x)
        return

    def query(self, x):
        # return x's estimated frequency
        bit_position = self._hash(x)
        if self.bitmap[bit_position] < 3:
            return self.bitmap[bit_position]
        if 2 + self.CountMin.query(x) < self.T:
            return 2 + self.CountMin.query(x)
        return self.T + self.SpaceSaving.query(x)

    def space(self):
        # SpaceSaving + CountMin + bitVector
        # 32 bits       log(T) bits   2 bits
        # return number of 4 bytes counters.
        return math.ceil( 1.0/self.SpaceSaving_epsilon + (self.countMinRows/self.CountMin_epsilon) * math.log2(self.T-2) / 32.0 + self.bitmapLen * 2.0 / 32 )

    def spaceRatio(self):
        return (self.bitmapLen * 2.0 / 32) / self.space(),  ((self.countMinRows/self.CountMin_epsilon) * math.log2(self.T-2) / 32.0) / self.space(), (1.0/self.SpaceSaving_epsilon) / self.space()

    def cardinality(self):
        dic = collections.Counter(self.bitmap)
        return self.bitmapLen * math.log(1.0 * self.bitmapLen / dic[0])

    def singleton(self):
        dic = collections.Counter(self.bitmap)
        cardinality = self.cardinality()
        single = dic[1] * math.exp( 1.0 * cardinality / self.bitmapLen)
        return single

    def maxFlow(self):
        heavyFlows = self.SpaceSaving.WeightHashmap()
        if not heavyFlows :
            heavyFlows = {0:[0]}
        return self.T+max(heavyFlows.keys())

    def pmf(self):
        bitmap_copy = self.bitmap.copy()
        CountMin_copy = copy.deepcopy(self.CountMin)
        # obtain the tail distribution from SpaceSaving
        heavyFlows = self.SpaceSaving.WeightHashmap()
        if not heavyFlows :
            heavyFlows = {0:[0]}
        else:
            for freq, items in heavyFlows.items():
                for item in items[1:]:
                    CountMin_copy.reset(item)

        maxFlow =  self.T+max(heavyFlows.keys())
        ans = [0 for i in range(maxFlow + 1)]

        for freq, times in heavyFlows.items():
            ans[self.T+freq] += times[0] 
        heavyFlowCardinality = sum(ans)

        # capture mice flow
        EM = EMFSD()
        EM.set_counters(len(bitmap_copy), bitmap_copy)
        for epo in range(convergThreshold):
            EM.next_epoch()

        cardinality = EM.card_init
        ans[1] = EM.ns[1]
        ans[2] = EM.ns[2]


        # capture flowsize from CountMin
        dic_arrays = [None for i in range(self.countMinRows)]
        temp = 0
        for table in CountMin_copy.tables:
            dic_arrays[temp] = collections.Counter(list(table))
            temp += 1

        counters = []
        for freq in range(self.T-1):
            val = 0
            if freq  == 1 or freq == 0:
                val = max([dic[freq] for dic in dic_arrays])
            elif freq == self.T-2:
                val = min([dic[freq] for dic in dic_arrays])
            else:
                val = int(math.ceil( mean([dic[freq] for dic in dic_arrays])))
            for i in range(val): 
                counters.append(freq)

        EM_CM = EMFSD()
        EM_CM.set_counters(len(counters), counters, cardinality-ans[1]-ans[2]-heavyFlowCardinality)
        for epo in range(convergThreshold):
            EM_CM.next_epoch()
        
        CM_NS = EM_CM.ns[:]
        CMCard = cardinality-ans[1]-ans[2]-heavyFlowCardinality
        prevCard = sum(CM_NS)
        if CMCard > 0:
            for i in range(len(CM_NS)):
                CM_NS[i] = 1.0 * CM_NS[i] * CMCard / prevCard
        
        for i in range(1, len(CM_NS)):
            ans[i+2] += CM_NS[i]

        self.dist = ans.copy()

        finalDistribution = []
        for i in ans:
            finalDistribution.append(1.0*i/sum(ans))
        return finalDistribution
    
    def cdf(self):
        pmf_arr = self.pmf()
        quantile = [0]
        for density in pmf_arr:
            quantile.append(density+quantile[-1])
        quantile.pop(0)
        return quantile

    def entropy(self):
        density = self.pmf()
        H = 0
        m = sum(density)
        for i, n_i in enumerate(density):
            if i == 0 or n_i == 0:
                pass
            else:
                H += 1.0 * i *  (n_i / m) * math.log( 1.0 * (n_i / m))
        return -1*H

