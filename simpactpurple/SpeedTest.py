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
import matplotlib
if os.popen("echo $DISPLAY").read().strip() == '':  # display not set
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys
sys.path.append(os.pardir)


population_ranges = range(1000,5001,1000)
#population_ranges = range(100,501,100)


print "multiple nodes, multiple communities"
multiple = []
for pop in population_ranges:
    #break
    start = time.time()
    success = "exit" in os.popen("mpiexec -n 2 -host v2,v3 python MainDistributed.py " + str(pop)).read()
    elapsed_time = time.time() - start
    print success, pop, elapsed_time
    multiple.append(elapsed_time)
    
print "one node,  one community"
single = []
import Community
for pop in population_ranges:
    #break
    start = time.time()
    s = Community.Community()
    s.INITIAL_POPULATION = pop
    s.run()
    elapsed_time = time.time() - start
    print True, pop, elapsed_time
    single.append(elapsed_time)

#make a nice graph
plt.ioff()
fig = plt.figure()
plt.plot(population_ranges, multiple)
plt.plot(population_ranges, single)
plt.xlabel('Population size')
plt.ylabel('Elapsed time (s)')
plt.title('Run time comparison')
plt.savefig('SpeedTests.png')
plt.close(fig)
