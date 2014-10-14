# -*- coding: utf-8 -*-
"""
Created on Tue Sep 02 13:23:24 2014

@author: Lucio

An investigation of the sensitivity of the model's output to different
recruiting and optimization effects. We run the model under several
scenarios and asses it's the model's ability to reproduce a sexual
network that is reasonably similar to what is seen in the data.
The scenarios are:
    (1) Recruit from queues based on queue size (not randomly).
    (2) Recruit agents from queues randomly (not based on time since
    last forming a relationship).
    (3) Resorting the queue for every suitor (not saving decisions for
    the next suitor).
    
This script runs each scenario by using modified community, operators, and
grid queue classes that are defined in this script. Call this script from
command line with the scenario you wish to run as a parameter. 

$ python SensitivityAnalysis.py 1

*Note: Originally "recycling values" was initially a scenario but was removed
because it doesn't help much in the run time so it is no longer used. 

"""

import simpactpurple
import simpactpurple.GridQueue as GridQueue
import simpactpurple.Operators as Operators
import numpy as np
import numpy.random as random
import simpactpurple.GraphsAndData as GraphsAndData
import sys

class ModifiedGridQueue(GridQueue.GridQueue):
    def recruit(self):
        """
        Scenario 2: When recruit method is called for the first time,
        it resorts agents with a random value (as opposed to based on 
        the their last match).
        """
        if self.scenario == 2:
            #0. return agents for main queue (if any)
            if self.agents.empty(): 
                return None
    
            #1. reorganize if dissimilar from previous
            if self.previous is not None: 
                self.previous = None
                agents = list(self.agents.heap)  # copy the list
                self.agents.clear()
                for probability, agent in agents:
                    #===START CHANGES 1/1 ===#
                    self.agents.push(random.random(), agent)
                    
            value, agent = self.agents.pop()
            agent.last_match = self.time
            self.agents.push(value+1,agent) 
            return agent.name    
            #===END CHANGES 1/1 ===#
        else:
            return GridQueue.GridQueue.recruit(self)
    
    def enquire(self, suitor):
        """
        Scenario 3: Set previous to None so that GridQueue
        resorts everytime. 
        """
        if self.scenario == 3:
            self.previous = None
            name = GridQueue.GridQueue.enquire(self, suitor)
            self.previous = suitor
            return name
        else:
            return GridQueue.GridQueue.recruit(self)
        
class ModifiedRelationshipOperator(Operators.RelationshipOperator):
    """
    Scenario 1: A modified relationship operator picks grid queues 
    based on their size (not randomly).
    """
    def step(self):
        """
        Grab the sizes of the queues for use with the recruiting
        method.
        """
        #get sizes for distribution
        for q in self.master.pipes:
            self.master.pipes[q].send("size")
        self.size = {}
        for q in self.master.pipes:
            self.size[q] = float(self.master.pipes[q].recv())
        Operators.RelationshipOperator.step(self)
            
    def recruit(self):
        """
        Instead of sampling queues uniformly, sample based on
        the size (length) of queue.
        """
        #build distribution
        queues = self.size.keys()
        queue_lengths = np.array([self.size[q] for q in queues])
        probabilities = queue_lengths/sum(queue_lengths)
        r = random.random()
        gq_index = [int(v) for v in r < np.cumsum(probabilities)].index(1)
        gq = queues[gq_index]
        
        #recruit as normal
        self.master.pipes[gq].send("recruit")
        agent_name = self.master.pipes[gq].recv()  
        if agent_name is not None:
            agent = self.master.agents[agent_name]
            self.master.main_queue.push(gq, agent)

class ModifiedCommunity(simpactpurple.Community):
    def make_n_queues(self, n):
        """
        Scenario 2 and 3: Use the modified Grid Queue defined above
        in the simulation. 
        """
        #make the grid queues
        for i in range(n):
            #===START CHANGES 1/1 ===#
            gq = ModifiedGridQueue(self.next_top, self.next_bottom, self.grid_queue_index)
            gq.scenario = self.scenario            
            #===START CHANGES 1/1 ===#
            gq.max_age = self.MAX_AGE
            gq.sex = i  # not used
            gq.PREFERRED_AGE_DIFFERENCE= self.PREFERRED_AGE_DIFFERENCE
            gq.AGE_PROBABILITY_MULTIPLIER = self.AGE_PROBABILITY_MULTIPLIER
            gq.PREFERRED_AGE_DIFFERENCE_GROWTH = self.PREFERRED_AGE_DIFFERENCE_GROWTH
            gq.SB_PROBABILITY_MULTIPLIER = self.SB_PROBABILITY_MULTIPLIER
            
            self.grid_queues[gq.index] = gq
            self.grid_queue_index+=1
            self.spawn_process_for(gq)  # start a new process for it
        
        #increment for next grid queue
        self.next_top += self.BIN_SIZE*52
        self.next_bottom += self.BIN_SIZE*52
        
    def make_operators(self):
        """
        Scenario 1: Use the modified operator defined above
        """
        simpactpurple.Community.make_operators(self)
        if self.scenario == 1:
            self.relationship_operator = ModifiedRelationshipOperator(self)
    
    def step(self):
        #self.debug()
        simpactpurple.Community.step(self)
        
#%%script starts here
try:
    scenario = int(sys.argv[1])
except IndexError:
    scenario = 0  # default
    
if __name__ == '__main__':
    n = 100
    for i in range(n):
        #run the modified simulation
        s = ModifiedCommunity()
        s.INITIAL_POPULATION = 1000
        s.PREFERRED_AGE_DIFFERENCE_GROWTH = 0.5
        s.BORN = lambda: -52*np.min((64,15.2+random.exponential(0.9)*12))
        s.DNP = lambda: random.power(0.7)*2.5
        s.AGE_PROBABILITY_MULTIPLIER = -0.4
        s.RECRUIT_RATE = 0.01
        s.scenario = scenario
        s.run()
        
        #write it all to a file
        #f = open("Sensitivity{0}.csv".format(resort),'a')
        #f.write(str(i) + ",")
        #f.write(",".join(map(lambda x: str(round(100*x,1)), GraphsAndData.intergenerational_sex_data(s, year = s.NUMBER_OF_YEARS)))+",")  # 2008
        #f.write(",".join(map(lambda x: str(round(100*x,1)), GraphsAndData.number_of_partners_data(s, year = s.NUMBER_OF_YEARS)))+",")  # 2008
        #f.write("\n")
        #f.close()
        
        print ",".join(map(lambda x: str(round(100*x,1)), GraphsAndData.intergenerational_sex_data(s, year = s.NUMBER_OF_YEARS)))+",",
        print ",".join(map(lambda x: str(round(100*x,1)), GraphsAndData.number_of_partners_data(s, year = s.NUMBER_OF_YEARS)))+","

def visualize_age_distribution():
    import matplotlib.pyplot as plt
    import numpy as np
    import numpy.random as random
    
    distribution = lambda: np.min((64,15.2+random.exponential(0.9)*12))
    plt.hist([distribution() for i in range(1000)],bins=range(15,70,5),normed=True)
    plt.title("Age Distribution")
    plt.xlabel("Age")
    plt.xlim([15,65])
    plt.ylabel("Frequency")