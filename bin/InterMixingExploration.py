# -*- coding: utf-8 -*-
"""
Created on Wed May 14 11:38:20 2014

@author: Lucio

Script to explore intermixing between several communities. If run on milano,
the script repeatedly makes a call to MainInterMixing and saves the output
 to a file. If run on slim, read the output file and make some pretty graphs.

"""
import numpy as np
import random
import os
import json
import matplotlib.pyplot as plt
import time

if os.popen("echo $DISPLAY").read().strip() == '':  # display not set (running on milano)
    #simulation parameters
    years = 15
    runs = 10
    
    #define parameter space
    pop_range = [1000, 2000, 3000, 4000, 5000]
    mult_range = np.arange(-8.0, 0.1, 0.5)
    np.append(mult_range, -0.2)
    nodes_range = np.arange(1, 8)

    #prepare file for writing
    files = os.popen('ls').read().split('\n')[:-1]
    if 'InterMixingExploration.csv' in files:
        f = open('InterMixingExploration.csv','a')
        print "Appending to existing..."
    else:
        f = open('InterMixingExploration.csv','w')
        f.write('#population,distance multiplier,number communities,')  # input
        f.write('on node relations, off node relations, inter node relations, total relationships,')
	f.write('one infected, total infected,')
        f.write('average attenuation, total attenuation, probability of intercommunity relationship,')
        f.write('total_time\n')
		
        f.write('#0,1,2,3,4,5,6,7,8,9,10,11,12\n')
        
    #do the runs
    for i in range(runs):
        #choose input
        pop = random.choice(pop_range)
        mult = random.choice(mult_range)
        n = random.choice(nodes_range)
        
        #run the simulation
        print i, "running nodes",n,"min_",mult,"==>",
        start = time.time()
        output = os.popen('mpiexec -n {0} -host v1,v2,v3,v4,v5 python\
            bin/distributed/MainInterMixing.py {1} {2} {3}'.format(n, pop, years, mult))\
            .read().strip()
        total_time = time.time() - start
        output = json.loads(output)
        print output['all_infected']
        
        #save the output
        f.write(",".join(map(str,(pop, mult, n)))+",")  # write input parameters
        f.write(",".join(map(str,(output['on_node_relationships'], # write output
                                  output['off_node_relationships'],
                                  output['inter_node_relationships'],
                                  output['total_relationships'],
								  
                                  output['one_infected'], 
                                  output['all_infected'],
								  
                                  output['average_attenuation'],
                                  output['total_attenuation'],
                                  output['inter_community_probability'],
								  
                                  total_time,
                                  )))+'\n')
    f.close()
else:  # running on slim
    #load data:
    print "making graphs..."
    plt.close('all')
    #data = np.loadtxt('C:\Users\Lucio\Desktop\SimpactPurple\InterMixingExploration.csv', delimiter=",")
    data = np.loadtxt('/mnt/nfs/netapp2/grad/stolenti/SimpactPurple/InterMixingExploration.csv', delimiter=",")
    #data = data[np.random.random(len(data))<0.8,:]
    print "data shape:",np.shape(data)
    data = np.append(np.transpose(data), [data[:,5]-data[:,4]-data[:,3]], axis=0)  # calculate num "internode" relations
    data = np.append(data, [data[9]/data[5]], axis=0)  # calculate % internode
    plt.ioff()

    #define indexes
    population = 0
    dist_mult = 1
    num_communities = 2
    on_node_rela = 3
    off_node_rela = 4
    total_rela = 5
    infected = 6
    #all_infections = 7
    avg_att = 7
    total_att = 8
    inter_node_rela = 9
    inter_percent = 10

    # 1 -- visualizing the distance multiplier
##    plt.figure(1)
##    plt.plot(np.arange(0,1,0.01), np.exp(-0.01*np.arange(0,1,0.01)))
##    plt.plot(np.arange(0,1,0.01), np.exp(-0.5*np.arange(0,1,0.01)))
##    plt.plot(np.arange(0,1,0.01), np.exp(-1*np.arange(0,1,0.01)))
##    plt.plot(np.arange(0,1,0.01), np.exp(-2*np.arange(0,1,0.01)))
##    plt.plot(np.arange(0,1,0.01), np.exp(-4*np.arange(0,1,0.01)))
##    plt.plot(np.arange(0,1,0.01), np.exp(-8*np.arange(0,1,0.01)))
##    plt.legend((-0.01,-0.5,-1,-2,-4,-8))
##    plt.xlabel('Euclidean Distance btwn communities')
##    plt.ylabel('Attenuation')
##    plt.title('Scales for different distance multipliers')
    
