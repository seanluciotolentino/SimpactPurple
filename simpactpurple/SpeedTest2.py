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

population_ranges = range(1000,5001,1000)
#population_ranges = range(100,501,100)
mult_ranges = [-0.01, -0.1, -0.5]

print "multiple nodes"
print "\t"," #\t\t".join([str(m) for m in mult_ranges])
for pop in population_ranges:
    break
    print pop,
    for mult in mult_ranges:
        start = time.time()
        num_rela = os.popen("mpiexec -n 2 -host v2,v3 python MainDistributed.py "\
                + str(pop) + " " + str(mult)).read().strip()
        elapsed_time = round(time.time() - start,2)
        print "\t",elapsed_time, num_rela,
    print
    
print
print "single node"
print "\t"," #\t\t".join([str(m) for m in mult_ranges])
import Community
for pop in population_ranges:
    #break
    print pop,
    for mult in mult_ranges:
        start = time.time()
        s = Community.Community()
        s.INITIAL_POPULATION = pop
        s.probability_multiplier = mult
        s.run()
        elapsed_time = round(time.time() - start,2)
        print "\t",elapsed_time, len(s.network.edges()),
    print
