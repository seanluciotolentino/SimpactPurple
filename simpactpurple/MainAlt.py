# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:14:02 2013

@author: Lucio

A script which uses MPI (mpi4py) to overlook several community simulations.  This
is the initial test script for proof of concept.

"""

from mpi4py import MPI
import GlobalAlt
import CommunityAlt
import GridServer
import sys

#MPI variables
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#Simulation variables set it Global struct
Global = GlobalAlt.Global(comm)
if len(sys.argv)>1:  # doing an intersection test
    Global.INITIAL_POPULATION = int(sys.argv[1])
if len(sys.argv)>2:  # doing an intersection test
    Global.INTERSECTION = float(sys.argv[2])
#print "hello from", comm.Get_rank(),"on",MPI.Get_processor_name()
#split actions based on rank
if rank == 0:
    # Run main simulator
    Global.run()
else:
    #have Global send a role and location
    role = comm.recv(source = 0)
    #print rank, " was assigned to be", role
    if role == "community":
        c = CommunityAlt.CommunityAlt(comm, Global)    
        
        #add additional grids of queues
        msg = comm.recv(source = 0)
        while msg != 'run':
            #print rank, "has new servant:",msg
            c.servants.append(msg)  # msg is the rank of a grid queue for c to use
            msg = comm.recv(source = 0)
                    
        #print rank, "is running..."
        c.run()
        
#        import GraphsAndData
#        GraphsAndData.formed_relations_graph(c,filename='formed_relations.'+str(rank)+'.png')
#        GraphsAndData.age_mixing_graph(c,filename='age_mixing.'+str(rank)+'.png')
#        GraphsAndData.demographics_graph(c,filename='demographics.'+str(rank)+'.png')
#        GraphsAndData.prevalence_graph(c,filename='prevalence.'+str(rank)+'.png')         
        
    elif role == "grid":
        gs = GridServer.GridServer(comm)        
        gs.master = comm.recv(source = 0)
        #print rank, "has new master:", gs.master
        msg = comm.recv(source = gs.master)
        while msg != 'run':
            gs.add_grid_queue(msg)
            msg = comm.recv(source = gs.master)
        #print rank, "is running..."
        gs.run()
    else:
        raise ValueError, "Role not known: " + role

print rank,"exiting" 
