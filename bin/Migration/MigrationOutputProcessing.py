# -*- coding: utf-8 -*-
"""
Created on Mon Sep 15 10:38:06 2014

@author: Lucio

Script to process the output from MainMigrationScenarios.

"""

#%% process some of the input
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats
import os

def clean_file(filename):
    """
    Remove debug output from *filename*.
    """
    #keep all the good lines, throw out the bad
    r = open(filename, 'r')
    w = open('temp.out', 'w')
    bug = False
    for line in r:
        if line[1] == '.' and bug:
            print 'x', line
            bug = False
            continue
        elif line[1] != '.':
            print 'x', line
            bug = True
            continue
        else:
            line = line.replace(' [[',',').replace('], [',',').replace(']]','')
            print '+', line
            w.write(line)
    r.close()
    w.close()
    
    #copy good lines back to original file
    r = open(filename, 'w')
    w = open('temp.out', 'r')
    for line in w:
        r.write(line)
    r.close()
    w.close()
    os.popen('rm temp.out')
            
plt.ion()
name = ['Western Cape', 'Eastern Cape', 'Northern Cape', 'Free State', 
        'KZN', 'North West', 'Gauteng', 'Mpumalanda', 'Limpopo']
prevalence = [10.7, 6.6, 8.4, 14.9,
              11.7, 10.3, 14.7, 14.1, 9.8]
data01 = np.loadtxt('MigrationOutput01.out', delimiter=",")
data05 = np.loadtxt('MigrationOutput05.out', delimiter=",")
data75 = np.loadtxt('MigrationOutput75.out', delimiter=",")
data10 = np.loadtxt('MigrationOutput10.out', delimiter=",")
data20 = np.loadtxt('MigrationOutput20.out', delimiter=",")
colors = ['g','b','r','y','k']
plt.close('all')
plt.figure()
plt.suptitle('Prevalence under Different Migration Scenarios', fontsize=14)
for i in range(3):
    for j in range(3):
        community = (i*3)+(j+1)
        plt.subplot(3,3,community)
        for c, data in enumerate([data01, data05, data75, data10, data20]):
            plt.hist(100*data[:,community*7],bins=range(0,40,2),normed=True, color=colors[c], alpha = 0.6)
        plt.plot((prevalence[community-1], prevalence[community-1]),(0,1),c='r')
        #fvalue, pvalue = scipy.stats.f_oneway(data10[:,community*7],data20[:,community*7])
        #print "community",community,"F-value", fvalue, "p-value", pvalue
        #star = ["", "*"][pvalue<=0.05]
        plt.title(name[community-1])
        if j == 0:
            plt.ylabel('Frequency')
        if i == 2:
            plt.xlabel('30-year Prevalence')
        plt.ylim((0.0, 0.40))
        plt.xlim((0,40))
        if community == 3:
            plt.legend(['actual','0.1', '0.5', '0.75', '1.0', '2.0'])