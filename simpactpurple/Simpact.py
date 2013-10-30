""" This is an main module for the SimpactPurple program, a parallelized
agent-based model for simulating dynamic sexual networks and sexually
transmitted diseases. It has four main classes: Simpact, MainQueue,
GridQueue, and Agent.  The main loop takes place in the Simpact class
and proceeds in weekly discrete timesteps. Each week three operations
occur on the network: 1) Relationships are formed and dissolved, 2)
HIV is transmitted, 3) time progresses (agents age, some die, some are
born). The novety of the algorithm comes from the queueing procedure
used to form and dissolve relationships. """

#NOTE: Queue.PriorityQueue() gives priority to lower numbers

import Operators
import Agent
import random
import networkx as nx
import time as Time  # I use the keyword time
import numpy as np
import multiprocessing
import sys
#import interval as np # when numpy isn't available

class Simpact():

    def __init__(self):
        #MODEL PARAMETERS
        self.NUMBER_OF_YEARS = 30

        #MODEL POPULATION
        self.INITIAL_POPULATION = 100
        self.AGENT_ATTRIBUTES = {}
        
        #MODEL OPERATORS
        #relationship operator
        self.GENDERS = 2
        self.MIN_AGE = 15
        self.MAX_AGE = 65
        self.BIN_SIZE = 5
        self.MAIN_QUEUE_MAX = 0.1  # proportion of initial population
        
        #infection operator
        self.infectivity = 0.01
        self.initial_prevalence = 0.01
        self.seed_time = 0.5  # in years        

        #time operator
        self.time = 0
        
    def run(self,timing=False):
        start = Time.time()  # for timing simulation
        self.network = nx.Graph()
        self.agents = {}  # agent_name --> agent
        self.grid_queue = {}  # agent --> grid_queue
        self.relationships = []
        self.make_operators()  
        self.make_population(self.INITIAL_POPULATION)  # make agents
        self.infection_operator.perform_initial_infections(self.initial_prevalence, self.seed_time) 
        
        #run mainloop
        for t in range(int(self.NUMBER_OF_YEARS*52)):
            #print "===",t,"==="
            #sys.stdout.flush()
            #self.debug()
            #self.assertions()

            self.time = t  # I wonder if this is bad form
            self.step()

        #clean up
        #print "cleaning up", Time.time() - start
        for pipe in self.relationship_operator.pipes.values():
            pipe.send("terminate")
            

        #print timing if desired:
        #print "ending mainloop"
        end = Time.time()
        if timing: print "simulation took",end-start,"seconds"

    def step(self):
        #1. Time progresses
        #print "TIME OPERATOR"
        self.time_operator.step()        
        
        #2. Form and dissolve relationships
        #print "RELATIONSHIP OPERATOR"
        self.relationship_operator.step()

        #2. HIV transmission
        #print "INFECTION OPERATOR"
        self.infection_operator.step()



    def make_population(self, size, born=None, gender=None, dnp=None):
        """
        This makes a vanilla population with uniform age distribution. More
        advanced models can provide functions for age, gender, and dnp.
        """
        if born is None:
            born = lambda: -52*random.uniform(self.MIN_AGE, self.MAX_AGE)
        if gender is None:
            gender = lambda: random.randint(0, self.GENDERS - 1)
        if dnp is None:
            dnp = lambda: random.randint(1, 3)

        self.AGENT_ATTRIBUTES["TIME_ADDED"] = self.time
        self.AGENT_ATTRIBUTES["TIME_REMOVED"] = np.Inf
        self.AGENT_ATTRIBUTES["PARTNERS"] = 0
        for i in range(size):
            #make agent and add some attributes
            a = Agent.Agent(self.AGENT_ATTRIBUTES.copy())
            a.attributes["NAME"] = len(self.agents)  # not i b/c replacement
            a.born = born()
            a.gender = gender()
            a.dnp = dnp()

            #add to our list of agents
            self.agents[a.attributes["NAME"]] = a
            #self.grid_queue[a] = None
            self.network.add_node(a)
            self.relationship_operator.update_grid_queue_for(a)
