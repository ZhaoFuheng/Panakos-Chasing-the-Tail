import math
from MRAC import jhash
from collections import defaultdict
import random
import sys
class CocoSketch():
	def __init__(self, memoryBudget, hashNum=2):
		self.hashNum = hashNum
		self.length = math.floor(memoryBudget/hashNum)
		self.stages = [[] for i in range(hashNum)]
		for i in range(len(self.stages)):
			self.stages[i] = [[None, 0] for i in range(self.length)]
		self.allQueryResult = None

	def insert(self, x, f=1):
		minimum = float('inf')
		minPos, minStage = 0, 0
		for i in range(self.hashNum):
			pos = jhash(str(x)+str(i)) % self.length
			if self.stages[i][pos][0] == x:
				self.stages[i][pos][1] += f
				return
			
			if self.stages[i][pos][1] < minimum:
				minPos = pos	
				minStage = i
				minimum = self.stages[i][pos][1]

		self.stages[minStage][minPos][1] += f

		if random.randint(1, sys.maxsize) % self.stages[minStage][minPos][1] - f < 0:
			self.stages[minStage][minPos][0] = x
		return

	def update(self, x, f = 1):
		self.insert(x, f)
		return
	
	def cdf(self):
		frequencies = defaultdict(int)
		for i in range(self.hashNum):
			for j in range(self.length):
				freq, item = self.stages[i][j][1], self.stages[i][j][0]
				frequencies[freq] += 1
		pmf = [0 for i in range(max(frequencies.keys()) + 1)]
		for freq, count in frequencies.items():
			pmf[freq] += 1
		
		result = []
		comulative_density = 0
		for density in pmf:
			comulative_density += density
			result.append(1.0 * comulative_density / sum(pmf))
		return result



	def allQuery(self):
		ans = defaultdict(int)
		for i in range(self.hashNum):
			for j in range(self.length):
				if self.stages[i][j][0]: # avoid None
					assert self.stages[i][j][0] not in ans, "I think it should not have duplicate"
					ans[self.stages[i][j][0]] = self.stages[i][j][1]
		self.allQueryResult = ans.copy()
		return ans
	
	def query(self, x):
		if not self.allQueryResult:
			self.allQuery()
		if x in self.allQueryResult:
			return self.allQueryResult[x]
		return 0

	def WeightHashmap(self):
		ans = defaultdict(list)
		for i in range(self.hashNum):
			for j in range(self.length):
				freq, item = self.stages[i][j][1], self.stages[i][j][0]
				if item:
					if freq in ans:
						ans[freq][0] += 1
					else:
						ans[freq].append(1)
					ans[freq].append(item)
		return ans




