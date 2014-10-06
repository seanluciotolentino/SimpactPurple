# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:14:02 2013

@author: Lucio

A script to evaluate the amount of time required for various population 
sizes and various numbers of nodes. 

"""

from mpi4py import MPI
import simpactpurple.distributed.CommunityDistributed as CommunityDistributed
import simpactpurple.distributed.MigrationOperator as MigrationOperator
import time
import simpactpurple.GraphsAndData as gad
import numpy as np
import numpy.random
import random

def run(population):
    #assign roles via ranks
    if rank < num_communities:
        s = CommunityDistributed.CommunityDistributed(comm, 0, [o for o in range(num_communities) if o!=rank])
        s.INITIAL_POPULATION = population
        s.run()
    else:
        master = rank%num_communities
        CommunityDistributed.ServeQueue(master, comm)

#MPI variables
name = MPI.Get_processor_name()
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
num_communities = comm.Get_size()/16

for pop in range(10000, 50001, 10000):
    start = time.time()
    run(pop)
    if rank == 0:
        print num_communities, pop, time.time() - start