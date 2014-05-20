"""
The module for the GridQueue class and function for listening.
"""
import random
import PriorityQueue  # lucio's implementation
import numpy as np

def listen(gq, pipe):    
    """
    Listens for an action from *pipe* to perform on *gq*. *semaphore* object
    passed by relationship operator which creates it -- allows simulation to
    use less than all the cores of the machine. 
    """
    while True:
        action = pipe.recv()
        if action == "recruit":
            pipe.send(gq.recruit())
        elif action == "enquire":
            pipe.send(gq.enquire(pipe.recv()))
        elif action == "add":
            gq.add(pipe.recv())
        elif action == "remove":
            gq.remove(pipe.recv())
        elif action == "contains":
            pipe.send(gq.contains(pipe.recv()))
        elif action == "queue":
            pipe.send(gq.agents)
        elif action == "time":
            gq.time = pipe.recv()
        elif action == "oldest":
            gq.oldest(pipe)            
        elif action == "terminate":
            break
        else:
            raise ValueError, "GridQueue received unknown action:" + action


class GridQueue():
    """
    A data structure for holding agents of similar age and sex.
    """
    def __init__(self, top, bottom, index):
        self.top = top
        self.bottom = bottom
        self.middle = (top+bottom)/2.0
        self.index = index

        #Data structures for keeping track of agents
        self.agents = PriorityQueue.PriorityQueue()  # populated with agents
        self.names = {}
        self.previous = None
        self.time = 0
        
        #additionally hazard variables and max_age (for removal) are set
    
    def recruit(self):
        """
        Returns the agent name from the queue that has been waiting the
        longest.  Returns None if there are no agents in the queue, or
        all the agents in it's queue have been returned this round. 
        """
        #0. return agents for main queue (if any)
        if self.agents.empty(): 
            return None
        
        #1. reorganize if dissimilar from previous
        if self.previous is not None: 
            self.previous = None
            agents = list(self.agents.heap)  # copy the list
            self.agents.clear()
            for hazard, agent in agents:
                self.agents.push(agent.last_match,agent)
        
        agent = self.agents.pop()[1]
        if agent.last_match == self.time:
            self.agents.push(agent.last_match,agent)
            return  None  # already returned on this round
        else:
            agent.last_match = self.time
            self.agents.push(agent.last_match,agent) 
            return agent.name

    def enquire(self, suitor):
        """
        Returns the agent name of an agent who would form a relationship
        with *suitor*. Returns None if there are no agents, or none of the
        agents in the grid queue don't accept.
        """
        #1. empty queue?
        if self.agents.empty():
            return None
        
        #2. Resort if dissimilar from previous suitor
        if self.previous is None or self.previous.grid_queue != suitor.grid_queue:
            suitor_age = self.age_of(suitor)
            ma = (suitor_age + self.age()) / 2
            ad = suitor_age - self.age()

            #flip coins for agents
            agents = list(self.agents.heap)
            self.agents.clear()
            for old_hazard, agent in agents:  # old_hazard is not needed
                hazard = self.hazard(agent, suitor, age_difference = ad, mean_age = ma)                
                if random.random() < hazard:                    
                    self.agents.push(agent.last_match,agent)
                else:
                    self.agents.push(np.inf, agent)
        self.previous = suitor

        #3. Update last_match and return an accepting agent
        accept, match = self.agents.pop()        
        if accept >= np.inf:
            self.agents.push(np.inf, match)  # push back in
            return None
        
        #3. 1 Check that suitor is not match
        match_name = match.name
        suitor_name = suitor.name
        if match_name == suitor_name:
            if self.agents.length() <= 1:  # if there is no one else
                self.agents.push(match.last_match, match)
                return None
            else:  # try to return the next in line
                new_accept, new_match = self.agents.pop()
                self.agents.push(accept, match)
                if new_accept >= np.inf:
                    self.agents.push(new_accept, new_match)
                    return None                    
                accept, match = new_accept, new_match
                match_name = match.name        
        
        #4. Finally, return match
        match.last_match = self.time
        self.agents.push(match.last_match, match)  # move from top position        
        return match_name
            
    def add(self, agent):
        """
        Add *agent* to the priority queue.
        """
        #Verify that this agent isn't already in the queue
        agent_name = agent.name
        if agent_name in self.names and self.names[agent_name]:
            return

        #add with the appropriate priority
        self.names[agent_name] = agent
        self.agents.push(agent.last_match, agent)
            
    def remove(self, agent_name):
        """
        Remove the agent with the name *agent_name* from the priority queue.
        """
        #Verify that this agent is in the queue
        if agent_name in self.names.keys() and self.names[agent_name]:
            self.agents.remove(self.names[agent_name])
            self.names[agent_name] = None
            
    def oldest(self, pipe):
        """
        Go through agents and send back to communitythose that are beyond the 
        age limit (removing them along the way).
        """
        agents = list(self.agents.heap)
        for h, agent in agents:
            if self.age_of(agent) > self.max_age:
                agent_name = agent.name
                self.remove(agent_name)
                pipe.send(agent_name)
        pipe.send('done')
        
    def accepts(self,agent):
        """
        Returns whether *agent* is qualified for this grid queue.
        """
        return agent.born >= self.bottom and agent.born < self.top
        
    def age(self):
        """
        Returns the age of the grid queue.
        """
        return (self.time - self.middle)/52
        
    def age_of(self,agent):
        """
        Returns the age of the *agent*.
        """
        return (self.time - agent.born)/52      
        
    def hazard(self, agent1, agent2, **attributes):
        """
        Calculates and returns the hazard of relationship formation between
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
            
        pad = (1 - (2*agent1.sex))* self.preferred_age_difference  # correct for perspective
        top = abs(age_difference - (pad*self.preferred_age_difference_growth*mean_age) )
        h = np.exp(self.probability_multiplier * top ) ;
        
        #FOR INTERMIXING EXPLORATION:
        cm = 1
        try:
            cm = self.distance[agent1.partition][agent2.partition]
            return cm*(agent1.sex ^ agent2.sex)*h
        except AttributeError:
            print "ATTRIBUTE ERROR IN GRID QUEUE HAZARD CALCULATION"
            pass  # must have forgotten to remove this stuff
        return (agent1.sex ^ agent2.sex)*h
            
    #Functions for debuging
    def agents_in_queue(self):
        return [str(a.name) for p,a in self.agents.heap]
