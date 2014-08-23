import numpy.random as random
import numpy as np
import simpactpurple
import simpactpurple.GridQueue as GridQueue
import OperatorsDistributed
import simpactpurple.Operators
import time as Time

def ServeQueue(master, comm):
    """
    An function to waits for queues to serve.
    """
    msg = comm.recv(source = master)
    while not msg == 'done':
        gq = msg
        pipe = MPIpe(master, comm)
        GridQueue.listen(gq, pipe)
        msg = comm.recv(source = master)

class MPIpe():
    """
    A pipe based on the mpi4py module that acts similarly to the 
    multiprocessing.Pipe. This is done to avoid the os.fork() used by
    multiprocessing.
    """
    def __init__(self, rank, comm):
        self.rank = rank
        self.comm = comm
        
    def send(self, msg):
        self.comm.send(msg, dest=self.rank)
    
    def recv(self):
        return self.comm.recv(source=self.rank)

class CommunityDistributed(simpactpurple.Community):
    """
    The main object for a distributed community simulation."
    """

    def __init__(self, comm, primary, others, **migration):
        simpactpurple.Community.__init__(self)
        
        #Distributed parameters
        self.comm = comm
        self.rank = comm.Get_rank()
        self.primary = primary
        self.is_primary = self.rank == primary
        self.others = others
        self.size = len(self.others) + 1
        self.transition_probabilities = np.ones((self.size,self.size))/self.size
        self.name_count = 0
        self.MAX_AGE = 40  # dictated by number of slots on helium -- 16
        
        #migration variables
        if len(migration)>0:
            self.migration = True
            self.other_primaries = migration['other_primaries']
            self.timing = migration['timing']
            self.gravity = migration['gravity']
            self.probabilities = self.gravity / np.sum(self.gravity, axis=0)
            self.transition = np.cumsum(self.probabilities, axis=0)
            #self.past_partners = {}  # for reforming relationships -- should be in start
        
        #queue ranks
        slots_per_node = 16  # 16 on neon, 12 on helium
        total_communities = self.comm.Get_size()/slots_per_node
        self.grid_queue_ranks = range(self.rank+total_communities, self.comm.Get_size(), total_communities)
        
    def spawn_process_for(self, gq):
        """
        Spawns a new process via MPI ranks with communication via an MPIpe.
        In a seperate function to accomadate distributed version.
        """
        gqrank = self.grid_queue_ranks.pop()
        self.comm.send(gq, dest = gqrank)
        pipe = MPIpe(gqrank, self.comm)
        self.pipes[gq.index] = pipe
                
    def make_operators(self):
        """
        Make the distributed operators necessary for a distributed simulation.
        """
        self.relationship_operator = OperatorsDistributed.RelationshipOperator(self)
        self.infection_operator = OperatorsDistributed.InfectionOperator(self)
        self.time_operator = OperatorsDistributed.TimeOperator(self)
        
    def make_population(self, size):
        """
        Same as original, except non-primary communities listen for added
        agents instead of making agents themselves.
        """
        if self.is_primary:
            simpactpurple.Community.make_population(self, size)
            if self.time < 0:
                self.broadcast(('done','making population'))
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
            agent.name = str(self.primary) + "-" + str(self.name_count)
            self.name_count+=1
        
        #save agent
        self.agents[agent.name] = agent
        self.network.add_node(agent)
        
        #assign a grid queue and partition
        grid_queue = [gq for gq in self.grid_queues.values() if gq.accepts(agent)][agent.sex]
        agent.grid_queue = grid_queue.index
        partitions = list(self.others)
        partitions.append(self.primary)  # only primary calls this so same as self.rank
        agent.partition = partitions[random.randint(len(partitions))]
        
        # add agent to simulation
        if agent.partition is not self.rank:
            self.comm.send(('add_to_simulation',agent), dest = agent.partition)
        self.add_to_grid_queue(agent)      
        if self.migration and not hasattr(agent, 'away'):
            self.add_migration(agent)
        
    def add_to_grid_queue(self, agent):
        """
        Find the appropriate grid queue for agent. Called by 
           1. Time Operator - when relationship with removed is dissolved
           2. Relationship Operator - a relationship is dissolved
           3. Community - in make_population in the mainloop
        """
        #check that agent in community boundaries
        if agent.partition is not self.rank:
            self.comm.send(('add_to_grid_queue',agent.name), dest = agent.partition)  # send to other community
        else:
            self.pipes[agent.grid_queue].send("add")
            self.pipes[agent.grid_queue].send(agent)
            
    def add_migration(self, agent):
        agent.home = self.rank
        if agent.sex == 1:
            agent.away = agent.home
        else:
            agent.away = [int(v) for v in np.random.random() < self.transition[:,self.rank]].index(1)
            
        if agent.home != agent.away:
            self.comm.send('add_to_grid_queue',agent))
            
    def active(agent):
        #check active/inactive status for migration
        if not self.migration:
            return True
        home_time = self.master.timing[agent.home,agent.home]
        away_time = self.master.timing[agent.away,agent.home]
        if self.master.rank == agent.home:
            return self.master.time/(home_time+away_time) <= agent.home_time:
        else: #agent is away
            return self.master.time/(home_time+away_time) > agent.home_time:
            
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
        
    def broadcast(self, message):
        """
        A function which sends message to all nodes. This is necessary b/c
        comm.bcast has buggy performance.
        """        
        for other in self.others:
            self.comm.send(message, dest = other)
            
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
        print "v=== listen for",for_what,"| FROM",from_whom,"ON",self.rank,"|time",self.time,"===v"
        msg, data = self.comm.recv(source = from_whom)  # data depends on msg
        while msg != 'done':
            print "  > listening on",self.rank,"| msg:",msg,"data:",data
            
            #parse message and act            
            if msg == 'add_to_simulation': # primary to non-primary
                agent = data
                self.agents[agent.name] = agent
            elif msg == 'add_to_grid_queue': # primary to non-primary
                agent = self.agents[data]
                self.add_to_grid_queue(agent)
            elif msg == 'add_migration':
                agent = data
                self.add_to_simulation(agent)
            elif msg == 'infection':
                agent = self.agents[data]
                agent.time_of_infection = self.time
                self.infection_operator.infected_agents.append(agent)
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
        print "^=== listen for",for_what,"| END on",self.rank,"|time",self.time,"======^" 
        print

    def run(self, timing=False):
        simpactpurple.Community.run(self)
        #send "done" to all grid queue ranks
        slots_per_node = 16  # 16 on neon, 12 on helium
        total_communities = self.comm.Get_size()/slots_per_node
        grid_queue_ranks = range(self.rank+total_communities, self.comm.Get_size(), total_communities)
        for r in grid_queue_ranks:
            self.comm.send('done', dest = r)
        
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
            
           
            self.migration = True          
            
            #0.3 finish
            self.broadcast(('done','migration updating'))
        else:
            self.listen('migration updates', self.primary)

