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
    if rank in primaries:
        others = [[], [rank+3]][size==96]
        op = [p for p in primaries if p != rank]
        s = CommunityDistributed.CommunityDistributed(comm, rank, others, 
                    other_primaries = op, timing = timing, gravity = gravity)
        s.INITIAL_POPULATION = pop
        s.NUMBER_OF_YEARS = 30
        s.INITIAL_PREVALENCE = initial_prevalence[rank]
        s.SEED_TIME = 0
        s.run()
        #gad.prevalence_graph(s, filename='prevalence{0}.png'.format(rank))
    elif rank in auxiliaries and size == 96:
        s = CommunityDistributed.CommunityDistributed(comm, rank-3, [rank-3], 
                    other_primaries = [], timing = timing, gravity = gravity)
        s.run()
    else:
        master = rank%(size/16)
        CommunityDistributed.ServeQueue(master, comm)

#MPI variables
name = MPI.Get_processor_name()
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

#cluster set up
gravity = np.loadtxt('migration.csv', delimiter=",")[:3,:3]  # place this in your neon home directory
gravity = np.power(gravity, 0.01) # increase migration dramatically for debugging
initial_prevalence = [0.0, 0.0, 0.1]
primaries = [0, 1, 2]
auxiliaries = [3, 4, 5]
timing = np.matrix([[1,5,5],[5,1,5],[5,5,1]])*3

for pop in range(10000, 100001, 10000):
    start = time.time()
    run()
    if rank == 0:
        print size, pop, time.time() - start
        