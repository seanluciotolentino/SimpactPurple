"""
The module for the GridQueue class and function for listening.
"""
import random
import PriorityQueue #lucio's implementation
import numpy as np
import sys

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
            pipe.send(gq.my_agents)
        elif action == "time":
            gq.time = pipe.recv()
        elif action == "terminate":
            break
        else:
            raise ValueError, "GridQueue received unknown action:" + action


class GridQueue():
    """
    A data structure for holding agents of similar age and sex.
    """

    def __init__(self, top, bottom, sex, index):#, hazard):
        self.top = top
        self.bottom = bottom
        self.my_age = (top + bottom)/2
        self.my_sex = sex
        self.my_index = index
        #self.hazard = hazard  #-- functions can't be pickled

        #Data structures for keeping track of agents
        self.my_agents = PriorityQueue.PriorityQueue()  # populated with agents
        self.names = {}
        self.previous = None
        self.time = 0
    
    def recruit(self):
        """
        Returns the agent name from the queue that has been waiting the
        longest.  Returns None if there are no agents in the queue, or
        all the agents in it's queue have been returned this round. 
        """
        #0. return agents for main queue (if any)
        if self.my_agents.empty(): 
            #print "  GQ",self.my_index,"return empty"
            return None
        
        #1. reorganize if dissimilar from previous
        if self.previous is not None: 
            self.previous = None
            agents = list(self.my_agents.heap)  # copy the list
            self.my_agents.clear()
            for hazard, agent in agents:
                self.my_agents.push(agent.last_match,agent)
        
        agent = self.my_agents.pop()[1]
        if agent.last_match == self.time:
            self.my_agents.push(self.time,agent)
            #print "  GQ",self.my_index,"already returned all agents"
            return  None  # already returned on this round
        else:
            agent.last_match = self.time
            self.my_agents.push(agent.last_match,agent) 
            #print "  GQ",self.my_index,"returning an agent"
            return agent.attributes["NAME"]

    def enquire(self, suitor):
        """
        Returns the agent name of an agent who would form a relationship
        with *suitor*. Returns None if there are no agents, or none of the
        agents in the grid queue don't accept.
        """
        #empty queue?
        if self.my_agents.empty():
            return None
        
        #Resort if dissimilar
        if self.previous is None or self.previous.grid_queue != suitor.grid_queue:
            suitor_age = self.age(suitor)
            ma = (suitor_age + self.my_age) / 2
            ad = suitor_age - self.my_age

            #flip coins for agents
            agents = list(self.my_agents.heap)
            self.my_agents.clear()
            for old_hazard, agent in agents:  # old_hazard is not needed
                hazard = self.hazard(agent, suitor, age_difference = ad, mean_age = ma)
                decision = int(random.random() < hazard)
                self.my_agents.push(-decision,agent)
        self.previous = suitor

        #Return an accepting agent
        top = self.my_agents.top()
        accept = top[0]
        match = top[1]
        match_name = match.attributes["NAME"]
        suitor_name = suitor.attributes["NAME"]
        if match_name == suitor_name:
            if self.my_agents.length() <= 1:
                return None
            else:
                #try to pop next in the queue
                suitor_accept, suitor = self.my_agents.pop()
                accept, match = self.my_agents.top()
                match_name = match.attributes["NAME"]
                self.my_agents.push(suitor_accept, suitor)
        
        if accept == 0:  
            return None
        else:
            return match_name
            
    def add(self, agent):
        """
        Add *agent* to the priority queue.
        """
        #Verify that this agent isn't already in the queue
        agent_name = agent.attributes["NAME"]
        if agent_name in self.names.keys() and self.names[agent_name]:
            return

        #add with the appropriate priority
        self.names[agent_name] = agent
        if self.previous is not None:  # adding to "matching" queue
            self.my_agents.push(-1, agent)        
        else:  # adding to a "time since last" queue
            self.my_agents.push(agent.last_match, agent)
            
    def remove(self, agent_name):
        """
        Remove the agent with the name *agent_name* from the priority queue.
        """
        #Verify that this agent is in the queue
        if agent_name in self.names.keys() and self.names[agent_name]:
            self.my_agents.remove(self.names[agent_name])
            self.names[agent_name] = None
                
    def contains(self, agent_name):
        """
        Returns whether this grid queue contains an agent with the name
        *agent_name*.
        """
        if agent_name in self.names:
            agent = self.names[agent_name]
            return self.my_agents.contains(agent)        
        else:
            return False
        
    def accepts(self,agent):
        """
        Returns whether *agent* is qualified for this grid queue.
        """
        return self.age(agent) >= self.bottom and self.age(agent) < self.top
        
    def age(self,agent):
        """
        Returns the age of the *agent*
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
            agent1_age = self.grid_queues[agent1.grid_queue].my_age
            agent2_age = self.grid_queues[agent2.grid_queue].my_age
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
        pad = (1 - (2*agent1.sex))* self.preferred_age_difference  # correct for perspective
        top = abs(age_difference - (pad*self.preferred_age_difference_growth*mean_age) )
        h = np.exp(self.probability_multiplier * top ) ;
        return (agent1.sex ^ agent2.sex)*h
            
    #Functions for debuging
    def agents_in_queue(self):
        return [str(a.attributes["NAME"]) for p,a in self.my_agents.heap]
