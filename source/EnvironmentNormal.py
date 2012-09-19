# Assignment:   Single Agent Planning
# Course:       Autonomous Agents 2012-2013
# Education:    Master Artificial Intelligence
# By:           Steven Laan
#               Auke Wiggers
#               Camiel Verschoor
#
# File:         environment.py
# Description:  Base class of the environment.

from predator import Predator
from prey import Prey

class EnvironmentNormal:
    '''
    Creates an instance of the environment. Default an eleven by eleven grid
    is used. The default position for the prey is (5,5).
    '''
    def __init__( self, width=11, height=11, preyLocation=(5,5), 
                  predatorLocation=(0,0) ):
        self.width  = width
        self.height = height
        S,terminal_states = self.getStates()        
        self.S = S
        self.terminal_states = terminal_states
                
        
        self.predator = Predator( self, predatorLocation )
        self.prey = Prey( self, preyLocation )
        
    def getState( self ):
        '''Returns the current environment state.'''
        # Create state
        predator_x, predator_y = self.predator.getLocation()
        prey_x, prey_y = self.prey.getLocation()
        
        # Retrieve predator positions
        s = (predator_x, predator_y, prey_x, prey_y)
        
        return s
        
    def getStates(self):
        '''
        Gets the entire statespace in two sets, the first containing the non-terminal states and the second containing terminal states.
        '''
        S = set()
        terminal_states = set() 
        for i in xrange( self.width ):
            for j in xrange( self.height ):
                for k in xrange( self.width ):
                    for m in xrange( self.height ):
                        s = (i,j,k,m)                 
                        if i == k and j == m:
                            terminal_states.add( s )
                        else:
                            S.add( s )
        return S, terminal_states
    
    def reward( self, s, a, s_prime ):
        '''
        Returns the reward for a given future 4d state containing location of 
        the predator and prey. In this case, state and action are actually 
        redundant but are added for the sake of completeness. 
        '''
        print s_prime
        if (s_prime[0], s_prime[1]) == (s_prime[2], s_prime[3]):
            return 10
        return 0

    def nextStates( self, s, a ):
        new_state = self.predator.performAction( s, a )
        return self.prey.getPossibleActions( new_state )
          