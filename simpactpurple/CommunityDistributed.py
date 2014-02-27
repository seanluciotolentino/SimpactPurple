import numpy.random as random
import numpy as np
import Community
import OperatorsAlt
import Operators
import time

class Community(Community.Community):

    def __init__(self, comm):
        Community.Community.__init__(self)
        #Distributed parameters
        self.comm = comm
        self.rank = comm.Get_rank()
        self.primary = rank == 0
        self.other = (rank+1)%2
        
        
        #MODEL PARAMETERS
        self.NUMBER_OF_YEARS = Global.NUMBER_OF_YEARS
        self.AGENT_ATTRIBUTES = {}

        #MODEL POPULATION
        self.INITIAL_POPULATION = Global.INITIAL_POPULATION/len(Global.community_nodes)
        
        #MODEL OPERATORS
        #relationship operator
        self.SEXES = Global.SEXES
        self.MIN_AGE = Global.MIN_AGE
        self.MAX_AGE = Global.MAX_AGE
        self.BIN_SIZE = Global.BIN_SIZE
        self.MAIN_QUEUE_MAX = Global.MAIN_QUEUE_MAX  # proportion of initial population

        #infection operator
        self.INFECTIVITY = Global.INFECTIVITY
        self.INTIAL_PREVALENCE = Global.INTIAL_PREVALENCE  # global does initial seeding
        self.SEED_TIME = Global.SEED_TIME 
            
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
        self.time_operator.step()        
        
        #2. Form and dissolve relationships
        self.relationship_operator.step()

        #3. HIV transmission
        self.infection_operator.step()
    
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
        
        
