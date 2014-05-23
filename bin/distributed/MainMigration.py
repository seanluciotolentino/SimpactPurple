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

#MPI variables
name = MPI.Get_processor_name()
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#simulation variables
if len(sys.argv)>1:
    pop = int(sys.argv[1])
else: 
    pop = 200
    print "Using default population size:",pop
    
if len(sys.argv)>2:
    time = float(sys.argv[2])
else: 
    time = 30
    print "Using default number years:",time

#assign roles via ranks
if rank == 0: #Migration Operator
    mo = MigrationOperator.MigrationOperator(comm)
    mo.NUMBER_OF_YEARS = time
    mo.run()
else:
    primary, others = comm.recv(source = 0)
    s = CommunityDistributed.CommunityDistributed(comm, primary, others, migration = True)
    s.INITIAL_POPULATION = pop
    s.NUMBER_OF_YEARS = time
    s.community_multipier = 0.2
    s.run()
    
    if comm.Get_rank() == 1:
        GraphsAndData.formed_relations_graph(s, filename='3formedrelations.png')
        print s.infection_operator.number_infected
#    	GraphsAndData.formed_relations_graph(c,filename='formed_relations'+str(c.rank)+'.png')
#    	GraphsAndData.demographics_graph(c,filename='demographics'+str(c.rank)+'.png')
#    	GraphsAndData.prevalence_graph(c,filename='prevalence'+str(c.rank)+'.png')

