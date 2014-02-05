# -*- coding: utf-8 -*-
"""
Created on Wed Feb 05 11:23:46 2014

@author: Lucio

An implementation of the approximate bayesian computation (ABC) for 
parameter inference.

"""
import Community
import GraphsAndData
import numpy.random as random
from numpy.random import uniform as uni
import sys

if len(sys.argv)>=3:
    threshold = sys.argv[1] # for accept function -- how close is close enough?
    n = sys.argv[2]  # how many data points to gather -- the larger the better
else:
    threshold = 20
    n = 10

def accept(s):
    """
    This is the distance function which represents how far from real life 
    the simulation *s* is. It returns a boolean accept/reject (1 = accept,
    0 = reject) based on age-disparate relationships and number of sexual
    partners.
    """
    #age disparate test
    actual = [98.0,2.0,81.4,18.5] # from SA health survey   
    simulated = map(lambda x: x*100, GraphsAndData.intergenerational_sex_data(s))
    age_disparate = all([abs(actual[i] - simulated[i])<threshold for i in range(len(actual))])
    
    #number of sexual partners test
    actual = [30.8,14.8,3.7, 6.0,3.0,0.8] # from SA health survey   
    simulated = map(lambda x: 100*x, GraphsAndData.number_of_partners_data(s))
    sexual_partners = all([abs(actual[i] - simulated[i])<threshold for i in range(len(actual))])
    
    #return result of test
    return age_disparate and sexual_partners

if __name__ == '__main__':
    #%% 0. Setup 
    # Every prior distribution is a uniform and given by a bottom and top
    prior = {
                1: lambda: uni(-0.01, -0.5),   # preferred age difference
                2: lambda: uni(-0.01, -0.3),   # probability multiplier
                3: lambda: uni(0.01, 2),       # preferred age difference growth
                
                4: lambda: uni(1, 4),          # desired number of partners scale
    }
    posterior = {i:[] for i in prior.keys()}
    
    #%% 1. Run ABC algorithm
    for i in range(n):
        #1.1 Sample and set parameters from prior distribution
        print "---Sample", i,"---"
        s = Community.Community()
        # set constants
        s.INITIAL_POPULATION = 200  # scale this up later?
        s.NUMBER_OF_YEARS = 10
        s.DURATIONS = lambda: 104*random.exponential(0.9)
        
        # set parameters
        s.preferred_age_difference = prior[1]()
        s.probability_multiplier = prior[2]()
        s.preferred_age_difference_growth = prior[3]()
        s.DNPscale = prior[4]()  # save for use building posterior distribution
        s.DNP = lambda: random.power(0.2)*s.DNPscale
        
        #1.2 Run simulation
        s.run()        
        
        #3. Evaluate and accept/reject based on distance function
        print "  parameters", s.preferred_age_difference, s.probability_multiplier, s.preferred_age_difference_growth, s.DNPscale
        print "  intergenerational sex", map(lambda x: 100*round(x,2), GraphsAndData.intergenerational_sex_data(s))
        print "  number of partners", map(lambda x: 100*round(x,2), GraphsAndData.number_of_partners_data(s))
        if accept(s):
            print 'accepted.'
            posterior[1].append(s.preferred_age_difference)
            posterior[2].append(s.probability_multiplier)
            posterior[3].append(s.preferred_age_difference_growth)
            posterior[4].append(s.DNPscale)
        else:
            print "rejected."
                
    print posterior
    
    
    
    
    
