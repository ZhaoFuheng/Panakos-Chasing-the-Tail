from EM import EMFSD
import math
import collections
from collections import defaultdict

convergThreshold = 10

'''
Original copyright notice:
	By Bob Jenkins, 1996.  bob_jenkins@burtleburtle.net.  You may use this
	code any way you wish, private, educational, or commercial.  It's free.

	See http://burtleburtle.net/bob/hash/evahash.html
	Use for hash table lookup, or anything where one collision in 2^^32 is
	acceptable.  Do NOT use for cryptographic purposes.
'''

def mix(a, b, c):
	a &= 0xffffffff; b &= 0xffffffff; c &= 0xffffffff
	a -= b; a -= c; a ^= (c>>13); a &= 0xffffffff
	b -= c; b -= a; b ^= (a<<8); b &= 0xffffffff
	c -= a; c -= b; c ^= (b>>13); c &= 0xffffffff
	a -= b; a -= c; a ^= (c>>12); a &= 0xffffffff
	b -= c; b -= a; b ^= (a<<16); b &= 0xffffffff
	c -= a; c -= b; c ^= (b>>5); c &= 0xffffffff
	a -= b; a -= c; a ^= (c>>3); a &= 0xffffffff
	b -= c; b -= a; b ^= (a<<10); b &= 0xffffffff
	c -= a; c -= b; c ^= (b>>15); c &= 0xffffffff
	return a, b, c

def jhash(data, initval = 0):
	length = lenpos = len(data)

	# empty string returns 0
	if length == 0:
		return 0

	# Set up the internal state
	a = b = 0x9e3779b9 # the golden ratio; an arbitrary value
	c = initval        # the previous hash value
	p = 0              # string offset

	# ------------------------- handle most of the key in 12 byte chunks
	while lenpos >= 12:
		a += (ord(data[p+0]) + (ord(data[p+1])<<8) + (ord(data[p+2])<<16) + (ord(data[p+3])<<24))
		b += (ord(data[p+4]) + (ord(data[p+5])<<8) + (ord(data[p+6])<<16) + (ord(data[p+7])<<24))
		c += (ord(data[p+8]) + (ord(data[p+9])<<8) + (ord(data[p+10])<<16) + (ord(data[p+11])<<24))
		a, b, c = mix(a, b, c)
		p += 12
		lenpos -= 12

	# ------------------------- handle the last 11 bytes
	c += length
	if lenpos >= 11: c += ord(data[p+10])<<24
	if lenpos >= 10: c += ord(data[p+9])<<16
	if lenpos >= 9:  c += ord(data[p+8])<<8
	# the first byte of c is reserved for the length
	if lenpos >= 8:  b += ord(data[p+7])<<24
	if lenpos >= 7:  b += ord(data[p+6])<<16
	if lenpos >= 6:  b += ord(data[p+5])<<8
	if lenpos >= 5:  b += ord(data[p+4])
	if lenpos >= 4:  a += ord(data[p+3])<<24
	if lenpos >= 3:  a += ord(data[p+2])<<16
	if lenpos >= 2:  a += ord(data[p+1])<<8
	if lenpos >= 1:  a += ord(data[p+0])
	a, b, c = mix(a, b, c)

	# ------------------------- report the result
	return c

class MRAC():
	def __init__(self, vectorLength = 1000):
		self.counters = [0 for i in range(vectorLength)]
		self.length = vectorLength
		self.streamLength = 0

	def arrLength(self):
		return self.length

	def zeroEntryRatio(self):
		dic = collections.Counter(self.counters)
		return 1.0 * dic[0] / self.length

	def insert(self, x, f=1):
		self.counters[jhash(str(x)) % self.length] += f
		self.streamLength += 1

	def space(self):
		return self.vectorLength

	def cardinality(self):
		dic = collections.Counter(self.counters)
		if 0 not in dic:
			return self.length * 10
		return self.length * math.log(1.0 * self.length / dic[0])

	def singleton(self, original = True):
		dic = collections.Counter(self.counters)
		cardinality = self.cardinality()
		single = dic[1] * math.exp( 1.0 * cardinality  / self.length)
		return single
		
	def maxFlow(self):
		return max(self.counters)

	def pmf(self):
		EM = EMFSD()
		EM.set_counters(self.length, self.counters)
		for epo in range(convergThreshold):
			EM.next_epoch()
		return EM.dist_new

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






