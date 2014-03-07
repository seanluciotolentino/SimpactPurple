# -*- coding: utf-8 -*-
"""
Created on Sun Sep 15 13:56:56 2013

@author: Lucio

A test script for running a single community on a signal node
with parallel grid queues. 

approximate bayesian computation -- validation. when the model is too complicated for standard bayesian approach

"""

import Community
import GraphsAndData

if __name__ == '__main__':
    s = Community.Community()
    s.INITIAL_POPULATION = 100
    s.NUMBER_OF_YEARS = 30
    s.run(timing = True)

    #GRAPH VERIFICATION
#    GraphsAndData.prevalence_graph(s)
    GraphsAndData.formed_relations_graph(s)
#    GraphsAndData.demographics_graph(s)
#    GraphsAndData.age_mixing_graph(s)
#    GraphsAndData.sexual_network_graph(s)

#    GraphsAndData.prevalence_graph(s,filename='graph1.png')
#    GraphsAndData.formed_relations_graph(s,filename='graph2.png')
#    GraphsAndData.age_mixing_graph(s,filename='graph3.png')
#    GraphsAndData.demographics_graph(s,filename='graph4.png')    
#    GraphsAndData.sexual_network_graph(s,filename='graph5.png')
