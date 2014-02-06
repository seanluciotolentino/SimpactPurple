# -*- coding: utf-8 -*-
"""
Created on Wed Feb 05 11:23:46 2014

@author: Lucio

An implementation of the approximate bayesian computation (ABC) for 
parameter inference.

"""
import Community
import GraphsAndData
import numpy as np
import numpy.random as random
from numpy.random import uniform as uni
import sys

if len(sys.argv)>=3:
    threshold = int(sys.argv[1]) # for accept function -- how close is close enough?
    n = int(sys.argv[2])  # how many data points to gather -- the larger the better
else:
    threshold = 200
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
    
def distance(s):
    """
    This is the 2nd distance function developed to be more flexible and reject
    or accept based on the total distance. 
    """
    #age disparate test
    actual = [98.0,2.0,81.4,18.5] # from SA health survey   
    simulated = map(lambda x: x*100, GraphsAndData.intergenerational_sex_data(s))
    age_disparate = sum([abs(actual[i] - simulated[i]) for i in range(len(actual))])
    
    #number of sexual partners test
    actual = [30.8,14.8,3.7, 6.0,3.0,0.8] # from SA health survey   
    simulated = map(lambda x: 100*x, GraphsAndData.number_of_partners_data(s))
    sexual_partners = sum([abs(actual[i] - simulated[i]) for i in range(len(actual))])
    
    #return result of test
    return age_disparate + sexual_partners
    
if __name__ == '__main__':
    #%% 0. Setup 
    # Every prior distribution is a uniform and given by a bottom and top
    prior = {
                1: lambda: uni(-0.01, -0.5),   # preferred age difference
                2: lambda: uni(-0.01, -0.3),   # probability multiplier
                3: lambda: uni(0.01, 2),       # preferred age difference growth
                
                4: lambda: uni(1, 4),          # desired number of partners scale
                5: lambda: uni(0, 5),          # durations expontial parameter
                6: lambda: uni(2, 10),          # durations mean age scale 
    }
    posterior = {i:[] for i in prior.keys()}
    distances = []
    
    #%% 1. Run ABC algorithm
    for i in range(n):
        #1.1 Sample and set parameters from prior distribution
        print "---Sample", i,"---"
        s = Community.Community()
        # set constants
        s.INITIAL_POPULATION = 500  # scale this up later?
        s.NUMBER_OF_YEARS = 10
        
        # set parameters
        s.preferred_age_difference = prior[1]()
        s.probability_multiplier = prior[2]()
        s.preferred_age_difference_growth = prior[3]()
        s.DNPscale = prior[4]()  # save for use building posterior distribution
        s.DNP = lambda: random.power(0.2)*s.DNPscale
        s.DURATIONSexpo = prior[5]()
        s.DURATIONSscale = prior[6]()
        s.DURATIONS = lambda a1,a2: np.mean((s.age(a1),s.age(a2)))*s.DURATIONSscale*random.exponential(s.DURATIONSexpo)
        
        #1.2 Run simulation
        s.run()        
        
        #3. Evaluate and accept/reject based on distance function
        print "  parameters"
        print "PAD_\tProbMult\tPADgrowth\tDNPscale\tDURAexpo\tDURAscale"
        print "\t".join(map(lambda x: str(round(x,2)),[s.preferred_age_difference, s.probability_multiplier, s.preferred_age_difference_growth, s.DNPscale, s.DURATIONSexpo, s.DURATIONSscale]))
        print "  intergenerational sex" 
        print "     s:", map(lambda x: round(100*x,1), GraphsAndData.intergenerational_sex_data(s))
        print "     a:", [98.0, 2.0, 81.4, 18.5]
        print "  number of partners"
        print "     s:", map(lambda x: round(100*x,1), GraphsAndData.number_of_partners_data(s))
        print "     a:", [30.8, 14.8, 3.7, 6.0, 3.0, 0.8]
        print "  distance",distance(s)
        #if accept(s):
        if distance(s)<threshold:
            print 'accepted.'
            posterior[1].append(s.preferred_age_difference)
            posterior[2].append(s.probability_multiplier)
            posterior[3].append(s.preferred_age_difference_growth)
            posterior[4].append(s.DNPscale)
            posterior[5].append(s.DURATIONSexpo)
            posterior[6].append(s.DURATIONSscale)
            distances.append(distance(s))
        else:
            print "rejected."
    
    print "===============RESULTS==============="
    print "Accepted:",len(posterior[1])
    print "Rejected:",n - len(posterior[1])
    print "Posterior:", posterior
    
    
    
    
    
