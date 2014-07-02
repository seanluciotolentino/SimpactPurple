# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:14:02 2013

@author: Lucio

A script which uses MPI (mpi4py) to overlook several community simulations.  This
is the initial test script for proof of concept.

"""

from mpi4py import MPI
import simpactpurple.distributed.CommunityDistributed as CommunityDistributed
import simpactpurple.distributed.MigrationOperator as MigrationOperator
import sys
import simpactpurple.GraphsAndData as GraphsAndData
import numpy as np
import numpy.random
import random

def run(who, where, when):
    #use parameters in the model:
    proportion_migrate = [who, 0, 0]  # who migrates
    gravity = [[0.0, 0.0, 0.0],
                [where, 0.0, 0.0],
                [1-where, 0.0, 0.0]]       # where they migrate
    timing = [[0, when, when],
              [when, 0, 0],
              [when, 0, 0]]          # how long they migrate for

    #assign roles via ranks
    others = [[oindex for oindex, other in enumerate(primaries) if oindex!=pindex and other==primary ] for pindex, primary in enumerate(primaries)]
    if rank == 0: #Migration Operator
        mo = MigrationOperator.MigrationOperator(comm, primaries, proportion_migrate, gravity, timing)
        mo.NUMBER_OF_YEARS = time
        mo.run()
        
        #grab prevalence from communities
        prev1 = round(comm.recv(source = 1),3)
        prev2 = round(comm.recv(source = 2),3)
        prev4 = round(comm.recv(source = 4),3)
        print i,who,where,when,prev1, prev2, prev4
    else:
        s = CommunityDistributed.CommunityDistributed(comm, primaries[rank], others[rank], migration = True)
        s.INITIAL_POPULATION = population[rank]
        s.INITIAL_PREVALENCE = initial_prevalence[rank]
        s.SEED_TIME = 0
        s.NUMBER_OF_YEARS = time
        
        #change some parameters
        #s.DURATIONS = lambda a1, a2: 10
        s.PROBABILITY_MULTIPLIER = 0
        s.INFECTIVITY = 0.01
        #s.MAX_AGE = 35  # to limit the number of grid queues spawned while v's are down
        #run the model
        s.run()
        
        #generate some output to be analyzed
        if s.is_primary:
            #print rank, "prevalence", [round(p, 2) for p in GraphsAndData.prevalence_data(s)[::52]]
            comm.send(GraphsAndData.prevalence_data(s)[-1], dest = 0)

#MPI variables
name = MPI.Get_processor_name()
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#simulation parameters
time = 30
pop = 1000
runs = 10

#cluster set up
population = np.array([0, 1, 3, 0, 5, 0])*pop #note that population size for non-primary doesn't matter
initial_prevalence = [0, 0.01, 0.1, 0, 0.1, 0]
primaries = [0, 1, 2, 2, 4, 4]

#do the runs
for i in range(runs):
    #generate random parameters and share
    who = round(numpy.random.rand(), 2)
    where = round(numpy.random.rand(), 2)
    when = random.choice(range(5,50,5))
        
    run(who, where, when)
