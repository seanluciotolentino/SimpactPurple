# -*- coding: utf-8 -*-
"""
Created on Tue Aug 12 14:53:18 2014

@author: Lucio

A script to evaluate the amount of time required for 3 migrating
communities simulated with 3 nodes versus 6 nodes.

"""

from mpi4py import MPI
import simpactpurple.distributed.CommunityDistributed as CommunityDistributed
import simpactpurple.distributed.MigrationOperator as MigrationOperator
import time
import simpactpurple.GraphsAndData as gad
import numpy as np
import numpy.random
import random

def run():
    #assign roles via ranks
    if rank == 0: #Migration Operator
        mo = MigrationOperator.MigrationOperator(comm, primaries, gravity, timing)
        mo.run()
    elif rank in primaries:
        others = [[], [rank+3]][size==96]
        s = CommunityDistributed.CommunityDistributed(comm, rank, others, migration = True)
        s.INITIAL_POPULATION = int(population[rank-1])
        s.run()
    elif rank in auxiliaries and size == 96:
        s = CommunityDistributed.CommunityDistributed(comm, rank-3, [rank-3], migration = True)
        s.run()
    else:
        master = rank%(size/16)
        master = [size/16,master][master>0]
        CommunityDistributed.ServeQueue(master, comm)

#MPI variables
name = MPI.Get_processor_name()
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

#cluster set up
gravity = np.loadtxt('migration.csv', delimiter=",")[:3,:3]  # place this in your neon home directory
initial_prevalence = [0.01, 0.0, 0.0]
primaries = [1, 2, 3]
auxiliaries = [4, 5, 6]
timing = np.matrix([[1,5,5],[5,1,5],[5,5,1]])*3

for pop in range(100, 501, 100):
    population = np.array([1, 1, 1])*pop
    start = time.time()
    run()
    if rank == 0:
        print size, pop, time.time() - start