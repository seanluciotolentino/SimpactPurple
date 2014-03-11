# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:14:02 2013

@author: Lucio

A script which uses MPI (mpi4py) to overlook several community simulations.  This
is the initial test script for proof of concept.

"""

from mpi4py import MPI
import CommunityDistributed
import MigrationOperator
import sys

print "hello from", MPI.Get_processor_name(),"rank",MPI.COMM_WORLD.Get_rank()

#MPI variables
name = MPI.Get_processor_name()
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#simulation variables
if len(sys.argv)>1: pop = sys.argv[1]
else: 
    pop = 200
    print "Using default population size:",pop
    
if len(sys.argv)>2: time = sys.argv[2]
else: 
    time = 30
    print "Using default number years:",time

if rank == 0: #Migration Operator
    mo = MigrationOperator.MigrationOperator(comm)
    mo.NUMBER_OF_YEARS = time
    mo.run()
else:
    primary, others = comm.recv(source = 0)  # does this need to be blocking?
    c = CommunityDistributed.CommunityDistributed(comm, primary, others)
    c.INITIAL_POPULATION = pop
    c.NUMBER_OF_YEARS = time
    c.run()


print "exit"
