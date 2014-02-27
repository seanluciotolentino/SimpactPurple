import numpy.random as random
import numpy as np
import Community
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
            
    def run(self, timing = False):
        """
        Initialize data structures and begin the mainloop of the modified 
        Community: Wait for "step" signal from Global, send "done" signal
        when finished. Global waits for all communities to send "done"
        before sending next "step". Global migration operator may remove and
        add individuals to communities.
        """
        self.start()  # initialize data structures
        print "running..."
        #mainloop
        for t in range(int(self.NUMBER_OF_YEARS*52)):
            self.time = t
            self.step()
        
        self.cleanup()  # send terminate signal

        #print timing if desired:
        end = Time.time()
        if timing: print "simulation took",end-start,"seconds"

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
    
    def make_operators(self):
        self.relationship_operator = OperatorsDistributed.RelationshipOperator(self)
        self.infection_operator = OperatorsDistributed.InfectionOperator(self)
        self.time_operator = OperatorsDistributed.TimeOperator(self)
            
    def add(self, agent):
        self.agents[agent.attributes["NAME"]] = agent
        self.network.add_node(agent)
        
        #location
        agent.attributes["LOC"] = np.random.rand(1,2) # should be generic to dimensions
        self.relationship_operator.update_grid_queue_for(agent)
        
        
