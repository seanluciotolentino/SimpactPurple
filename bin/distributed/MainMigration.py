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
import simpactpurple.distributed.OperatorsDistributed as OperatorsDistributed
import sys
import simpactpurple.GraphsAndData as GraphsAndData
import numpy as np
import numpy.random as random      
    
#MPI variables
name = MPI.Get_processor_name()
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#simulation parameters
time = 30
pop = 10
population = np.array([0, 1, 2, 0, 5, 0])*pop #note that population size for non-primary doesn't matter
initial_prevalence = [0, 0.1, 0.1, 0, 0.1, 0]

#migration / community parameters
primaries = [0, 1, 2, 2, 4, 4]
proportion_migrate = [0, 0.6, 0, 0, 0, 0]  # who migrates
distance = [[1.0, 3.0, 4.0],
            [3.0, 1.0, 5.0],
            [4.0, 5.0, 1.0]]       # where they migrate
timing = [[1, 3, 4],
          [3, 1, 5],
          [4, 5, 1]]          # how long they migrate for

#assign roles via ranks
others = [[oindex for oindex, other in enumerate(primaries) if oindex!=pindex and other==primary ] for pindex, primary in enumerate(primaries)]
if rank == 0: #Migration Operator
    mo = MigrationOperator.MigrationOperator(comm, primaries, proportion_migrate, distance, timing)
    mo.NUMBER_OF_YEARS = time
    mo.run()
else:
    s = CommunityDistributed.CommunityDistributed(comm, primaries[rank], others[rank], migration = True)
    s.INITIAL_POPULATION = population[rank]
    s.INITIAL_PREVALENCE = initial_prevalence[rank]
    s.SEED_TIME = 0
    s.NUMBER_OF_YEARS = time
    
    #change some parameters
    #s.DURATIONS = lambda a1, a2: 10
    s.PROBABILITY_MULTIPLIER = 0
    s.INFECTIVITY = 0.5
    #s.MAX_AGE = 35  # to limit the number of grid queues spawned while v's are down
    #run the model
    s.run()
    
    #generate some output to be analyzed
    print rank, "prevalence", GraphsAndData.prevalence_data(s)