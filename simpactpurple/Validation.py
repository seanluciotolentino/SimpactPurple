# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 11:47:47 2014

@author: Lucio
"""
import Community
import GraphsAndData
import numpy as np
import numpy.random as random
import matplotlib.pyplot as plt

if __name__ == '__main__':
    #%% 0. VALIDATION PARAMETERS    
    number_of_replications = 1
    
    #%%  1. MAKE SIMULATIONS    
    simulations = []
    for i in range(number_of_replications):
        print "replication",i
        s = Community.Community()
        s.INITIAL_POPULATION = 200  # scale this up later
        s.NUMBER_OF_YEARS = 5.1
        
        #parameters
        s.preferred_age_difference = -0.13#-0.1
        s.probability_multiplier = -0.27#-0.1
        s.preferred_age_difference_growth = 0.21#5
        
        #s.DURATIONS = lambda: 104*random.exponential(0.9)
        s.DURATIONSexpo = 0.9
        s.DURATIONSscale = 20
        s.DURATIONS = lambda a1,a2: np.mean((s.age(a1),s.age(a2)))*s.DURATIONSscale*random.exponential(s.DURATIONSexpo)
        s.DNP = lambda: random.power(0.2)*(2)
        
        s.run()
        simulations.append(s)
    
    ## 2. MAKE FIGURES
    #%% Figure 1 -- Prevalence    
#    plt.ion()
#    plt.figure()
#    
#    #actual
#    plt.plot([0.2, 0.5, 1.0, 1.9, 3.1, 4.8, 6.7, 8.8, 10.8, 12.6, 14.1, 15.3,
#              16.1, 16.6, 16.9, 17.1, 17.2, 17.3, 17.5, 17.6, 17.6, 17.8, 
#              17.9])  # Spectrum adult prevalence data, 1990-2012, 2013 UNAIDS Global Report
#    
#    #simulated
#    prevalence_cloud = np.array([GraphsAndData.prevalence_data(simulations[0])[0::52]])*100
#    plt.plot(prevalence_cloud[0], '0.75')
#    for s in simulations[1:]:
#        prev = [GraphsAndData.prevalence_data(s)[0::52]*100]
#        prevalence_cloud = np.append(prevalence_cloud, prev, axis=0)
#        plt.plot(prev[0], '0.75')
#    plt.plot(np.mean(prevalence_cloud, axis=0),'r')
#    
#    #graph options
#    plt.title("HIV Prevalence")
#    plt.xlabel("Time (years)")
#    plt.ylabel("HIV Prevalence (%)")
#    
    #%% Figure 2 -- Actual versus Simulated
    plt.ion()
    plt.figure()
    nrows = 3
    ncols = 2
    
    #Age-Mixing
    #actual
    plt.subplot(nrows,ncols,1)
    agemixing = np.transpose(np.loadtxt('C:\Users\Lucio\Dropbox\My Documents\Research\Fast HIV Simulations\Data\DataAgeMixing.csv', delimiter=","))
    plt.scatter(agemixing[0], agemixing[1], color='b')
    plt.plot((15,65),(15,65),'r')  # red line for "perfect mixing"
    plt.xlim(15, 65)
    plt.ylim(15, 65)
    plt.title("Actual", fontsize='16')
    plt.xlabel("Male Age")
    plt.ylabel("Female Age")
    #simulated
    plt.subplot(nrows,ncols,2)
    agemixing = GraphsAndData.age_mixing_data(simulations[0])
    plt.scatter(agemixing[0], agemixing[1], color='g')
    plt.plot((15,65),(15,65),'r')  # red line for "perfect mixing"
    plt.xlim(15, 65)
    plt.ylim(15, 65)
    plt.title("Simulated", fontsize='16')
    plt.xlabel("Male Age")
    plt.ylabel("Female Age")
    
    #    #Relationship Duration
    #    #actual
    #    plt.subplot(4,2,3)
    #    durations = np.transpose(np.loadtxt('C:\Users\Lucio\Dropbox\My Documents\Research\Fast HIV Simulations\Data\DataDurations.csv', delimiter=","))
    #    plt.hist(durations, color = 'b')
    #    plt.title("Relationship Durations")
    #    plt.xlabel("Relationship Duration (weeks)")
    #    plt.ylabel("Frequency")    
    #    #simulated
    #    plt.subplot(4,2,4)
    #    plt.hist([r[3]-r[2] for r in s.relationships], color='g')
    #    plt.title("Relationship Durations")
    #    plt.xlabel("Relationship Duration (weeks)")
    #    plt.ylabel("Frequency")
    
    #AgeDisparate Relationships
    #actual
    plt.subplot(nrows,ncols,3)
    xpos = [1,2,4,5]
    ypos = [98.0,2.0,81.4,18.5] # from SA health survey   
    rects = plt.bar(xpos, ypos, width=1, color=[(0.0,0.0,0.2),(0.3,0.3,1.0),(0.0,0.0,0.2),(0.3,0.3,1.0)])
    plt.xticks(xpos,["","Male","","Female"])
    plt.yticks(range(0,150,20),['0', '20', '40', '60', '80', '100', '',''] )
    plt.ylim(0,150)
    plt.ylabel("Had relationship type (%)")
    plt.legend((rects[0],rects[1]),("Within 5 years of own age", "Partner is 5+ years older"))
    xoffset = 0.4
    yoffset = 0.5
    for i in range(len(xpos)):
        plt.text(xpos[i]+xoffset, ypos[i]+yoffset,str(ypos[i]))
    #simulated
    plt.subplot(nrows,ncols,4)
    xpos = [1,2,4,5]
    ypos = map(lambda x: 100*round(x,2)+0.01, GraphsAndData.intergenerational_sex_data(s))  # +0.01 b/c matplotlib doesn't want to plot zero values
    rects = plt.bar(xpos, ypos, width=1, color=[(0.0,0.2,0.0),(0.3,1.0,0.3),(0.0,0.2,0.0),(0.3,1.0,0.3)])
    plt.xticks(xpos,["","Male","","Female"])
    plt.yticks(range(0,150,20),['0', '20', '40', '60', '80', '100', '',''] )
    plt.ylim(0,150)
    plt.ylabel("Had relationship type (%)")
    plt.legend((rects[0],rects[1]),("Within 5 years of own age", "Partner is 5+ years older"))
    for i in range(len(xpos)):
        plt.text(xpos[i]+xoffset, ypos[i]+yoffset,str(ypos[i]))
    
    #Number of Sexual Partners
    #actual
    plt.subplot(nrows,ncols,5)
    xpos = [1,2,3, 5,6,7]  # male, female
    ypos = [30.8,14.8,3.7, 6.0,3.0,0.8] # from SA health survey   
    xoffset = 0.3
    yoffset = 0.4
    rects = plt.bar(xpos, ypos, width=1, color=[(0.0,0.0,0.2),(0.1,0.1,0.5),(0.3,0.3,1.0),
                                                (0.0,0.0,0.2),(0.1,0.1,0.5),(0.3,0.3,1.0)])
    plt.xticks([2.5,6.5],["Male","Female"])
    plt.yticks(range(0,150,20),['0', '20', '40', '60', '80', '100', '',''] )
    plt.ylim(0,40)
    plt.ylabel("More than one partner (%)")
    plt.legend((rects[0],rects[1],rects[2]),("15-24","25-49",">50"))
    for i in range(len(xpos)):
        plt.text(xpos[i]+xoffset, ypos[i]+yoffset,str(ypos[i]))
    #simulated
    plt.subplot(nrows,ncols,6)
    xpos = [1,2,3, 5,6,7]  # male, female
    ypos = map(lambda x: 100*round(x,2)+0.01, GraphsAndData.number_of_partners_data(s))  # +0.01 b/c matplotlib doesn't want to plot zero values
    rects = plt.bar(xpos, ypos, width=1, color=[(0.0,0.2,0.0),(0.1,0.5,0.1),(0.3,1.0,0.3),
                                                (0.0,0.2,0.0),(0.1,0.5,0.1),(0.3,1.0,0.3)])
    plt.xticks([2.5,6.5],["Male","Female"])
    plt.ylim(0,40)
    plt.ylabel("More than one partner (%)")
    plt.legend((rects[0],rects[1],rects[2]),("15-24","25-49",">50"))
    for i in range(len(xpos)):
        plt.text(xpos[i]+xoffset, ypos[i]+yoffset,str(ypos[i]))
    
    