#            self.relationship_operator.pipes[a.grid_queue].send("add")
#            self.relationship_operator.pipes[a.grid_queue].send(a)
#            self.relationship_operator.pipes[a.grid_queue].send("print")
            
    def make_operators(self):
        self.relationship_operator = Operators.RelationshipOperator(self)
        self.infection_operator = Operators.InfectionOperator(self)
        self.time_operator = Operators.TimeOperator(self)

    def age(self,agent):
        return (self.time - agent.born)/52

    def hazard(self, agent1, agent2, age_difference=None, mean_age=None):
        """
        This is a "simpactWhite" hazard function. In the future we can do
        "simpactBlu" hazard function in which we specifically ask the agent
        what she is looking for.
        """
        if(age_difference is None or mean_age is None):
            agent1_age = self.relationship_operator.grid_queues[agent1.grid_queue].my_age
            agent2_age = self.relationship_operator.grid_queues[agent2.grid_queue].my_age
            mean_age = (agent1_age + agent2_age) / 2
            age_difference = agent2_age - agent1_age

        #Agent centric:    
        #return agent1.is_looking_for(agent2, age_difference, mean_age)

        #controller centric
        #1
        age_difference = abs(age_difference)
        AGE_DIFFERENCE_FACTOR =-0.2
        MEAN_AGE_FACTOR = -0.01  # smaller --> less likely
        BASELINE = 1
        h = (agent1.gender ^ agent2.gender)*BASELINE*np.exp(AGE_DIFFERENCE_FACTOR*age_difference+MEAN_AGE_FACTOR*mean_age) 
        return h

        #2
#        preferred_age_difference = (1 - (2*agent1.gender))* -0.5
#        probability_multiplier = -0.1
#        preferred_age_difference_growth = 1
#        top = abs(age_difference - (preferred_age_difference*preferred_age_difference_growth*mean_age) )
#        h = np.exp(probability_multiplier *top ) ;
#        return (agent1.likes(agent2))*h

        #3
#        preferred_age_difference = (1 - (2 * agent1.gender)) * -0.5
#        probability_multiplier = -0.1
#        preferred_age_difference_growth = 0.9
#        age_difference_dispersion = -0.05
#        top = abs(age_difference - (preferred_age_difference * preferred_age_difference_growth * mean_age) )
#        bottom = preferred_age_difference*mean_age*age_difference_dispersion
#        h = np.exp(probability_multiplier * (top/bottom))
#        return (agent1.likes(agent2))*h
    def debug(self):
        print "======================", self.time, "======================="
        print "Cumulative num relations:",len(self.relationships)
        print "Point prevalence of relations:",len(self.network.edges())
        print "Grid Queues"
        print "agent in grid queues = ",sum([ len(gq.my_agents.heap) for gq in self.relationship_operator.grid_queues])
            
        print "GQ\t| G Ag Sz|| doubles?\t|| agents"
        print "------------------------------------------"
#        print ''.join([  str(gq.my_index)+"\t| "+str(gq.my_gender)+ " " + str(gq.my_age)+
#                    " "+str(len(gq.my_agents.heap)) +
#                    " || " + str(any([a for a in gq.agents_in_queue() 
#                        if gq.agents_in_queue().count(a) > 1])) +
#                    "\t|| "+" ".join(gq.agents_in_queue()) + '\n'
#                    for gq in self.relationship_operator.grid_queues])
        for gq in self.relationship_operator.grid_queues:
            pipe = self.relationship_operator.pipes[gq.my_index]
            pipe.send("queue")
            agents = pipe.recv()
            agents = [str(a.attributes["NAME"]) for p,a in agents.heap]
            
            line = str(gq.my_index) + "\t|" + str(gq.my_gender) + " " + \
                str(gq.my_age) + " " + str(len(agents)) + " || " + \
                str(any([a for a in agents if agents.count(a) > 1])) + \
                "\t|| " + " ".join(agents)
            print line
            
            
                        
    def assertions(self):
        doubles = []
        for gq in self.relationship_operator.grid_queues:
            pipe = self.relationship_operator.pipes[gq.my_index]
            pipe.send("queue")
            agents = pipe.recv().heap
            doubles.append([a for p,a in agents if agents.count(a) > 1])
        any_doubles = any([any(d) for d in doubles])
        assert (not any_doubles), "Duplicates in grid queues:" + " ".join([str(d) for d in doubles])
