# -*- coding: utf-8 -*-
"""
Created on Wed Feb 05 11:23:46 2014

@author: Lucio

An implementation of the approximate bayesian computation (ABC) for 
parameter inference. Writes to a file parameter, simulation output for those
parameters, and their distance to the survey data. Processing of the file
is performed by another script, ABCOutputProcessing.

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
    threshold = 500
    n = 20

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
    or accept based on the total distance. Hardcoded numbers are from SA health
    survey.
    """
    # 1. Intergenerational Sex
    age_disparate = 0
    
    # 1.1 2005
    actual = [98.0,2.0,81.4,18.5]  # male partner within 5 years, male partner 5+ years, female partner within 5 years, female partner 5+ years, 
    simulated = map(lambda x: x*100, GraphsAndData.intergenerational_sex_data(s, year=s.NUMBER_OF_YEARS-3))
    age_disparate += sum([abs(actual[i] - simulated[i]) for i in range(len(actual))])
    
    # 1.2 2008
    actual = [98.5,0.7,72.4,27.6]
    simulated = map(lambda x: x*100, GraphsAndData.intergenerational_sex_data(s, year=s.NUMBER_OF_YEARS-0))
    age_disparate += sum([abs(actual[i] - simulated[i]) for i in range(len(actual))])
    
    # 2. Multiple Sexual Partners    
    sexual_partners = 0
    
    # 2.1 2002
    actual = [23.0,11.5,7.5,8.8,2.5,0.6] # male15-24,male25-49,male50+,female15-24,female25-49,female50+
    simulated = map(lambda x: 100*x, GraphsAndData.number_of_partners_data(s, year = s.NUMBER_OF_YEARS-6))
    sexual_partners += sum([abs(actual[i] - simulated[i]) for i in range(len(actual))])
    
    # 2.2 2005
    actual = [27.2,14.4,9.8,6.0,1.8,0.3]
    simulated = map(lambda x: 100*x, GraphsAndData.number_of_partners_data(s, year = s.NUMBER_OF_YEARS-3))
    sexual_partners += sum([abs(actual[i] - simulated[i]) for i in range(len(actual))])
    
    # 2.3 2008
    actual = [30.8,14.8,3.7, 6.0,3.0,0.8]
    simulated = map(lambda x: 100*x, GraphsAndData.number_of_partners_data(s, year = s.NUMBER_OF_YEARS-0))
    sexual_partners += sum([abs(actual[i] - simulated[i]) for i in range(len(actual))])    

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
    
    #file to write
    f = open('ABCoutput.csv','w')
    f.write("#,ProbMult, PAD, PADgrowth, DNPscale, DURAexpo, DURAscale,")  # parameters
    f.write("NonInterMale05,InterMale05,NonInterFemale05,InterFemale05,")  # intergernational sex 2005
    f.write("NonInterMale08,InterMale08,NonInterFemale08,InterFemale08,")  # intergernational sex 2008
    
    f.write("MP15-24Male02,MP15-24Female02,MP25-49Male02,MP25-49Female02,MP50+Male02,MP50+Female02,")  # multiple partners 02
    f.write("MP15-24Male05,MP15-24Female05,MP25-49Male05,MP25-49Female05,MP50+Male05,MP50+Female05,")  # multiple partners 05
    f.write("MP15-24Male08,MP15-24Female08,MP25-49Male08,MP25-49Female08,MP50+Male08,MP50+Female08,")  # multiple partners 08
    
    f.write("distance,")
    f.write("accept?\n")
    
    #%% 1. Run ABC algorithm
    for i in range(n):
        #1.1 Sample and set parameters from prior distribution
        print "---Sample", i,"---"
        s = Community.Community()
        # set constants
        s.INITIAL_POPULATION = 500  # scale this up later?
        s.NUMBER_OF_YEARS = 15
        
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
        
        #1.3 Save to csv
        f.write(str(i) + ",")
        f.write(",".join(map(lambda x: str(round(x,2)),[s.probability_multiplier,
                             s.preferred_age_difference, s.preferred_age_difference_growth,
                             s.DNPscale, s.DURATIONSexpo, s.DURATIONSscale]))+",")
        
        f.write(",".join(map(lambda x: str(round(100*x,1)), GraphsAndData.intergenerational_sex_data(s, year = s.NUMBER_OF_YEARS-3)))+",")  # 2005
        f.write(",".join(map(lambda x: str(round(100*x,1)), GraphsAndData.intergenerational_sex_data(s, year = s.NUMBER_OF_YEARS-0)))+",")  # 2008
        
        f.write(",".join(map(lambda x: str(round(100*x,1)), GraphsAndData.number_of_partners_data(s, year = s.NUMBER_OF_YEARS-6)))+",")  # 2002
        f.write(",".join(map(lambda x: str(round(100*x,1)), GraphsAndData.number_of_partners_data(s, year = s.NUMBER_OF_YEARS-3)))+",")  # 2005
        f.write(",".join(map(lambda x: str(round(100*x,1)), GraphsAndData.number_of_partners_data(s, year = s.NUMBER_OF_YEARS-0)))+",")  # 2008       
        
        f.write(str(distance(s))+",")
        f.write(str(int(distance(s)<threshold))+"\n")
        
    # end abc for-loop    
    f.close()  
    
    
    

