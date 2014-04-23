# -*- coding: utf-8 -*-
"""
Created on Sun Sep 15 13:56:56 2013

@author: Lucio

A test script for running a single community on a signal node
with parallel grid queues. 

approximate bayesian computation -- validation. when the model is too complicated for standard bayesian approach

"""

import simpactpurple
import simpactpurple.GraphsAndData as gad

if __name__ == '__main__':
    s = simpactpurple.Community()
    s.INITIAL_POPULATION = 1000
    s.probability_multiplier = -0.2
    s.NUMBER_OF_YEARS = 1
    s.NUM_CPUS = 4
    s.BIN_SIZE = 5
    s.RECRUIT_WARM_UP = 20
    s.RECRUIT_INITIAL = 0.01
    s.RECRUIT_RATE = 0.002
    s.run(timing = True)

    #GRAPH VERIFICATION
#    gad.prevalence_graph(s)
    gad.formed_relations_graph(s)
#    gad.demographics_graph(s)
#    gad.age_mixing_graph(s)
#    gad.age_mixing_heat_graph(s)
#    gad.sexual_network_graph(s)

#    gad.prevalence_graph(s,filename='graph1.png')
#    gad.formed_relations_graph(s,filename='graph2.png')
#    gad.age_mixing_graph(s,filename='graph3.png')
#    gad.demographics_graph(s,filename='graph4.png')    
#    gad.sexual_network_graph(s,filename='graph5.png')
