import math
from EM import EMFSD
from collections import defaultdict
import random
import sys
import hashlib

class FCMCounter():
	def __init__(self, width, size):
		self.width = int(width)
		self.counter_size = size
		self.max_range = 2**size - 2
		self.max_reg = 2**size - 1
		self.carray = [0 for i in range(self.width)]
		self.empty = width

	def increment(self, w, f=1):
		old_reg = self.carray[w]
		new_reg = old_reg + f
		new_f = 0
		if new_reg < self.max_reg:
			new_reg = new_reg 
		else:
			new_f = f - (new_reg - self.max_reg)
			new_reg = self.max_reg
		assert new_f >= 0
		self.carray[w] = new_reg
		if old_reg == 0:
			self.empty -= 1
		return new_reg, new_f

	def query(self, w):
		val_reg = self.carray[w]
		return val_reg if val_reg < self.max_range else self.max_range

	def isOverFlow(self, w):
		return self.carray[w] == self.max_reg

	def memory(self):
		# in bits
		return (len(self.carray)+2) * self.counter_size


class FCMSketch():
	def __init__(self, params, FCM_Depth=2):
		self.d = FCM_Depth
		self.FCMSK_K_POW = 3
		self.FCMSK_K_ARY = 8
		self.C1 = []
		self.C2 = []
		self.C3 = []
		self.total_memory = 0
		for i in range(FCM_Depth):
			self.C1.append(FCMCounter(params[0][0], params[0][1]))
			self.C2.append(FCMCounter(params[1][0], params[1][1]))
			self.C3.append(FCMCounter(params[2][0], params[2][1]))

			self.total_memory += self.C1[i].memory()
			self.total_memory += self.C2[i].memory()
			self.total_memory += self.C3[i].memory()

		self.cumul_l2 = 2**params[0][1] - 1
		self.cumul_l3 = self.cumul_l2 + 2**params[1][1] - 1

	def _hash(self, x):
		ans = []
		md5 = hashlib.md5(str(hash(x)).encode('utf-8'))
		for i in range(self.d):
			md5.update(str(i).encode('utf-8'))
			ans.append(int(md5.hexdigest(), 16) % self.C1[0].width)
		return ans

	def update(self, x, f=1):
		assert f >= 0
		ret_val = [0 for i in range(self.d)]
		hash_index = self._hash(x)

		for i in range(self.d):
			ret_val[i], remain = self.C1[i].increment(hash_index[i], f)
			if self.C1[i].isOverFlow(hash_index[i]):
				hash_index[i] = hash_index[i] >> self.FCMSK_K_POW
				ret_val[i], remain = self.C2[i].increment(hash_index[i])
				ret_val[i] += self.cumul_l2

				if self.C2[i].isOverFlow(hash_index[i]):
					hash_index[i] = hash_index[i] >> self.FCMSK_K_POW
					ret_val[i], remain= self.C3[i].increment(hash_index[i], remain)
					ret_val[i] += self.cumul_l3

	def query(self, x):
		ret_val = [0 for i in range(self.d)]
		hash_index = self._hash(x)
		count_query = float('inf')
		for i in range(self.d):
			ret_val[i] = self.C1[i].query(hash_index[i])
			if self.C1[i].isOverFlow(hash_index[i]):
				hash_index[i] = hash_index[i] >> self.FCMSK_K_POW
				ret_val[i] = self.C2[i].query(hash_index[i]) + self.cumul_l2

				if self.C2[i].isOverFlow(hash_index[i]):
					hash_index[i] = hash_index[i] >> self.FCMSK_K_POW
					ret_val[i] = self.C3[i].query(hash_index[i]) + self.cumul_l3;

			count_query = ret_val[i] if count_query > ret_val[i] else count_query

		return count_query

	def cardinality(self):
		avgnum_empty_counter = 0
		for i in range(self.d):
			avgnum_empty_counter += self.C1[i].empty
		if not avgnum_empty_counter:
			avgnum_empty_counter = 1
		return self.C1[0].width * math.log(1.0* self.C1[0].width * self.d / avgnum_empty_counter)

	def get_distribution(self):
		arr = [[] for i in range(self.d)]
		for i in range(self.d):
			for j in range(self.C1[i].width):
				if not self.C1[i].isOverFlow(j):
					arr[i].append(self.C1[i].query(j))
				else:
					k = j >> self.FCMSK_K_POW
					if not self.C2[i].isOverFlow(k):
						arr[i].append(self.C2[i].query(k) + self.cumul_l2)
					else:
						k = k >> self.FCMSK_K_POW
						arr[i].append(self.C3[i].query(k) + self.cumul_l3)
		distri = None
		for i in range(self.d):
			EM = EMFSD()
			EM.set_counters(len(arr[i]), arr[i])
			for epo in range(10):
				EM.next_epoch()

			if not distri:
				distri = EM.ns[:]
			else:
				for i in range(len(EM.ns)):
					if i < len(distri):
						distri[i] += EM.ns[i]
					else:
						distri += EM.ns[i:]
						break
		pmf= []
		total = sum(distri)
		for i in distri:
			pmf.append(1.0*i/total)
		return pmf
	def cdf(self):
		pmf_arr = self.get_distribution()
		quantile = [0]
		for density in pmf_arr:
			quantile.append(density+quantile[-1])
		quantile.pop(0)
		return quantile
	
	def entropy(self):
		density = self.get_distribution()
		H = 0
		m = sum(density)
		for i, n_i in enumerate(density):
			if i == 0 or n_i == 0:
				pass
			else:
				H += 1.0 * i *  (n_i / m) * math.log( 1.0 * (n_i / m))
		return -1*H










