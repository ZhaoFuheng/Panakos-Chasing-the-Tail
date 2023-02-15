from MRAC import jhash
from EM import EMFSD
import math
from collections import defaultdict
import heapq

convergThreshold = 10

class lightPart():
	def __init__(self, length):
		self.mice_dist = [0 for i in range(256)]
		self.length = length
		self.counters = [0 for i in range(length)]

	def insert(self, x, f=1):
		pos = jhash(str(x)) % self.length
		old_val = self.counters[pos]
		new_val = self.counters[pos] + f

		if new_val > 255:
			new_val = 255
		self.counters[pos] = new_val
		if old_val != 0:
			self.mice_dist[old_val]-=1
		self.mice_dist[new_val]+=1

	def swap_insert(self, x, f):
			pos = jhash(str(x)) % self.length

			if f > 255:
				f = 255
			if self.counters[pos] < f:
				old_val = self.counters[pos]
				self.counters[pos] = f
				new_val = f
				if old_val != 0:
					self.mice_dist[old_val]-=1
				self.mice_dist[new_val]+=1

	def query(self, x):
		pos = jhash(str(x)) % self.length
		return self.counters[pos]

	def get_memory_usage(self):
		return self.length* math.log2(256) / 32

	def cardinality(self):
		mice_card = 0
		for i in range(1, 256):
			mice_card += self.mice_dist[i]
		if mice_card == self.length:
			mice_card = self.length - 1
		rate = 1.0 * (self.length - mice_card) / self.length
		return self.length * math.log(1.0/rate)

	def distribution(self):
		EM = EMFSD()
		EM.set_counters(len(self.mice_dist), self.mice_dist[:])
		for epo in range(convergThreshold):
			EM.next_epoch()
		return EM.ns

class bucket():
	def __init__(self, rate_threshold = 8, size = 8):
		self.dic = defaultdict(list) # positive count and flag
		self.limit = size
		self.currSize = 0
		self.negativeVote = 0
		self.threshold = rate_threshold

	def find(self, x):
		return x in self.dic
	
	def isFull(self):
		return self.currSize == self.limit

	def query(self,x):
		return self.dic[x][0]

	def flag(self,x):
		return self.dic[x][1]
	
	def insert(self, x, f=1):
		if x in self.dic:
			self.dic[x][0] += f
			return None, None
		if not self.isFull():
			self.currSize += 1
			self.dic[x] = [f,0] # freq of f and flag is 0
			return None, None

		self.negativeVote += f
		minFreq = float('inf')
		minItem = None
		for item, arr in self.dic.items():
			if minFreq > arr[0]:
				minFreq = arr[0]
				minItem = item
		rate = 1.0*self.negativeVote/minFreq

		if rate < self.threshold:
			return None, f
		else:
			self.negativeVote = 0
			del self.dic[minItem]
			self.dic[x] = [f, 1] # freq of f and flag is 1 which indicate eviction happened
			return minItem, minFreq



class ElasticSketch():
	def __init__(self, bucketNum, countMinLength, rate_threshold = 8):
		self.length = bucketNum
		self.map = []
		for i in range(bucketNum):
			self.map.append( bucket(rate_threshold) )

		self.threhsold = rate_threshold
		self.lightPart = lightPart(countMinLength)

	def insert(self, x, f=1):
		pos = jhash(str(x)) % self.length
		
		item, freq = self.map[pos].insert(x)

		if item == None and freq != None:
			self.lightPart.insert(x, freq)
		elif item != None and freq != None:
			self.lightPart.swap_insert(item, freq)

	def query(self, x):
		pos = jhash(str(x)) % self.length
		if not self.map[pos].find(x) : 
			return self.lightPart.query(x)

		if self.map[pos].flag(x) == 0: # flag == 0 indicate no error
			return self.map[pos].query(x)

		return self.map[pos].query(x) + self.lightPart.query(x)

	def space(self):

		return self.lightPart.get_memory_usage() + self.length * self.map[0].limit

	def maxFlow(self):
		ans = 0
		for bucket in self.map:
			for item in bucket.dic.keys():
				freq = self.query(item)
				ans = max(ans, freq)
		return ans

	def cdf(self):
		density = self.pmf()
		cdf = []
		temp = 0
		for d in density:
			temp += d
			cdf.append(1.0*temp/sum(density))
		return cdf

	def pmf(self):
		density = self.lightPart.distribution()
		for bucket in self.map:
			for item in bucket.dic.keys():
				val = bucket.query(item)
				ex_val = self.lightPart.query(item)
				if bucket.flag(item) and ex_val != 0 and ex_val < len(density) and density[ex_val] > 0:
					val += ex_val
					density[ex_val] -= 1

				while len(density) <= val:
					density.append(0)
				try:
					density[val] += 1
				except:
					print(density, len(density), val)
					print("error!!!")
		return density

	def entropy(self):
		density = self.pmf()
		H = 0
		m = sum(density)
		for i, n_i in enumerate(density):
			if i <= 0 or n_i <= 0:
				pass
			else:
				H += 1.0 * i *  (n_i / m) * math.log( 1.0 * (n_i / m))
		return -1*H

	def cardinality(self):
		card = self.lightPart.cardinality()

		for bucket in self.map:
			for item in bucket.dic.keys():
				
				val = bucket.query(item)
				ex_val = self.lightPart.query(item)

				if bucket.flag(item) and ex_val != 0:
					val += ex_val
					card -= 1

				card += 1

		return card














