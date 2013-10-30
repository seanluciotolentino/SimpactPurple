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

#print "comm size",comm.Get_size()
#Simulation variables (set it Global struct)
Global = Global.Global(comm, int(sys.argv[1]))

#split actions based on rank
if rank == 0:
    # Run main simulator
    Global.run()
    print rank,"exiting"   
else:
    # Make and run a community
    Community = CommunityMPI.CommunityMPI(comm, Global)
    Community.run()
    print rank,"exiting"
    
    #display stuff
#    import GraphsAndData
#    GraphsAndData.formed_relations_graph(Community,filename='formed_relations.'+str(rank)+'.png')
#    GraphsAndData.age_mixing_graph(Community,filename='age_mixing.'+str(rank)+'.png')
#    GraphsAndData.demographics_graph(Community,filename='demographics.'+str(rank)+'.png')
#    GraphsAndData.prevalence_graph(Community,filename='prevalence.'+str(rank)+'.png')
    
    #write relationship files
#    f = open('output/relationships.'+str(rank)+'.out','w')
#    for relationship in Community.relationships:
#        agent1, agent2, start, end = relationship  # unpack
#        male = [agent1, agent2][agent1.gender]
#        female = [agent1, agent2][agent2.gender]
#        mx,my = male.attributes["LOC"][0]
#        fx,fy = female.attributes["LOC"][0]
#        f.write(str(male.attributes["NAME"])+","+str(mx)+","+str(my)+","+\
#                str(female.attributes["NAME"])+","+str(fx)+","+str(fy)+","+\
#                str(start)+","+str(end)+"\n")
#    f.close()
    
    #write population files
#    f = open('output/population.'+str(rank)+'.out','w')
#    for agent in Community.agents.values():
#        x,y = agent.attributes["LOC"][0]
#        f.write(str(agent.attributes["NAME"])+","+str(agent.gender)+","+str(x)+","+str(y)+"\n")
#    f.close()
    
