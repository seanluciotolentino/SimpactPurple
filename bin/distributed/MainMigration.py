# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:14:02 2013

@author: Lucio

A script which uses MPI (mpi4py) to overlook several community simulations.  This
is the initial test script for proof of concept.

"""

from mpi4py import MPI
import simpactpurple.distributed.CommunityDistributed as CommunityDistributed
import simpactpurple.distributed.MigrationOperator as MigrationOperator
import simpactpurple.distributed.OperatorsDistributed as OperatorsDistributed
import sys
import simpactpurple.GraphsAndData as GraphsAndData
import numpy as np
import numpy.random as random

class MigrationModelInfectionOperator(OperatorsDistributed.InfectionOperator):
    pass
    
def role_prevalence(s, years):
    """
    Find prevalence for different roles (local women, long-distance migrant, 
    short-distance migrant, non-migrant men) at 10 years, 20 years, and max.
    """
    agents = s.agents.values()
    roles = [ 'local_women', 'short_distance_migrant', 'long_distance_migrant', 'non_migrant_men']
    den = {r:{y:0.0 for y in years} for r in roles}
    num = {r:{y:0.0 for y in years} for r in roles}
    #print s.rank,"going through",len(agents),"agents"
    for agent in agents:
        #assess agents "role"
        if agent.sex == 1:  # local women
            role = 'local_women'
        elif not hasattr(agent,'migrant'):
            role = 'non_migrant_men'
        elif agent.migrant == 2:
            role = 'short_distance_migrant'
        elif agent.migrant == 4:
            role = 'long_distance_migrant'
        else:
            print "role error: agent",agent,"migrant",agent.migrant
            
            
        #add to denominators and numerators
        ta = agent.attributes["TIME_ADDED"]
        tr = agent.attributes["TIME_REMOVED"]
        #if agent.primary == 1 and role != roles[0]:        
        #    print rank,"agent",agent.name,'ta',ta,'tr',tr,role,agent.time_of_infection,"|",
        for y in years:
            t = (y*52)-1  # convert to weeks and adjust for end of simulation off by one week
            # skip if: born after OR removed earlier
            if ta > t or tr <= t:
                continue
            
            #skip if not on this rank
            #find nearest migration timestamp
            before_time = -np.inf
            before = None           
            for timestamp in agent.attributes["MIGRATION"]:
                if timestamp[0] > before_time and timestamp[0] <= t:
                    before_time = timestamp[0]
                    before = timestamp

            #if didn't migrate here in most previous timestep
            if before[2] is not s.rank:
                continue

            #made it this far then:
            den[role][y]+=1.0
            if agent.time_of_infection <= t:
                num[role][y]+=1.0
            #    if agent.primary == 1 and role != roles[0]:
            #        print "+",t,"|",
            #elif agent.primary == 1 and role != roles[0]:
            #    print "-",t,"|",
            
        #if agent.primary == 1 and role != roles[0]: 
        #    print '< done.'

    return num, den
    #return { r:{y:round(num[r][y]/den[r][y],3) for y in years} for r in roles}
         
    
#MPI variables
name = MPI.Get_processor_name()
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#model parameters
time = 31
population = {1:1, 2: 3, 3: 3, 4:5, 5:5}  # initial population scales {rank:population}
initial_prevalence = {1:0.01, 2:0.1, 3:0, 4:0.1, 5:0}  # note that 3 and 5 don't matter...
pop = 1000
migration = 0 #0.6 # 
sexual_behavior_association = 0#1


#assign roles via ranks
if rank == 0: #Migration Operator
    mo = MigrationOperator.MigrationOperator(comm)
    mo.NUMBER_OF_YEARS = time
    mo.migration[1]['proportion'] = migration
    mo.sexual_behavior_association = sexual_behavior_association
    mo.run()
else:
    primary, others = comm.recv(source = 0)
    s = CommunityDistributed.CommunityDistributed(comm, primary, others, migration = True)
    s.INITIAL_POPULATION = pop * population[rank]
    s.INITIAL_PREVALENCE = initial_prevalence[rank]
    s.NUMBER_OF_YEARS = time
    
    #change some parameters
    #s.infection_operator = MigrationModelInfectionOperator(s)
    #s.DURATIONS = lambda a1, a2: 10
    s.PROBABILITY_MULTIPLIER = 0
    s.INFECTIVITY = 0.02
    #run the model
    s.run()
    
    #generate some output to be analyzed
    roles = [ 'local_women', 'long_distance_migrant', 'short_distance_migrant', 'non_migrant_men']
    years = np.arange(0,time,0.5)
    if rank == 2 or rank == 4:
        num,den = role_prevalence(s, years)
        comm.send((num,den), dest=1)
    if rank == 1:  # the Hlabisa community
        #grab the prevalence from other communities
        num1,den1 = role_prevalence(s, years)
        num2,den2 = comm.recv(source = 2)
        num4,den4 = comm.recv(source = 4)
        
        #avoid div by 0 error:
        for r in roles:
            for y in years:
                den1[r][y] = max((1,den1[r][y]))
                den2[r][y] = max((1,den2[r][y]))
                den4[r][y] = max((1,den4[r][y]))
        
        #define some helper functions to aggregate
        num_sum = lambda r,y: num1[r][y]+num2[r][y]+num4[r][y]
        den_sum = lambda r,y: max((1,den1[r][y]+den2[r][y]+den4[r][y]))
        total_sum = lambda r,y: num_sum(r,y)/den_sum(r,y)
        
#        print "Numerators:"
#        print '\t'.join(['year','lw','sdm','ldm','nmm','men','women','total'])
#        for y in (10,20,30):
#            print y,'\t','\t'.join([str(num_sum(r,y)) for r in roles]),
#            print '\t', str(sum([num_sum(r,y) for r in roles[1:]])),
#            print '\t', str(num_sum(roles[0],y)),
#            print '\t', str(sum([num_sum(r,y) for r in roles]))
#        print
#        
#        print "Denominators:"
#        print '\t'.join(['year','lw','sdm','ldm','nmm','men','women','total'])
#        for y in (10,20,30):
#            print y,'\t','\t'.join([str(den_sum(r,y)) for r in roles]),
#            print '\t', str(sum([den_sum(r,y) for r in roles[1:]])),
#            print '\t', str(den_sum(roles[0],y)),
#            print '\t', str(sum([den_sum(r,y) for r in roles]))
#        print

        #bar chart output
        print "Prevalence:" # local men and women are just for community 1
        print '\t'.join(['year','lw','ldm','sdm','nmm','men','women','total'])
        for y in (10,20,30):
            print y,'\t'+str(100*round(num1[roles[0]][y]/den1[roles[0]][y],3)), #local women
            print '\t','\t'.join([str(100*round(num_sum(r,y)/den_sum(r,y),3)) for r in roles[1:3]]), #migrants
            print '\t', str(100*round(num1[roles[3]][y]/den1[roles[3]][y],3)), #local non-migrant men
            print '\t', str(100*round(sum([num_sum(r,y) for r in roles[1:]])/sum([den_sum(r,y) for r in roles[1:]]),3)), #all men
            print '\t', str(100*sum([round(num_sum(r,y)/den_sum(r,y),3) for r in roles[0:1]])), #all women
            print '\t', str(100*round(sum([num_sum(r,y) for r in roles])/sum([den_sum(r,y) for r in roles]),3)) #total
        print       
        #print "total",{ r:{y:round(total_sum(r,y),3) for y in years} for r in roles}
        
        #prevalence graphs
        print
        print '\t'.join(['year','ldm','rw','rnmm'])
        for y in years:
            print y,'\t'+str(100*round(num1[roles[1]][y]/den1[roles[1]][y],3)), #long distance migrants
            print '\t'+str(100*round(num1[roles[0]][y]/den1[roles[0]][y],3)), #rural women
            print '\t'+str(100*round(num1[roles[3]][y]/den1[roles[3]][y],3)) #rural non-migrant men


