# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 18:32:35 2013

@author: Lucio
"""
from heapq import *
#from heapL import *
import multiprocessing

class PriorityQueue():

    def __init__(self):
        self.items = {}
        self.heap = []

    def push(self, priority, item):
        heappush(self.heap, (priority, item))
        self.items[item] = priority

    def pop(self):
        priority, item = heappop(self.heap)
        self.items[item] = None
        return (priority, item)
        
    def top(self):
        priority, item = heappop(self.heap)
        heappush(self.heap, (priority,item))
        return (priority, item)

    def remove(self, item):
        priority = self.items[item]
        self.heap.remove((priority, item))
        self.items[item] = None

    def contains(self, item):
        return item in self.items.keys() and self.items[item] is not None

    def clear(self):
        self.items = {}
        self.heap = []

    def empty(self):
        return not len(self.heap)
        
    def __len__(self):
        return len(self.heap)
        
    def __str__(self):
        return str(self.heap)
