# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:14:02 2013

@author: Lucio

A script which uses MPI (mpi4py) to overlook several community simulations.  This
is the initial test script for proof of concept.


Migration info from StatsSA:

http://www.statssa.gov.za/publications/P03014/P030142011.pdf (page 26)
matrix([[5158316,	40152,	10566,	5155,	9221,	5039,	50694,	4759,	3381],	
        [170829,	6250135,	5081,	15542,	73831,	32341,	117964,	12001,	8877],	
        [17577,	4077,	1054841,	8559,	5708,	11478,	16019,	4202,	1907],	
        [12644,	8155,	7103,	2524282,	8881,	24090,	74387,	10859,	5283],	
        [21857,	19178,	2437,	11481,	9812129,	8655,	184337,	28904,	4719],	
        [6013,	3085,	17000,	9917,	3882,	3146255,	103550,	8495,	14066],	
        [74915,	40161,	9446,	31455,	55620,	75260,	10416258,	61269,	54145],	
        [7256,	3390,	1932,	5032,	12511,	13091,	122578,	3723843,	25299],	
        [7826,	2742,	1847,	5481,	4574,	26826,	283495,	39492,	5088084]])

#some commands that might helpful:
gravity = gravity.astype(float)
probabilities = gravity / np.sum(gravity, axis=0)
np.set_printoptions(precision=3, linewidth=150)


"""

from mpi4py import MPI
import simpactpurple.distributed.CommunityDistributed as CommunityDistributed
import simpactpurple.distributed.MigrationOperator as MigrationOperator
import simpactpurple.GraphsAndData as gad
import numpy as np

def run(gravity, power):
    #assign roles via ranks
    if rank == 0: #Migration Operator
        gravity = np.power(gravity, power)
        mo = MigrationOperator.MigrationOperator(comm, primaries, gravity, timing)
        mo.NUMBER_OF_YEARS = time
        mo.run()
        
        #grab messages from communities
        prev = [comm.recv(source = r) for r in primaries]
        print power," ".join(map(lambda p: " ".join(map(str,p)),prev))
    elif rank in primaries:
        s = CommunityDistributed.CommunityDistributed(comm, rank, [], migration = True)
        s.INITIAL_POPULATION = int(population[rank-1])
        s.INITIAL_PREVALENCE = initial_prevalence[rank-1]
        s.SEED_TIME = 0
        s.NUMBER_OF_YEARS = time
        #s.DURATIONS = lambda a1, a2: 10
        #s.SEX = lambda: int(random.random() > 0.35)
        s.INFECTIVITY = 0.01
        s.PROBABILITY_MULTIPLIER = 0
        s.run()
        
        #generate some output to be analyzed
        if s.is_primary:
            comm.send(gad.prevalence_data(s)[::52*5], dest = 0)
    else:
        master = rank%(comm.Get_size()/16)
        master = [3,master][master>0]
        s = CommunityDistributed.QueueServer(master, comm)
        s.run()

#MPI variables
name = MPI.Get_processor_name()
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#simulation parameters
time = 31
num_runs = 20
num_communities = 3
fraction = 1.0 / 1000

#cluster set up
migration = np.loadtxt('migration.csv', delimiter=",")  # place this in your neon home directory
gravity = migration[:3,:3]
population = np.array([migration[i,i] for i in range(num_communities)])*fraction
initial_prevalence = [0.05, 0, 0]
primaries = [1, 2, 3]
timing = np.matrix([[1,3,5],[3,1,4],[5,4,1]])*5  # make a constant

#run it
for i in range(num_runs):            
    #normal migration
    run(gravity, 1.0)
    
    #less migration
    run(gravity, 2.0)
    
    #more migration
    run(gravity, 0.5)
    
    #a lot more migration
    run(gravity, 0.1)
