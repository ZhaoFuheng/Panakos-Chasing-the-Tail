from collections import defaultdict
import random
import math
class SpaceSaving():
    def __init__(self, epsilon = 0.01, unbiased = False, universe = 2**16):
        self.epsilon = epsilon
        self.unbiased = unbiased
        self.k = math.ceil(1.0 / epsilon)
        self.size = 0
        self.weight_heap = [] # Min heap
        self.item_to_indices = defaultdict(list)
        self.universe = universe
        self.total_items = 0
        
    def fillPercent(self):
        return len(self.weight_heap) / self.k
    
    def parent(self, i):
        return (i-1)//2
    def left(self, i): 
        return 2*i + 1
    def right(self, i):
        return 2*i + 2
    def isFull(self):
        return self.size == self.k
    def isEmpty(self):
        return self.size==0
    
    def swap(self, tuple_x, tuple_y):

        x, x_val = tuple_x
        y, y_val = tuple_y      
        
        x_weight_index = self.item_to_indices[x]
        y_weight_index = self.item_to_indices[y]

        self.weight_heap[x_weight_index] = tuple_y
        self.weight_heap[y_weight_index] = tuple_x
        self.item_to_indices[x] = y_weight_index
        self.item_to_indices[y] = x_weight_index

        
        x_weight_index = self.item_to_indices[x]
        y_weight_index = self.item_to_indices[y]
        
        assert self.weight_heap[x_weight_index][0] == x
        assert self.weight_heap[y_weight_index][0] == y
            
            
    
    def insertUnmonitored(self, item, val=1):
        assert item not in self.item_to_indices
        
        arr = self.weight_heap
        self.item_to_indices[item] = len(arr) # the item will be append to the end of the array
        arr.append([item, val])
        index = len(arr) - 1
        while index!=0 and arr[self.parent(index)][1] > arr[index][1]:
            self.swap(arr[self.parent(index)], arr[index])
            index = self.parent(index)
        return
            
    def updateMonitored(self, item, val = 1):
        assert item in self.item_to_indices

        arr = self.weight_heap
        index = self.item_to_indices[item]
        arr[index][1] += val
        while self.left(index) < self.size:
            smallest_child_index = self.left(index)
            if self.right(index) < self.size and arr[self.right(index)][1] < arr[smallest_child_index][1]:
                smallest_child_index = self.right(index)
            if arr[index][1] > arr[smallest_child_index][1]:
                self.swap(arr[index], arr[smallest_child_index])
                index = smallest_child_index
            else:
                return
        
    def update(self, x, val=1):
        self.total_items += val
        if x in self.item_to_indices:
            self.updateMonitored(x, val)
        else:
            if self.size < self.k:
                assert(val > 0)
                self.size += 1
                self.insertUnmonitored(x, val)
            else:
                if val > 0:
                    # replace min
                    min_item, min_weight = self.weight_heap[0]
                    assert self.item_to_indices[min_item] == 0
                    # replace min item by the new item x
                    self.updateMonitored(min_item, val)
                    weight_index = self.item_to_indices[min_item]
                    assert self.weight_heap[weight_index][0] == min_item
                    self.weight_heap[weight_index][0] = x
                    del self.item_to_indices[min_item]
                    self.item_to_indices[x] = weight_index
        return
              
    def query(self, x, strictNoUnderestimate = False):
        """
        Return an estimation of the amount of times `x` has ocurred.
        """
        if x in self.item_to_indices:
            pos = self.item_to_indices[x]
            return self.weight_heap[pos][1]
        if strictNoUnderestimate:
            return self.weight_heap[0][1]
        return 0

    def __getitem__(self, x):
        """
        A convenience method to call `query`.
        """
        return self.query(x)
    
    def space(self):
        return self.k   
    
    def WeightHashmap(self):
        ans = defaultdict(list)
        for item, freq in self.weight_heap:
            if freq in ans:
                ans[freq][0] += 1
            else:
                ans[freq].append(1)
            ans[freq].append(item)
        return ans
    
    def ItemFreq(self):
        ans = {}
        for item, freq in self.weight_heap:
            ans[item] = freq
        return ans

