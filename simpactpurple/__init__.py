""" 
The main module for simulating HIV in a community.
"""

import Operators
import GridQueue
import PriorityQueue
import networkx as nx
import time as Time  # I use the keyword time
import numpy as np
import numpy.random as random
import multiprocessing
import sys

class Agent():
    def __init__(self):
        """
        A class for holding the important information about agents. All 
        variables are set in the make_population (they are initialized here
        as None to emphasis their existence).
        """
        self.born = None
        self.sex = None
        self.dnp = None
        self.grid_queue = None
        self.name = None
    
        self.time_of_infection = np.Inf 
        self.last_match = -np.Inf
        self.attributes = {}
        
    def __str__(self):
        return str(self.name)

class Community():
    """
    This is the main object for simulating HIV in a community. 
    """
    def __init__(self):
        #MODEL PARAMETERS
        self.NUMBER_OF_YEARS = 30
        
        #MODEL OPERATORS
        #probabilitiy
        self.PREFERRED_AGE_DIFFERENCE = -0.1
        self.AGE_PROBABILITY_MULTIPLIER = -0.2
        self.PREFERRED_AGE_DIFFERENCE_GROWTH = 0.1
        self.SB_PROBABILITY_MULTIPLIER = 0
        
        #relationship operator
        self.SEXES = 2
        self.MIN_AGE = 15
        self.MAX_AGE = 65
        self.BIN_SIZE = 5
        self.DURATIONS = lambda a1, a2: 30*random.exponential(1)
        self.RECRUIT_WARM_UP = 20
        self.RECRUIT_INITIAL = 0.02
        self.RECRUIT_RATE = 0.005
        
        #infection operator
        self.INFECTIVITY = 0.01
        self.INITIAL_PREVALENCE = 0.01
        self.SEED_TIME = 20  # in weeks

        #time operator
        self.time = -1
        self.grid_queue_index = 0
                
        #MODEL POPULATION
        self.INITIAL_POPULATION = 100
        self.AGENT_ATTRIBUTES = {}
        self.BORN = lambda: -52*random.uniform(self.MIN_AGE, self.MAX_AGE)
        self.SEX = lambda: random.randint(self.SEXES)
        self.DNP = lambda: random.power(0.1)*1.2
        self.SEXUAL_BEHAVIOR = lambda: random.randint(1,5)
        
    def run(self, timing=False):
        """
        Runs the mainloop of the simulation. Clear all data structures, make
        agents, and iterate through time steps.
        """
        #pre-process
        start = Time.time()  # for timing simulation
        self.start()  # initialize data structures
        
        #mainloop
        self.update_recruiting(self.RECRUIT_INITIAL)
        for t in range(self.RECRUIT_WARM_UP):
            self.time = t
            self.step()
        
        self.update_recruiting(self.RECRUIT_RATE)
        for t in range(self.RECRUIT_WARM_UP, int(self.NUMBER_OF_YEARS*52)):
            self.time = t
            self.step()
        
        #post-process / clean-up
        for pipe in self.pipes.values():
            pipe.send("terminate")

        #print timing if desired:
        end = Time.time()
        if timing: print "simulation took",round(end-start,2),"seconds"
        
    def start(self):
        """
        Initializes the data structures and operators.  This allows users to 
        set simulation variables and still have initialization of data
        structures independent from the run method.
        """
        #basic structures
        self.time = -1
        self.network = nx.Graph()
        self.agents = {}  # {agent_name : agent}
        self.relationships = []
        self.grid_queues = {}  # {gq.index : gq}
        self.pipes = {}  # {gq.index : pipe}
        self.relationships_ending_at = {t:[] for t in range(1+int(self.NUMBER_OF_YEARS*52))}
        self.main_queue = PriorityQueue.PriorityQueue()
        
        #turn off warm up for short simulations
        if int(self.NUMBER_OF_YEARS*52) < self.RECRUIT_WARM_UP:
            self.RECRUIT_WARM_UP = 0

        #grid queues and operators     
        self.next_top = -52 * self.MAX_AGE
        self.next_bottom = -52 * (self.MAX_AGE + self.BIN_SIZE)   
        self.make_queues()
        self.make_operators()  
        
        #initialize population
        self.make_population(self.INITIAL_POPULATION)  # make agents
        self.BORN = lambda: self.time - (52*15.02)  # new born function for replacement
        self.infection_operator.perform_initial_infections(self.INITIAL_PREVALENCE, self.SEED_TIME) 
    
    def make_queues(self):
        """
        Make all the initial queues.
        """
        for age in range(self.MIN_AGE, self.MAX_AGE+self.BIN_SIZE, self.BIN_SIZE):
            self.make_n_queues(self.SEXES)
                
    def make_n_queues(self, n):
        """
        Make *n* new queues based on the previously made queues. This method is
        seperate from "make_queues" so that the time operator can make new 
        queues as the oldest queues are retired.
        """
        #make the grid queues
        for i in range(n):
            gq = GridQueue.GridQueue(self.next_top, self.next_bottom, self.grid_queue_index)
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
        
    def spawn_process_for(self, gq):
        """
        Spawns a new process via multiprocessing with communication via a pipe.
        In a seperate function to accomadate distributed version.
        """
        pipe_top, pipe_bottom = multiprocessing.Pipe()
        p = multiprocessing.Process(target=GridQueue.listen,args=(gq, pipe_bottom))
        p.start()
        self.pipes[gq.index] = pipe_top
        
    def make_operators(self):
        """
        Creates the operators necessary for the simulation.
        """
        self.relationship_operator = Operators.RelationshipOperator(self)
        self.infection_operator = Operators.InfectionOperator(self)
        self.time_operator = Operators.TimeOperator(self)
        
    def make_population(self, size):
        """
        Creates *size* agents with age, sex, and desired number of partners
        (DNP) dictated by *born*, *sex*, and *dnp* (distributions set at 
        initialization). If these these are omitted, default distributions will
        be used. After an agent receives a name, age, sex, and DNP, he or she 
        is added to the network graph and added to a grid queue.
        """        
        for i in range(size):
            #make agent and add some attributes
            a = Agent()
            a.attributes["TIME_ADDED"] = self.time
            a.attributes["TIME_REMOVED"] = np.Inf
            a.born = self.BORN()
            a.sex = self.SEX()
            a.dnp = self.DNP()
            a.sexual_behavior = self.SEXUAL_BEHAVIOR()
            a.name = len(self.agents)  # not i b/c replacement
            self.add_to_simulation(a)
            
    def add_to_simulation(self,agent):
        """
        Add *agent* to the list of agents, the network, and assign to a grid
        queue. This is seperate from the make_population method so that
        other objects can add agents without make_population.
        """
        self.agents[agent.name] = agent
        self.network.add_node(agent)
        
        #agent given a grid queue at initialization
        grid_queue = [gq for gq in self.grid_queues.values() if gq.accepts(agent)][agent.sex]
        agent.grid_queue = grid_queue.index
        self.add_to_grid_queue(agent)
        
    def add_to_grid_queue(self, agent):
        """
        Add an agent back to their grid queue. Called when (1) When agent is 
        initialized (called by Community) and (2) When one of the agent's 
        relationship is dissolved (called by the Time Operator).           
        """
        self.pipes[agent.grid_queue].send("add")
        self.pipes[agent.grid_queue].send(agent)
        
    def update_recruiting(self, rate):
        """
        Function called after initial warm up period -- updates the value for
        self.recruit. In a seperate function to accomadate distributed version.
        """
        self.recruit = int(np.ceil(self.INITIAL_POPULATION*rate))

    def step(self):
        """
        Take a single time step (one week) in the simulation. 
        """
        #1. Time progresses
        self.time_operator.step()
        
        #2. Form and dissolve relationships"
        self.relationship_operator.step()

        #3. HIV transmission
        self.infection_operator.step()
        
    def age(self, agent):
        """
        Finds the age of *agent*
        """
        return (self.time - agent.born)/52.0

    def probability(self, agent1, agent2, **attributes):
        """
        Calculates and returns the probability of relationship formation between
        agent1 and agent2. If *age_difference* or *mean_age* is None (i.e.
        not provided), this function will calculate it. 
        """
        if('age_difference' in attributes and 'mean_age' in attributes):
            age_difference = attributes['age_difference']
            mean_age = attributes['mean_age']
        else:
            agent1_age = self.grid_queues[agent1.grid_queue].age()
            agent2_age = self.grid_queues[agent2.grid_queue].age()
            mean_age = (agent1_age + agent2_age) / 2.0
            age_difference = agent2_age - agent1_age
            
        pad = (1 - (2*agent1.sex))* self.PREFERRED_AGE_DIFFERENCE  # correct for perspective
        age_abs = abs(age_difference-(pad*self.PREFERRED_AGE_DIFFERENCE_GROWTH*mean_age))
        age_probability = np.exp(self.AGE_PROBABILITY_MULTIPLIER*age_abs)
        
        sb_abs = abs(agent1.sexual_behavior-agent2.sexual_behavior)
        sb_probability = np.exp(self.SB_PROBABILITY_MULTIPLIER*sb_abs)
        p = (agent1.sex ^ agent2.sex)*age_probability*sb_probability
        #print "name",agent1.name,"age", round(self.age(agent1),2),"sex",agent1.sex,"sb",agent1.sexual_behavior,
        #print "| name",agent2.name,"age", round(self.age(agent2),2),"sex",agent2.sex,"sb",agent2.sexual_behavior,
        #print "| age_p = ", round(age_probability,2), "sb_p", round(sb_probability,2), "p", round(p,2)
        return p

    def debug(self):
        print "======================", self.time, "======================="
        print "Cumulative num relations:",len(self.relationships)
        print "Point prevalence of relations:",len(self.network.edges())
        print "Grid Queues"
        print "agents in grid queues = ",sum([ len(gq.agents.heap) for gq in self.grid_queues.values()])
            
        print "GQ\t| G Ag Sz|| doubles?\t|| agents"
        print "------------------------------------------"
        for gq in self.grid_queues.values():
            pipe = self.pipes[gq.index]
            pipe.send("queue")
            pq = pipe.recv()
            #agents = [str(a.name) for p,a in agents.heap]
            agents = []
            for i in range(len(pq.heap)):
                a = pq.pop()
                agents.append(str((a[0], a[1].name)))
            
            line = str(gq.index) + "\t|" + str(gq.sex) + " " + \
                str(round(gq.age(),2)) + " " + str(len(agents)) + " || " + \
                str(any([a for a in agents if agents.count(a) > 1])) + \
                "\t|| " + " ".join(agents)
            print line
        sys.stdout.flush()
                        
    def assertions(self):
        #assert that no agents is in a grid queue twice
        doubles = []
        for gq in self.grid_queues.values():
            pipe = self.pipes[gq.index]
            pipe.send("queue")
            agents = pipe.recv().heap
            doubles.append([a for p,a in agents if agents.count(a) > 1])
        any_doubles = any([any(d) for d in doubles])
        assert (not any_doubles), "Duplicates in grid queues:" + " ".join([str(d) for d in doubles])        
