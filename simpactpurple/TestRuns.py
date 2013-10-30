# -*- coding: utf-8 -*-
"""
Created on Sun Sep 15 13:56:56 2013
s
@author: Lucio
"""

import Community
import GraphsAndData

if __name__ == '__main__':
    s = Community.Community()
    s.INITIAL_POPULATION = 100
    s.NUMBER_OF_YEARS = 1
    s.run(timing = True)

    #GRAPH VERIFICATION
#    GraphsAndData.prevalence_graph(s)
#    GraphsAndData.formed_relations_graph(s)
#    GraphsAndData.demographics_graph(s)
#    GraphsAndData.age_mixing_graph(s)
#    GraphsAndData.sexual_network_graph(s)

    GraphsAndData.prevalence_graph(s,filename='graph1.png')
    GraphsAndData.formed_relations_graph(s,filename='graph2.png')
    GraphsAndData.age_mixing_graph(s,filename='graph3.png')
    GraphsAndData.demographics_graph(s,filename='graph4.png')    
    GraphsAndData.sexual_network_graph(s,filename='graph5.png')
