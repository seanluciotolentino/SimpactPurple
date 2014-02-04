""" 
The main module a simulation of a community. 
"""

import Operators
import Agent
import networkx as nx
import time as Time  # I use the keyword time
import numpy as np
import numpy.random as random
import multiprocessing

class Community():
    """
    This is the main object for simulating HIV in a community. 
    """
    def __init__(self):
        #MODEL PARAMETERS
        self.NUMBER_OF_YEARS = 30
        
        #MODEL OPERATORS
        #relationship operator
        self.SEXES = 2
        self.MIN_AGE = 15
        self.MAX_AGE = 65
        self.BIN_SIZE = 5
        self.MAIN_QUEUE_MAX = 0.3  # proportion of initial population
        self.DURATIONS = lambda: 52*random.exponential(0.9)
        
        #infection operator
        self.INFECTIVITY = 0.01
        self.INTIIAL_PREVALENCE = 0.01
        self.SEED_TIME = 0  # in years        

        #time operator
        self.time = 0
                
        #MODEL POPULATION
        self.INITIAL_POPULATION = 100
        self.AGENT_ATTRIBUTES = {}
        self.BORN = lambda: -52*random.uniform(self.MIN_AGE, self.MAX_AGE)
        self.SEX = lambda: random.randint(self.SEXES)
        self.DNP = lambda: random.power(0.2)*(10*52)
        
    def run(self, timing=False):
        """
        Runs the mainloop of the simulation. Clear all data structures, make
        agents, and iterate through time steps.
        """
        start = Time.time()  # for timing simulation
        self.start()  # initialize data structures
        
        #mainloop
        for t in range(int(self.NUMBER_OF_YEARS*52)):
            print "time",t
            self.time = t
            self.step()
            #self.assertions()
        
        self.cleanup()  # send terminate signal

        #print timing if desired:
        end = Time.time()
        if timing: print "simulation took",end-start,"seconds"
        
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
        self.BORN = lambda: self.time - (52*15.02)  # new born function for replacement
        self.infection_operator.perform_initial_infections(self.INTIIAL_PREVALENCE, self.SEED_TIME) 
            
    def make_operators(self):
        """
        Creates the operators necessary for the simulation.
        """
        self.relationship_operator = Operators.RelationshipOperator(self)
        self.infection_operator = Operators.InfectionOperator(self)
        self.time_operator = Operators.TimeOperator(self)
        
    #def make_population(self, size, born=None):
    def make_population(self, size):
        """
        Creates *size* agents with age, sex, and desired number of partners
        (DNP) dictated by *born*, *sex*, and *dnp* (functions). If these 
        these are omitted, default distributions will be used.

        After an agent receives a name, age, sex, and DNP, he or she is added
        to the network graph and added to a grid queue.
        """
#        if not born:
#            born = lambda: -52*random.uniform(self.MIN_AGE, self.MAX_AGE)
#        sex = lambda: random.randint(self.SEXES)
#        dnp = self.DNP
        
        self.AGENT_ATTRIBUTES["TIME_ADDED"] = self.time
        self.AGENT_ATTRIBUTES["TIME_REMOVED"] = np.Inf
        for i in range(size):
            #make agent and add some attributes
            a = Agent.Agent(self.AGENT_ATTRIBUTES.copy())
            a.attributes["NAME"] = len(self.agents)  # not i b/c replacement
            a.born = self.BORN()
            a.sex = self.SEX()
            a.dnp = self.DNP()
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
        
    def cleanup(self):
        """
        Send a 'terminate' signal to all of the Grid Queues. Update end values
        in relationships (to account for deaths). 
        """
        for pipe in self.relationship_operator.pipes.values():
            pipe.send("terminate")
            
        for r in self.relationships:
            agent1 = r[0]
            agent2 = r[1]
            r[3] = min((r[3], agent1.attributes["TIME_REMOVED"], agent2.attributes["TIME_REMOVED"]))

    def age(self, agent):
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
        #return agent1.sex ^ agent2.sex

        #1
        #age_difference = abs(age_difference)
        #AGE_DIFFERENCE_FACTOR =-0.2
        #MEAN_AGE_FACTOR = -0.01  # smaller --> less likely
        #BASELINE = 1
        #h = (agent1.sex ^ agent2.sex)*BASELINE*np.exp(AGE_DIFFERENCE_FACTOR*age_difference+MEAN_AGE_FACTOR*mean_age) 
        #return h

        #2
        preferred_age_difference = (1 - (2*agent1.sex))* -0.5
        probability_multiplier = -0.1
        preferred_age_difference_growth = 1
        top = abs(age_difference - (preferred_age_difference*preferred_age_difference_growth*mean_age) )
        h = np.exp(probability_multiplier *top ) ;
        return (agent1.sex ^ agent2.sex)*h

        #3
        ##preferred_age_difference = (1 - (2 * agent1.sex)) * -0.5
        ##probability_multiplier = -0.1
        ##preferred_age_difference_growth = 0.9
        ##age_difference_dispersion = -0.05
        ##top = abs(age_difference - (preferred_age_difference * preferred_age_difference_growth * mean_age) )
        ##bottom = preferred_age_difference*mean_age*age_difference_dispersion
        ##h = np.exp(probability_multiplier * (top/bottom))
        ##return (agent1.likes(agent2))*h

        #4
        #return int(not (agent1.sex ^ agent2.sex))  # true if same sex

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
            
            line = str(gq.my_index) + "\t|" + str(gq.my_sex) + " " + \
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