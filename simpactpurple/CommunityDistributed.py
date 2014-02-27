import numpy.random as random
import numpy as np
import Community
import Operators
import OperatorsDistributed
import time as Time

class CommunityDistributed(Community.Community):

    def __init__(self, comm):
        Community.Community.__init__(self)
        #Distributed parameters
        self.comm = comm
        self.rank = comm.Get_rank()
        self.primary = self.rank == 0
        self.other = (self.rank+1)%2
        
        #MODEL PARAMETERS
        self.NUMBER_OF_YEARS = 5
        
        #MODEL OPERATORS
        #hazard
        self.preferred_age_difference = -0.1
        self.probability_multiplier = -0.1
        self.preferred_age_difference_growth = 5
        
        #relationship operator
        self.SEXES = 2
        self.MIN_AGE = 15
        self.MAX_AGE = 65
        self.BIN_SIZE = 5
        self.MAIN_QUEUE_MAX = 0.3  # proportion of initial population
        self.DURATIONS = lambda a1, a2: 52*random.exponential(0.9)
        
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
        self.DNP = lambda: random.power(0.2)*(4)

    def step(self):
        """
        Take a single time step (one week) in the simulation. 
        """ 
        #1. Time progresses
        #self.time_operator.step()        
        
        #2. Form and dissolve relationships
        self.relationship_operator.step()

        #3. HIV transmission
        #self.infection_operator.step()

    def make_population(self):
        if self.primary:
            Community.Community.make_population(self, self.INITIAL_POPULATION)
            self.comm.send('done', dest = self.other)
        else:
            agent = self.master.comm.recv(source = self.master.other)
            while agent != 'done':
                self.update_grid_queue_for(agent)
                agent = self.master.comm.recv(source = self.master.other)
    
    def make_operators(self):
        self.relationship_operator = OperatorsDistributed.RelationshipOperator(self)
        self.infection_operator = Operators.InfectionOperator(self)
        self.time_operator = Operators.TimeOperator(self)
            
    def add(self, agent):
        self.agents[agent.attributes["NAME"]] = agent
        self.network.add_node(agent)
        
        #location
        agent.attributes["LOC"] = np.random.rand(1,2) # should be generic to dimensions
        self.relationship_operator.update_grid_queue_for(agent)
        