import numpy.random as random
import numpy as np
import simpactpurple
import OperatorsDistributed
import time as Time
import multiprocessing

class CommunityDistributed(simpactpurple.Community):
    """
    The main object for a distributed community simulation."
    """

    def __init__(self, comm, primary, others, migration = False):
        simpactpurple.Community.__init__(self)
        #Distributed parameters
        self.comm = comm
        self.rank = comm.Get_rank()
        self.primary = primary
        self.is_primary = self.rank == primary
        self.others = others
        self.size = len(self.others) + 1
        self.migration = migration
        self.transition_probabilities = np.ones((self.size,self.size))/self.size
        
        #print "hello from rank",self.rank, "my primary is", self.primary
        #all other parameters inherited
		
    def start(self):
        """
        Initialize the transition matrix based on transition probabilities.
        """
        self.transition = np.cumsum(self.transition_probabilities, axis=0)
        simpactpurple.Community.start(self)
    
    def broadcast(self, message):
        """
        A function which sends message to all nodes. This is necessary b/c
        comm.bcast has buggy performance.
        """        
        for other in self.others:
            self.comm.send(message, dest = other)
            
    def update_recruiting(self, rate):
        """
        Change the number of agents to recruit during relationship operator's
        step.
        """
        if self.is_primary:
            #1. Calculate recruit numbers
            nodes = self.size
            recruit = np.ceil(self.INITIAL_POPULATION*rate)
            per_node_float = recruit/nodes
            per_node_int = int(recruit)/nodes
            fraction = per_node_float - per_node_int
            ceils = int(fraction*nodes)  # the number of nodes that get the floor
            floors = int(nodes - ceils)  # the number of nodes that get the ceil
            
            #2. Send recruit number
            self.recruit = int(np.floor(per_node_float))  # primary takes the last floor
            for other in self.others[:floors-1]:
                self.comm.send(('recruit',int(np.floor(per_node_float))), dest = other)
            for other in self.others[floors-1:]:
                self.comm.send(('recruit',int(np.ceil(per_node_float))), dest = other)
        else:
            #listen for recruit number
            msg, data = self.comm.recv(source = self.primary)
            self.recruit = data
    
    def make_population(self, size):
        """
        Same as original, except non-primary communities listen for added
        agents instead of making agents themselves.
        """
        if self.is_primary:
            simpactpurple.Community.make_population(self, size)
            if self.time < 0:
                self.broadcast(('done','making population')) 
                if self.migration:
                    self.comm.send(('done','making population'), dest = 0)
        else:
            self.listen('initial population', self.primary)

    def add_to_simulation(self, agent):
        """
        Save the agent's name for future reference, add to network, assign
        a location, and add to grid queue.
        """
        #add primary community number as prefix to agent's name (for migration)
        if type(agent.name) == type(0):
            agent.primary = self.primary
            agent.name = str(self.primary) + "-" + str(agent.name)
        
        #save agent
        self.agents[agent.name] = agent
        self.network.add_node(agent)
        
        #assign a grid queue
        grid_queue = [gq for gq in self.grid_queues.values() if gq.accepts(agent)][agent.sex]
        agent.grid_queue = grid_queue.index
       
        #assign a partition
        partitions = list(self.others)
        partitions.append(self.primary)  # only primary calls this so same as self.rank
        agent.partition = partitions[random.randint(len(partitions))]
        if agent.partition is not self.rank:
            self.comm.send(('add_to_simulation',agent), dest = agent.partition)
        self.add_to_grid_queue(agent)        
        
        if self.migration:  # and not an migration add
            agent.attributes["MIGRATION"] = [(self.time, 0, self.rank)]
            self.comm.send(('add',agent), dest = 0)

        #add to infected agents list if applicable            
        if agent.time_of_infection < np.inf:
            self.infection_operator.infected_agents.append(agent)
        
    def add_to_grid_queue(self, agent):
        """
        Find the appropriate grid queue for agent. Called by 
           1. Time Operator - when agent graduates to the next grid queue
           1.5 Time Operator - when relationship with removed is dissolved
           2. Relationship Operator - a relationship is dissolved
           3. Community - in make_population in the mainloop
        """
        #check that agent in community boundaries
        if agent.partition is not self.rank:
            self.comm.send(('add_to_grid_queue',agent.name), dest = agent.partition)  # send to other community
        else:
            self.pipes[agent.grid_queue].send("add")
            self.pipes[agent.grid_queue].send(agent)
        
    def listen_all(self, for_what):
        """
        Method for receiving messages from all other communities.
        """
        for other in self.others:
            self.listen(for_what, from_whom = other)
    
    def listen(self, for_what, from_whom):
        """
        Method for receiving messages from other communities and responding
        accordingly.
        """
        #print "v=== listen for",for_what,"| FROM",from_whom,"ON",self.rank,"|time",self.time,"===v"
        msg, data = self.comm.recv(source = from_whom)  # data depends on msg
        while True:
            #print "  > listening on",self.rank,"| msg:",msg,"data:",data
            if msg == 'done':
                break
            
            #parse message and act            
            if msg == 'add_to_simulation': # primary to non-primary
                agent = data
                self.agents[agent.name] = agent
            elif msg == 'add_to_grid_queue': # primary to non-primary
                agent = self.agents[data]
                self.add_to_grid_queue(agent)
            elif msg == 'remove_from_simulation': #non-primary to primary
                agent_name = data
                agent = self.agents[agent_name]
                self.time_operator.remove(agent)
                self.time_operator.replace(agent)
            elif msg == 'remove_from_grid_queue': # primary to non-primary
                agent_name = data  # data is agent name here
                agent = self.agents[agent_name]                
                agent_pipe = self.pipes[agent.grid_queue]
                agent_pipe.send("remove")
                agent_pipe.send(agent_name)
            elif msg == 'add_relationship':  # non-primary to primary
                relationship = data  # data is relationship tuple here
                agent1 = self.agents[relationship[0]]  # look up name
                agent2 = self.agents[relationship[1]]
                self.relationship_operator.form_relationship(agent1, agent2)
            elif msg == 'push':
                agent = data  # data is agent object here
                self.main_queue.push(agent.grid_queue, agent)
            else:
                raise Exception,"Unknown msg received: " + msg
            
            msg, data = self.comm.recv(source = from_whom)  # listen for next message
        #print "^=== listen for",for_what,"| END on",self.rank,"|time",self.time,"======^" 
        #print

    def step(self):
        """
        Take a single time step (one week) in the simulation. 
        """
        #1. Proceede normally
        simpactpurple.Community.step(self)
            
        #2. Migration operations
        if not self.migration:
            return

        if self.is_primary:
            self.migration = False  # temp disable 'add' and 'remove' messages to MO
            
            self.comm.send(('done','updating'), dest = 0)
