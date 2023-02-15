import math
import collections
from collections import defaultdict
class BetaGenerator():
	def __init__(self, s):
		self.sum = s
		self.now_flow_num = 0
		self.flow_num_limit = 7
		if s > 50:
			self.flow_num_limit = 5
		if s > 600:
			self.flow_num_limit = 3

		self.now_result = []
	def get_new_comb(self):
		for j in range(self.now_flow_num - 2, -1, -1):
			self.now_result[j] += 1
			t = self.now_result[j]
			for k in range(j+1, self.now_flow_num-1):
				self.now_result[k] = t
			partial_sum = 0
			for k in range(0, self.now_flow_num - 1):
				partial_sum += self.now_result[k]

			remain = self.sum - partial_sum
			#print(remain, self.now_result[self.now_flow_num - 2])

			if (remain > self.now_result[self.now_flow_num - 2]):
				self.now_result[self.now_flow_num - 1] = remain
				return True
		return False
	def get_next(self):
		while (self.now_flow_num < self.flow_num_limit):
			#print("get_next", self.now_flow_num, self.flow_num_limit)
			if self.now_flow_num == 0:
				self.now_flow_num = 1
				self.now_result = [self.sum]
				return True
			elif self.now_flow_num == 1:
				self.now_flow_num = 2
				self.now_result[0] = 0
			#self.now_result = [0 for i in range(self.now_flow_num)]
			while len(self.now_result)<self.now_flow_num:
				self.now_result.append(0)
			if self.get_new_comb():
				#print("new_comb return true")
				return True
			else:
				self.now_flow_num += 1
				for i in range(self.now_flow_num-2):
					self.now_result[i] = 1
				self.now_result[self.now_flow_num - 2] = 0
			return False
	
class EMFSD():
	def __init__(self):
		self.w = 0
		self.counter_dist = []
		self.dist_old = []
		self.dist_new = []
		self.ns = []
		self.n_sum = 0
		self.card_init = 0
		self.singleton = 0
		self.inited = False
		n_old, n_new = 0, 0
		
	def set_counters(self, _w, counters, card = None):
		self.inited = True
		self.w = _w
		max_cnt = self.collect_counters(counters)
		self.n_new = self.w - self.counter_dist[0]
		
		self.dist_old = [0 for i in range(len(self.counter_dist))]
		self.dist_new = [0 for i in range(len(self.counter_dist))]
		self.ns = [0 for i in range(len(self.counter_dist))]
		
		for i in range(1, len(self.counter_dist)):
			self.dist_new[i] = 1.0 * self.counter_dist[i] / (self.w - self.counter_dist[0])
			self.ns[i] = self.counter_dist[i]
		if not card:
			try:
				self.card_init =  self.w * math.log(1.0 * self.w / self.counter_dist[0]) # linear counting method
			except:
				self.card_init = self.w * 10
		else:
			self.card_init = card
		try:
			self.singleton = abs(self.counter_dist[1] * math.log(1.0*self.card_init/self.w)) # approximate number of single flows
		except:
			self.singleton = self.w

			
	def get_p_from_beta(self, bt, lamb, now_dist, now_n):
		mp = defaultdict(int)
		for i in range(bt.now_flow_num):
			mp[bt.now_result[i]] += 1
		ret = math.exp(-1*lamb)
		for si, fi in mp.items():
			lambda_i = now_n * (now_dist[si]) / self.w
			ret *= pow(lambda_i, fi) / math.factorial(fi)
		return ret
	
	def collect_counters(self, counters):
		assert self.w == len(counters)
		max_counter_val = max(counters)
		self.counter_dist = [0 for i in range(max_counter_val + 1)]
		for i in range(self.w):
			#print(counters[i])
			self.counter_dist[counters[i]] += 1
		#print("counter_dist", self.counter_dist)
		#print("self.counter_dist 0: ", self.counter_dist[0])
		#print("maximum counter value ", max_counter_val)

		return max_counter_val
		
	def next_epoch(self):
		self.dist_old = self.dist_new
		self.n_old = self.n_new
		
		lamb = 1.0 * self.n_old / self.w
		for i in range(len(self.ns)):
			self.ns[i] = 0
		for i in range(1, len(self.counter_dist)):
			#print("in next_epoch ")
			if self.counter_dist[i] == 0:
				continue
			bts1 = BetaGenerator(i)
			bts2 = BetaGenerator(i)
			sum_p = 0
			while bts1.get_next():
				p = self.get_p_from_beta(bts1, lamb, self.dist_old, self.n_old)
				sum_p += p
				
			while bts2.get_next():
				p = self.get_p_from_beta(bts2, lamb, self.dist_old, self.n_old)
				for j in range(bts2.now_flow_num):
					self.ns[bts2.now_result[j]] += self.counter_dist[i] * p / sum_p
		n_new = 0
		for i in range(1, len(self.counter_dist)):
			n_new += self.ns[i]
		for i in range(1, len(self.counter_dist)):
			self.dist_new[i] = self.ns[i] / n_new
		self.n_sum = self.n_new  
