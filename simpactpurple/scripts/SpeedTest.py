# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 14:16:27 2013

@author: Lucio

Program for timing the execution time of SimpactPurple with clusters. Specifically,
this script should be run on the vinci cluster, but it's not appropriate for
helium.

"""

import os
import time

population_ranges = range(1000,1001,1000)
#population_ranges = range(1000,5001,1000)
#population_ranges = range(100,500,100)


#one node
print "one node, multiple communities"
for pop in population_ranges:
    break
    start = time.time()
    #success = "exit" in os.popen("mpiexec -n 5 python MainMPI.py " + str(pop)).read()
    success = "exit" in os.popen("mpiexec -n 9 python MainAlt.py " + str(pop)).read()
    print success, pop, time.time()-start

#one node
print "multiple nodes, multiple communities"
for pop in population_ranges:
    #break
    start = time.time()
    success = "exit" in os.popen("mpiexec -n 3 -host v1,v2,v3 python MainAlt.py " + str(pop)).read()
    print success, pop, time.time()-start
    
#one node
print "one node,  one community"
import Community
for pop in population_ranges:
    break
    start = time.time()
    s = Community.Community()
    s.INITIAL_POPULATION = pop
    s.run()
    print True, pop, time.time()-start
