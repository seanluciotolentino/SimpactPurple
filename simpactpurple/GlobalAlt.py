import Agent
import numpy as np
import random
import time

class Global:
    """
    The Global class is reponsible for generating the initial population as well
    as dealing with communication and syncing between communities. Each time
    step the Global object sends updates to communities, receives replies, and
    processes the replies for the next rounds updates.
    """
    
    def __init__(self, comm):        
        #global specific 
        self.comm = comm
        self.community_nodes = range(1,3)
        self.grid_nodes = []#range(5,9)
        
        #MODEL PARAMETERS
        self.NUMBER_OF_YEARS = 30

        #MODEL POPULATION
        self.INITIAL_POPULATION = 500
        self.AGENT_ATTRIBUTES = {}
        
        #MODEL OPERATORS
        #relationship operator
        self.SEXES = 2
        self.MIN_AGE = 15
        self.MAX_AGE = 65
        self.BIN_SIZE = 5
        self.MAIN_QUEUE_MAX = 0.1  # proportion of initial population
        
        #infection operator
        self.INFECTIVITY = 0.1
        self.INTIAL_PREVALENCE = 0.1
        self.SEED_TIME = 0 # in years        
        
        #time operator
        self.TIME = 0
            
    def run(self):
        """
        Initialize community and grid server processes, execute
        main loop, then close connections.
        """
        #initialize roles and master/servant relationships
        self.setup()

        #mainloop:
        for t in range(int(self.NUMBER_OF_YEARS*52)):
            print "-----time",t,"------"
            self.TIME = t

            #send "step" signal
            for c in self.community_nodes:
                self.comm.send("step", dest = c)

            #wait for "done" signal from communities
            for c in self.community_nodes:
                assert self.comm.recv(source=c)=="done"

            #perform migrations
            #...no implemented yet...

        #post clean up
        self.tear_down()


    def setup(self):
        """
        Initial setup implementation.
        Global (0)
            Community (1)
                GridServer (1)
                GridServer (5)
            Community (2)
                GridServer (2)
                GridServer (6)
            Community (3)
                GridServer (3)
                GridServer (7)
            Community (4)
                GridServer (4)
                GridServer (8)
        """
        #send community roles and their servant nodes
        for c in self.community_nodes:
            self.comm.send("community", dest = c)
            self.comm.send(c, dest = c)
            #self.comm.send(c+4, dest = c)
            self.comm.send("run", dest = c)

        #send grid server roles and their master nodes
        for g in self.grid_nodes:
            self.comm.send("grid", dest = g)
            self.comm.send(g-4, dest = g)

    def tear_down(self):
        """
        Send signal for communities to finish their simulation.
        """
        for c in self.community_nodes:
            self.comm.send("terminate", dest = c)
        
        time.sleep(5)  # give them time to close their pipes
        for g in self.grid_nodes:  # grids
            self.comm.send("terminate", dest = g)


            