#            if self.rank == 1:
#                print '-----primary',self.rank,'migration operations-----'
            
            #0.1 Remove some agents (migrate away)
            removals = self.comm.recv(source = 0)
#            if self.rank == 1:
#                print self.rank,"  received removals:",[a.name for a in removals]

            for removed in removals:
                agent = self.agents[removed.name]
                #send remove to grid queue in addition to time op remove
                if agent.partition is not self.rank:
                    self.comm.send(('remove_from_grid_queue',agent.name), dest = agent.partition)
                else:
                    self.pipes[agent.grid_queue].send("remove")
                    self.pipes[agent.grid_queue].send(agent.name)                    
                self.time_operator.remove(agent)
                del self.agents[removed.name]
                
            #0.2 Add some agents (migrate in)
            additions = self.comm.recv(source = 0)
#            if self.rank == 1:
#                print self.rank,"  received additions:",[a.name for a in additions]
#                print
            for agent in additions:
                self.add_to_simulation(agent)
                #print "    -",agent.name,"in network:",agent in self.network
            self.migration = True
            
#            if self.rank == 1:
#                print "=====",self.time,"====="
#                print 'removals:', [(a.name, a.time_of_infection) for a in removals]
#                print 'additions:', [(a.name, a.time_of_infection) for a in additions]    
#                print "===========" 
#                print              
            
            #0.3 finish
            self.broadcast(('done','migration updating'))
            #print '-----end migration operations----------'
        else:
            self.listen('migration updates', self.primary)
            
    def make_operators(self):
        """
        Make the distributed operators necessary for a distributed simulation.
        """
        self.relationship_operator = OperatorsDistributed.RelationshipOperator(self)
        self.infection_operator = OperatorsDistributed.InfectionOperator(self)
        self.time_operator = OperatorsDistributed.TimeOperator(self)