##    # 2 -- sanity check graphs
##    plt.figure()
##    plt.scatter(data[num_communities] + (0.5 - np.random.random(np.shape(data[num_communities]))), data[avg_att], c=data[num_communities], s=50, linewidth=0)
##    plt.xlabel('number of communities')
##    plt.ylabel('average attenuation')
##    plt.title('Color: number communities')
##    plt.colorbar(ticks=range(1,8))
##
##    plt.figure()
##    plt.scatter(data[num_communities] + (0.5 - np.random.random(np.shape(data[num_communities]))), data[avg_att], c=data[dist_mult], s=50, linewidth=0)
##    plt.xlabel('number of communities')
##    plt.ylabel('average attenuation')
##    plt.title('Color: distance multiplier')
##    plt.colorbar()
##    
##    plt.figure()
##    plt.scatter(data[dist_mult] + (0.5 - np.random.random(np.shape(data[dist_mult]))),data[inter_percent],c=data[num_communities],linewidth=0)
##    plt.xlabel('probability multiplier')
##    plt.ylabel('% relationships inter-community')
##    plt.title('Color: Number of communities')
##    plt.colorbar(ticks=range(1,8))

    # 3 -- number of relationships versus number of infected (scatter plots with curvy arrow)
    plt.figure()
    #data = data[:,data[num_communities,:]>1]
    plt.suptitle("Color: num communities")
    #plt.suptitle("Color: Average Att")
    #plt.suptitle("Color: % inter-community relationship")
    color =   num_communities  #avg_att # inter_node_rela # inter_percent # on_node_rela
    for i,pop in enumerate(range(1000,5001,1000)):
        plt.subplot(2,3,i+1)
	d = data[:,data[0,:]==pop]
	plt.title('population = {0}'.format(pop))

        plt.scatter(d[total_rela], d[infected], c=d[color], linewidth=0)
        plt.xlabel('number relationships')
        plt.ylabel('number infected')
        #plt.colorbar(ticks=range(1,8))
        plt.colorbar()

	#add to last one
	plt.subplot(2,3,6)
	plt.scatter(d[total_rela], d[infected], c=d[color], linewidth=0)
    plt.xlabel('number relationships')
    plt.ylabel('number infected')
    #plt.colorbar(ticks=range(1,8))
    plt.colorbar()    
    # 4 -- inputs predicting number relationships / infected (bar charty)
##    noise = 300
##    a = 1
##    response = 3 #5   3-- number of relationships, 5 -- number of infections
##    plt.figure()
##    plt.scatter(data[population]+np.random.randint(-noise,noise,size=np.shape(data[population])),data[response], alpha=a,c=data[avg_att], linewidth=0)
##    plt.ylabel('number relationships')
##    plt.xlabel('population')
##    plt.title("Color: avg attenuation")
##    plt.colorbar()
##
##    plt.figure()
##    plt.scatter(data[population]+np.random.randint(-noise,noise,size=np.shape(data[population])),data[response], c=data[num_communities], alpha=a,linewidth=0)
##    plt.ylabel('number relationships')
##    plt.xlabel('population')
##    plt.title("Color: number of communities")
##    plt.colorbar(ticks=range(1,8))
##
##    plt.figure()
##    plt.scatter(data[population]+np.random.randint(-noise,noise,size=np.shape(data[population])),data[response], c=data[total_att], alpha=a,linewidth=0)
##    plt.ylabel('number relationships')
##    plt.xlabel('population')
##    plt.title("Color: total ttenuation")
##    plt.colorbar(ticks=range(1,8))

    # 5 -- % off node relationships and the attenuation (loner guy)
##    plt.figure(7)    
##    #plt.scatter(data[dist_mult] +(0.5 - np.random.random(np.shape(data[dist_mult]))),data[on_node_rela]/data[total_rela], c=data[num_communities], linewidth=0)
##    plt.scatter(data[num_communities] +(0.5 - np.random.random(np.shape(data[num_communities]))),data[on_node_rela], c=data[population], linewidth=0)
##    plt.xlabel('Number of Communities')
##    plt.ylabel('Number of on-node relationships')
##    plt.title('Color: population')
##    #plt.ylim(0,1)
##    #plt.xlim(-8,0.1)
##    plt.colorbar()
    
##    # 6.1  -- attenuation and % inter-node relationships
##    plt.figure(8)
##    markers = ('o', 'v', 's', 'h', 'D', 'd')
##    explanatory = total_att #avg_att
##    response = inter_percent
##    for i,pop in enumerate(range(1000,5001,1000)):
##        plt.subplot(2,3,i+1)
##        d = data[:,data[0,:]==pop]
##        plt.scatter(np.log(d[explanatory]), d[response], c=d[num_communities], marker=markers[i], alpha=0.75, linewidth=0)
##        plt.title('pop = {0}'.format(pop))
##        plt.xlabel('log(total attenuation)')
##        plt.ylabel('% inter-node relationships')
##        plt.colorbar(ticks=range(1,8))
##        #plt.colorbar()
##
##        #add it to the last plot too
##        plt.subplot(2,3,6)
##        plt.scatter(np.log(d[explanatory]), d[response], c=d[num_communities], s=d[infected]/5, marker=markers[i], alpha=0.5, linewidth=0)
##    plt.colorbar(ticks=range(1,8))
##    #plt.colorbar()
##    plt.xlabel('log(total attenuation)')
##    plt.ylabel('% inter-node relationships')
##    plt.title('Color: # communities, Size: # infections')
    
    #loop through all variables and plot all relationships
##    var = ['population', 'distance multiplier', 'number communities', 'relations', ' off node relations', ' infected', ' total attenuation', ' average attenuation', 'total relationships']
##    for i in range(1,len(data)):
##        plt.figure()
##        plt.suptitle(var[i])
##        for j in range(1,len(data)):
##            plt.subplot(3,3,j)
##            plt.scatter(data[i], data[j], c=data[num_communities], s=data[infected]/5,alpha=0.5), linewidth=0)
##            plt.colorbar(ticks=range(1,8))
##            plt.xlabel(var[i])
##            plt.ylabel(var[j])
    
    plt.show()
