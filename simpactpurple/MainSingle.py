# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:14:02 2013

@author: Lucio

A script which runs a single community simulation. 

"""

from mpi4py import MPI
import Community
import sys
import GraphsAndData

print "hello from", MPI.Get_processor_name(),"rank",MPI.COMM_WORLD.Get_rank()
name = MPI.Get_processor_name()

#MPI variables
if __name__ == '__main__':
    c = Community.Community()
    c.INITIAL_POPULATION = int(sys.argv[1])
    c.NUMBER_OF_YEARS = 30
    c.run()

    GraphsAndData.formed_relations_graph(c,filename='formed_relations_single.png')
    #GraphsAndData.demographics_graph(c,filename='demographics_single.png')
    #GraphsAndData.prevalence_graph(c, filename = 'prevalence_single.png')
    #GraphsAndData.age_mixing_graph(c, filename = 'agemixing_single.png')

print "exit"
