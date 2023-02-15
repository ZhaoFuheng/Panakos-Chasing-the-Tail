#https://github.com/rafacarrascosa/countminsketch/blob/master/countminsketch.py
# -*- coding: utf-8 -*-
import math
import hashlib
import array

class CountMinSketch(object):
    """
    A class for counting hashable items using the Count-min Sketch strategy.
    It fulfills a similar purpose than `itertools.Counter`.
    The Count-min Sketch is a randomized data structure that uses a constant
    amount of memory and has constant insertion and lookup times at the cost
    of an arbitrarily small overestimation of the counts.
    It has two parameters:
     - `m` the size of the hash tables, larger implies smaller overestimation
     - `d` the amount of hash tables, larger implies lower probability of
           overestimation.
    An example usage:
        from countminsketch import CountMinSketch
        sketch = CountMinSketch(1000, 10)  # m=1000, d=10
        sketch.add("oh yeah")
        sketch.add(tuple())
        sketch.add(1, value=123)
        print sketch["oh yeah"]       # prints 1
        print sketch[tuple()]         # prints 1
        print sketch[1]               # prints 123
        print sketch["non-existent"]  # prints 0
    Note that this class can be used to count *any* hashable type, so it's
    possible to "count apples" and then "ask for oranges". Validation is up to
    the user.
    """

    def __init__(self, m, d, T=2**32):
        """ `m` is the size of the hash tables, larger implies smaller
        overestimation. `d` the amount of hash tables, larger implies lower
        probability of overestimation.
        """
        if not m or not d:
            raise ValueError("Table size (m) and amount of hash functions (d)"
                             " must be non-zero")
        self.m = math.ceil(m)
        self.d = d
        self.n = 0
        self.T = T
        self.tables = []
        for _ in range(d):
            table = array.array("i", (0 for _ in range(self.m)))
            self.tables.append(table)
        #print(self.tables)
    def _hash(self, x):
        md5 = hashlib.md5(str(hash(x)).encode('utf-8'))
        for i in range(self.d):
            md5.update(str(i).encode('utf-8'))
            yield int(md5.hexdigest(), 16) % self.m

    def add(self, x, value=1):
        """
        Count element `x` as if had appeared `value` times.
        By default `value=1` so:
            sketch.add(x)
        Effectively counts `x` as occurring once.
        """
        self.n += value
        for table, i in zip(self.tables, self._hash(x)):
            table[i] += value
            table[i] = min(table[i], self.T)

    def reset(self, x):
        for table, i in zip(self.tables, self._hash(x)):
            table[i] = 0

    def query(self, x):
        """
        Return an estimation of the amount of times `x` has ocurred.
        The returned value always overestimates the real value.
        """
        return min(table[i] for table, i in zip(self.tables, self._hash(x)))

    def __getitem__(self, x):
        """
        A convenience method to call `query`.
        """
        return self.query(x)

    def __len__(self):
        """
        The amount of things counted. Takes into account that the `value`
        argument of `add` might be different from 1.
        """
        return self.n
    def density(self):
        ans = 0
        for arr in self.tables:
            for i in range(self.m):
                if(arr[i] == 0):
                    #print(arr[i])
                    ans+=1
        return 1 - ans/(self.m*self.d)



        