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

class MigrationModelInfectionOperator(OperatorsDistributed.InfectionOperator):
    pass
    


#MPI variables
name = MPI.Get_processor_name()
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#model parameters
time = 1
population = {1:1, 2: 10, 3: 0, 4:5, 5:0}  # initial population scales {rank:population}
pop = 300

#assign roles via ranks
if rank == 0: #Migration Operator
    mo = MigrationOperator.MigrationOperator(comm)
    mo.NUMBER_OF_YEARS = time
    mo.run()
else:
    primary, others = comm.recv(source = 0)
    s = CommunityDistributed.CommunityDistributed(comm, primary, others, migration = True)
    s.INITIAL_POPULATION = pop * population[rank]
    s.NUMBER_OF_YEARS = time
    
    #change some parameters
    s.infection_operator = MigrationModelInfectionOperator(s)
    s.PROBABILITY_MULTIPLIER = 0
    s.DURATIONS = lambda a1, a2: np.mean((s.age(a1),s.age(a2)))*random.exponential(5)
    
    
    s.run()


