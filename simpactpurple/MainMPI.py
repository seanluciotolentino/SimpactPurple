# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:14:02 2013

@author: Lucio

A script which uses MPI (mpi4py) to overlook several community simulations.  This
is the initial test script for proof of concept.

"""

from mpi4py import MPI
import CommunityMPI
import Global
import sys

#MPI variables
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#Simulation variables set it Global struct
Global = Global.Global(comm, int(sys.argv[1]))

#split actions based on rank
if rank == 0:
    # Run main simulator
    Global.run()
else:
    # Make and run a community
    Community = CommunityMPI.CommunityMPI(comm, Global)
    Community.run()
    
    #display stuff
    #    import GraphsAndData
    #    GraphsAndData.formed_relations_graph(Community,filename='formed_relations.'+str(rank)+'.png')
    #    GraphsAndData.age_mixing_graph(Community,filename='age_mixing.'+str(rank)+'.png')
    #    GraphsAndData.demographics_graph(Community,filename='demographics.'+str(rank)+'.png')
    #    GraphsAndData.prevalence_graph(Community,filename='prevalence.'+str(rank)+'.png')

print rank,"exiting" 
