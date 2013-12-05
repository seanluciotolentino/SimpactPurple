import numpy.random as random
import numpy as np
import Community
import OperatorsAlt
import Operators
import time

class CommunityAlt(Community.Community):
    """
    This particular Community object knows how to communicate with a Global 
    object via OpenMPI and run parallel to other CommunityMPI objects
    """
    
    def __init__(self, comm, Global):
        Community.Community.__init__(self)
        self.comm = comm
        self.servants = []
        
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
        self.start()
        self.time = -1
        while self.comm.recv(source = 0) == "step":
            self.time+=1
            self.step()
            self.comm.send("done", dest = 0)
        
        time.sleep(2)
        self.cleanup()
    
    def make_operators(self):
        self.relationship_operator = OperatorsAlt.RelationshipOperatorAlt(self)
        self.infection_operator = Operators.InfectionOperator(self)
        self.time_operator = Operators.TimeOperator(self)
            
    def add(self, agent):
        self.agents[agent.attributes["NAME"]] = agent
        self.network.add_node(agent)
        
        #location
        agent.attributes["LOC"] = np.random.rand(1,2) # should be generic to dimensions
        self.relationship_operator.update_grid_queue_for(agent)
        
        
