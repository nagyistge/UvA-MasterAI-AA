# Assignment:   MultiAgent Planning&Learning
# Course:       Autonomous Agents 2012-2013
# Education:    Master Artificial Intelligence
# By:           Steven Laan
#               Auke Wiggers
#               Camiel Verschoor
#
# File:         environment.py
# Description:  Base class of the environment.
from Predator import Predator
from Prey import Prey
try:
    import gurobipy as grb
except:
    print 'No Gurobi = no minimax-Q-learning'
    
import time
import random
from collections import defaultdict

class Environment:
    '''
    Creates an instance of the environment. Default an eleven by eleven grid
    is used. The default position for the prey is (5,5).
    '''
    def __init__( self, 
                  width=11, 
                  height=11, 
                  preyLocation=(5,5), 
                  predatorLocation=(0,0),
                  numberOfPredators=1  ):
                      
        assert numberOfPredators > 0
        assert numberOfPredators < 5
        assert type(numberOfPredators) == int        
        
        self.width  = width
        self.height = height
        self.numberOfPredators = numberOfPredators
        
        self.Prey = Prey( self, preyLocation )
        self.PredatorLocations = [(0,0), (10,0), (0,10), (10,10)]
        self.Predators = [Predator(self, self.PredatorLocations[i]) \
                          for i in range(self.numberOfPredators)]        

        self.Agents = [self.Prey] + self.Predators

        
    def qLearning( self, 
           episodes, 
           optimistic_init=15,
           verbose=False,
           return_num_of_steps=True,
           learning_rates=None):
        '''
        Q, return_list <- qLearning(episodes, 
                                    optimistic_init=15,
                                    verbose=False,
                                    return_num_of_steps=True,
                                    learning_rates=None)
        
        Implementation of Q-learning. Integer optimistic_init is used 
        to initialize Q, and should be larger than zero. Verbose is a boolean
        indicating whether updates should be given by the system. 
        Return_num_of_steps indicates whether the function should return the 
        number of steps (if true), or the performance (if false).
        
        learning_agents is a list containing booleans, indicating which agents
        should learn. The first agent is the prey, 
        '''
        state_total = 121**self.numberOfPredators

        # Set the learning rate of each agent
        learning_rates = [0.3 for i in xrange(len(self.Agents))] if \
                         learning_rates == None else learning_rates
        for i in xrange(len(self.Agents)):
            self.Agents[i].QLearning.alpha = learning_rates[i]
            self.Agents[i].QLearning.optimistic_value = optimistic_init
        
        return_list = list()        
        now = time.time()            
        # For a number of episodes
        for n in xrange(1,episodes+1):
            
            if verbose and n % 1000 == 0:
                print 'Episode {0}, time taken: {1}.'.format(n, time.time()-now)
                now = time.time()
                print 'Total number of states encountered: {0} out of {1}.'\
                      .format(len(self.Agents[0].QLearning.Q), state_total)
                
            # Initialize the beginstate s semi-randomly
            self.resetAgents()            
            s = self.gameState()                                         

            game_over = False
            step_number = 0           
            
            # Run through one episode
            while not game_over:      
                step_number += 1
        
                # All agents take one QLearning step simultaneously, but we
                # calculate the state that results from the prey's new position
                actions = list()              
                for Agent in self.Agents:   

                    # Find a sample action (epsilon-greedy) given the state
                    a = Agent.getActionEpsilonGreedy(s)
                    
                    # Perform that action
                    Agent.performAction(a)

                    # And save it                    
                    actions.append(a)            
                    
                # Derive the new state from updated agent locations
                s_prime = self.gameState()
                
                # This results in reward
                r, game_over = self.reward(s_prime)

                # Update Q for each agent
                for i in xrange(len(self.Agents)):  
                    self.Agents[i].updateQ( s, 
                                            actions[i], 
                                            s_prime, 
                                            r )
                #if s == ((0,1),):
                #    print 'Game over?', game_over, '\n'
                #    print r
                #    raw_input()
                # Update the state
                s = s_prime
                
            if return_num_of_steps:       
                return_list.append(step_number)
            else:
                total_return = list()
                # Only the prey and one predator matter, since return is the
                # same for every predator 
                for Agent in self.Agents[0:2]:
                    total_return.append( r * Agent.QLearning.alpha ** step_number)
                # Negate prey reward, as reward function is from predator POV
                total_return[0] = -total_return[0]
                
                return_list.append(total_return)
           
        Q_agents = list()
        for Agent in self.Agents:
            Q_agents.append(Agent.QLearning.Q)
            
        return Q_agents, return_list
           
    def minimaxQLearning( self ):
        done = False

        alpha = 0.8
        gamma = 0.8        
        
        s = 'starting_state'
        Q = defaultdict()
        V = defaultdict()
        
        # Set of own actions and opponent actions
        A = set()        
        O = set() 
        
        if prey:
            A = self.Prey.actions
            if len( self.Predators ) == 2:
                O = set( [ (a1,a2) for a1 in A for a2 in A ] )
        else:
            O = self.Prey.actions
            if len( self.Predators ) == 2:
                A = set( [ (a1,a2) for a1 in O for a2 in O ] )

        
        while not done:
            # In state s take action a and opponent action o to get reward r and
            # state s_prime
            a = myTeamAction( s )
            o = opponentTeamAction( s )
            r, s_prime = self.step( s, a, o )
            
            Q[s][a,o] = (1-alpha) * Q[s][a,o] + alpha * (r + gamma* V[s_prime])
           
            # Use linear programming to obtain optimal policy for this state
            try:
                # Create a new model
                m = grb.Model("MultiAgentMinimax")
                
                # Create variables
                pi = dict()
                for a in A:
                    pi[a] = m.addVar( 0.0, 1.0, vtype = grb.GRB.CONTINUOUS, name = a )
            
                # Integrate new variables
                m.update()            
            
                # Set objective
                m.setObjective( grb.LinExpr( [ ( Q[s][(a,o)], pi[a] ) for o in O for a in A ] ), grb.GRB.MAXIMIZE)
            
                # Add constraint: Sum_a pi(a) = 1
                expr = grb.quicksum( m.getVars() )
                m.addConstr( expr == 1, "Total probability" )
            
                # Add more constraints
                for o in O:
                    expr = grb.LinExpr( [ (Q[s][(a,o)], pi[a]) for a in A ] )
                    m.addConstr( expr >= 0 )
                
                m.optimize()
            
                for v in m.getVars():
                    #print v.varName, v.x
                    policy[s][tuple(v.varName)] = v.x
            
                #print 'Obj:', m.objVal
            
            except grb.GurobiError:
                print 'Error reported'
                
            # Update V
            V[s] = min( Q[s] )
            
    def reward( self, s ):
        '''
        r, game_over <- reward(s)

        Returns the reward for a given state containing location of 
        the predators and prey. Return is the reward of the predator(s), as 
        this is a zero-sum-game, the reward of the predator is simply the 
        negated reward of the prey. Boolean game_over indicates if the state 
        is absorbing.
        '''
        # Prioritize confusion of predators            
        if len(s) != len(set(s)):
            return -10, True
        elif (0,0) in s:
            return 10, True
        else:
            return 0, False
 
    def deriveState( self, locations ):
        '''
        state <- deriveState( locations )        
        
        Derive the state based on the locations of the prey and the predators.
        '''
        state = list()
        prey_x, prey_y = locations[0]

        for i in xrange( self.numberOfPredators ):
            predator_x, predator_y = locations[i+1]
            x = ( ( 5 + prey_x - predator_x ) % ( self.width ) ) - 5
            y = ( ( 5 + prey_y - predator_y ) % ( self.height ) ) - 5
            state.append( (x, y) )

        return tuple(state)

    def gameState( self ):
        '''
        state <- deriveState( gameState ) 
        
        Derives the gamestate based on agents location
        '''
        state = list()
        prey_x, prey_y = self.Prey.location
        for Predator in self.Predators:
            predator_x, predator_y = Predator.location
            x = ( ( 5 + prey_x - predator_x ) % ( self.width ) ) - 5
            y = ( ( 5 + prey_y - predator_y ) % ( self.height ) ) - 5
            state.append( (x, y) )

        return tuple(state)

    def resetAgents(self):
        '''
        Reset the position of the prey and predator in this environment.        
        '''
        self.Prey.location = (5,5)
        for Predator in self.Predators:
            Predator.location = (random.randint(-5,5), random.randint(-5,5))        
    
    def simulateEnvironment(self):
        ''''
        simulateEnvironment(reset=False)

        Simulate the environment for one step. Location of each agent is 
        updated. Returns a list of agent locations. 
        '''                
        s = self.gameState()
        
        for Agent in self.Agents:
            # Get an action based on Q
            a = Agent.getActionEpsilonGreedy(s)
            # Update location
            Agent.performAction(a)