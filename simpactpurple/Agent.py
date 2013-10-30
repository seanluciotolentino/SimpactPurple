import math
import numpy as np
#import interval as np # when you don't have numpy

class Agent():
    def __init__(self, attributes):
        #all these variables are set in the make_population. Initialized here
        #as None to emphasis their existence
        self.born = None
        self.gender = None
        self.dnp = None
        self.grid_queue = None;
    
        self.time_of_infection = np.Inf 
        self.last_match = -np.Inf
        self.attributes = attributes
        
    def __str__(self):
        return "Name: " + str(self.attributes["NAME"]) + " Born: " + str(round(self.born,2)) + " Gender: " + str(self.gender) #+ " GQ:" + str(self.grid_queue.my_index)

