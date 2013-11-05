""" 
The main module a simulation of a community. 
"""

import Operators
import Agent
import random
import networkx as nx
import time as Time  # I use the keyword time
import numpy as np

class Community():
    """
    This is the main object for simulating HIV in a community. 
    """
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
        self.INFECTIVITY = 0.01
        self.INTIIAL_PREVALENCE = 0.01
        self.SEED_TIME = 0.5  # in years        

        #time operator
        self.time = 0
        
    def start(self):
        """
        Initializes the data structures and operators.  This allows users to 
        set simulation variables and still have initialization of data
        structures independent from the run method.
        """
        self.network = nx.Graph()
        self.agents = {}  # agent_name --> agent
        self.grid_queue = {}  # agent --> grid_queue
        self.relationships = []
        self.make_operators()  
        self.make_population(self.INITIAL_POPULATION)  # make agents
        self.infection_operator.perform_initial_infections(self.INTIIAL_PREVALENCE, self.SEED_TIME) 
        
    def run(self, timing=False):
        """
        Runs the mainloop of the simulation. Clear all data structures, make
        agents, and iterate through time steps.
        """
        start = Time.time()  # for timing simulation
        self.start()
        #run mainloop
        for t in range(int(self.NUMBER_OF_YEARS*52)):
            self.time = t  # I wonder if this is bad form
            #if t%52==0: print "=== Year",t/52,"==="
            #sys.stdout.flush()
            #self.debug()
            #self.assertions()            
            self.step()
        #clean up
        self.cleanup()    

        #print timing if desired:
        end = Time.time()
        if timing: print "simulation took",end-start,"seconds"
        
    def cleanup(self):
        """
        Send a 'terminate' signal to all of the Grid Queues.
        """
        for pipe in self.relationship_operator.pipes.values():
            pipe.send("terminate")

    def step(self):
        """
        Take a single time step (one week) in the simulation. 
        """ 
        #1. Time progresses
        self.time_operator.step()        
        
        #2. Form and dissolve relationships
        self.relationship_operator.step()

        #2. HIV transmission
        self.infection_operator.step()

    def make_population(self, size, born=None, gender=None, dnp=None):
        """
        Creates *size* agents with age, gender, and desired number of partners
        (DNP) dictated by *born*, *gender*, and *dnp* (functions). If these 
        these are omitted, default distributions will be used.

        After an agent receives a name, age, gender, and DNP, he or she is added
        to the network graph and added to a grid queue.
        """
        if born is None:
            born = lambda: -52*random.uniform(self.MIN_AGE, self.MAX_AGE)
        if gender is None:
            gender = lambda: random.randint(0, self.GENDERS - 1)
        if dnp is None:
            dnp = lambda: random.randint(1, 3)

        self.AGENT_ATTRIBUTES["TIME_ADDED"] = self.time
        self.AGENT_ATTRIBUTES["TIME_REMOVED"] = np.Inf
        for i in range(size):
            #make agent and add some attributes
            a = Agent.Agent(self.AGENT_ATTRIBUTES.copy())
            a.attributes["NAME"] = len(self.agents)  # not i b/c replacement
            a.born = born()
            a.gender = gender()
            a.dnp = dnp()
            self.add(a)            
            
    def add(self,agent):
        """
        Add *agent* to the list of agents, the network, and assign to a grid
        queue. This is seperate from the make_population method so that
        other objects can add agents without make_population.
        """
        self.agents[agent.attributes["NAME"]] = agent
        self.network.add_node(agent)
        self.relationship_operator.update_grid_queue_for(agent)
            
    def make_operators(self):
        """
        Creates the operators necessary for the simulation.
        """
        self.relationship_operator = Operators.RelationshipOperator(self)
        self.infection_operator = Operators.InfectionOperator(self)
        self.time_operator = Operators.TimeOperator(self)

    def age(self,agent):
        """
        Finds the age of *agent*
        """
        return (self.time - agent.born)/52.0

    def hazard(self, agent1, agent2, age_difference=None, mean_age=None):
        """
        Calculates and returns the hazard of relationship formation between
        agent1 and agent2. If *age_difference* or *mean_age* is None (i.e.
        not provided), this function will calculate it. 
        """
        if(age_difference is None or mean_age is None):
            agent1_age = self.relationship_operator.grid_queues[agent1.grid_queue].my_age
            agent2_age = self.relationship_operator.grid_queues[agent2.grid_queue].my_age
            mean_age = (agent1_age + agent2_age) / 2
            age_difference = agent2_age - agent1_age
            
        #0
        #return agent1.gender ^ agent2.gender

        #1
        age_difference = abs(age_difference)
        AGE_DIFFERENCE_FACTOR =-0.2
        MEAN_AGE_FACTOR = -0.01  # smaller --> less likely
        BASELINE = 1
        h = (agent1.gender ^ agent2.gender)*BASELINE*np.exp(AGE_DIFFERENCE_FACTOR*age_difference+MEAN_AGE_FACTOR*mean_age) 
        return h

        #2
        ##preferred_age_difference = (1 - (2*agent1.gender))* -0.5
        ##probability_multiplier = -0.1
        ##preferred_age_difference_growth = 1
        ##top = abs(age_difference - (preferred_age_difference*preferred_age_difference_growth*mean_age) )
        ##h = np.exp(probability_multiplier *top ) ;
        ##return (agent1.likes(agent2))*h

        #3
        ##preferred_age_difference = (1 - (2 * agent1.gender)) * -0.5
        ##probability_multiplier = -0.1
        ##preferred_age_difference_growth = 0.9
        ##age_difference_dispersion = -0.05
        ##top = abs(age_difference - (preferred_age_difference * preferred_age_difference_growth * mean_age) )
        ##bottom = preferred_age_difference*mean_age*age_difference_dispersion
        ##h = np.exp(probability_multiplier * (top/bottom))
        ##return (agent1.likes(agent2))*h

        #4
        #return int(not (agent1.gender ^ agent2.gender))  # true if same gender

    def debug(self):
        print "======================", self.time, "======================="
        print "Cumulative num relations:",len(self.relationships)
        print "Point prevalence of relations:",len(self.network.edges())
        print "Grid Queues"
        print "agents in grid queues = ",sum([ len(gq.my_agents.heap) for gq in self.relationship_operator.grid_queues])
            
        print "GQ\t| G Ag Sz|| doubles?\t|| agents"
        print "------------------------------------------"
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
        #assert that no agents is in a grid queue twice
        doubles = []
        for gq in self.relationship_operator.grid_queues:
            pipe = self.relationship_operator.pipes[gq.my_index]
            pipe.send("queue")
            agents = pipe.recv().heap
            doubles.append([a for p,a in agents if agents.count(a) > 1])
        any_doubles = any([any(d) for d in doubles])
        assert (not any_doubles), "Duplicates in grid queues:" + " ".join([str(d) for d in doubles])        