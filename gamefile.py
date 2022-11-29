import time
from random import randint

def main(n = 3, m = 3, k = 3, automatic_players = [1,2], manual_players = [],ifdisplay = True, ifprune = False):
    """ Function to set up and run the game as specified in alpha_beta.py
    """
    game = Game(n, m, k, automatic_players, manual_players, ifdisplay =ifdisplay, ifprune = ifprune)
    computing_times, states_visited_per_turns = game.play()
    print(computing_times)
    print(states_visited_per_turns)



class Game(object):
    """
    Class representing the (m, n, k)-game.
    """


    def __init__(self, m, n, k,  automatic_players = [1, 2], manual_players = [1], ifdisplay = True, ifprune = False):
        """ Initilise the (m, n, k)-game. 
        
        This function sets the parameters of the (m, n, k)-game as specified by the User.
        
        Start the game. When creating a new Game, the user can set the game's parameters.
        The game's state is represented by a tuple of sets (set(), set()), where the first 
        set comprises moves performed by player1(max) and the second set contains moves made by player2(min). 
        Each move is represented by a tuple (coord x, coord y), where coord x is an integer reflecting the 
        projection of a point on the x-axis of the board, i.e. a column of the game-grid. This coordinate is 
        represented to the user alphabetically, so that A==first column, B==second column, and so on. 
        coord y is an integer that represents the projection of a coordinate on the y-axis of the board, 
        i.e. a row of the game-grid, where 1==first row, 2==second row, and so on. 
        The minimax algorithm will recommend a move for players in both automatic players and manual players, 
        but the user can pick what move to make.
        
        Inputs:
            - m(int): the width of the grid (size along the x-axis)
            - n(int): the height of the grid (size along the y-axis)
            - k(int): the number of consecutive gridcells (in one direction: vertical, horizontal or 
                      diagonal) that the player needs to fill on the game's grid to win the game
            - automatic_players(list): denotes how many players are going to be played automatically
                                       by the mininmax algorithm:
                                       [1, 2] - minimax algorithm is applied to both players to play automatically
                                       [1] - minimax algorithm is applied to player1, 
                                       [2] - minimax algorithm is applied to player 2
                                       [] - none of the players are played automatically
                                       if the same players are simultaneously selected to be played manually, 
                                       the algorithm will not perform the moves for them, but will suggest the most 
                                       optimal move to take (by printout)
            - manual_players(list): denotes the player to be played manually by the mininmax algorithm. If both player is 
                                    selected to be both automatic and manual at the same time, the player's moves are going 
                                    to be selected manually, but the automatic algorithm will suggest the most optimal
                                    moves to take. 
            - ifdisplay(bool): denotes if the graphical representation of the board and the game is outputted in 
                               the terminal. 
        
        Returns:


        """

        # save the inputted parameters as Game attributes 
        self.m = m
        self.n = n
        self.num_all_states = self.n * self.m
        self.k = k

        self.automatic_players = automatic_players # list of the players to be played automatically
        self.manual_players = manual_players # list of the players to be played manually
        self.ifdisplay = ifdisplay # whether the game should be graphically displayed

        # at the start, the set of possible moves include all of cells on (m,n)-grid
        self.possible_initial_moves = set([(i,j) for i in range(1,self.m+1) for j in range(1, self.n+1)]) 

        # at the start, the moves history for both player
        self.player1_move_history = set() 
        self.player2_move_history = set()

        # define the current game state given the previous history of the players
        self.game_state = (self.player1_move_history, self.player2_move_history)

        # tuple of functions to get a gridcell in a given direction and of a given stepsize 
        self.directions = (self.horizontal, self.diagonal_right, self.vertical, self.diagonal_left)

        # history of the states visited - 
        # dictionary that stores results of alpha-beta pruning and state values. 
        # It uses the frozenset of game states as keys to store the calculated utilities 
        # (value) and alpha-beta eliminations (ifcut) for each game state. 
        self.history = {} 

        # stores the utility values of each potential action that can be made
        self.action_values = {}

        self.ifprune = ifprune # if alpha-beta pruning should be applied

        self.states_visited  = 0 # counter of the game states visited
    
    def is_valid_move(self, game_state, action):
        """
        Check if a given action is valid in a given state. The action needs to be
        in bounds of the board and be an unoccupied cell.

        Inputs:
            - game_state(tuple(set(), set())): tuple containing previous game history of 2 players which represents 
                                               the current state of the game
            - action(tuple(x,y)): an action to understake - represents the coordinates of a gridcell to occupy.
                                  x - integer representing the gridcell's x-axis coordinates
                                  y - integer representing the gridcell's y-axis coordinates 

        Returns: 
            - ifvalid(boolean): True if action is valid, False if action is invalid.

        """
        x,y = action

        if (1 <= x <= self.m) and (1 <= y <= self.n) and (action not in game_state[0]) and (action not in game_state[1]): 
            return True
        else:
            return False

    def translate_move(self, action_list):
        """ Translates the actions (x,y) into the coordinates its board representation representation.
            
        Input: 
            - action(list of tuple(int, int): tuple containing integer coordinates x,y, representing the gridcell 
                                             location on the board to occupy.
        
        Returns: 
            - coordinates_string(str): string containing board representation of the action coordinates (e.g., A3, B2)

        """
        board_coordinates = []
        upper_case_offset = 64
        # translate all the optimal actions
        for x, y in action_list:
            x_board = chr(x + upper_case_offset)
            y_board = str(y)
            board_coordinates.append(x_board + y_board)
       
        # sort the board coordinates of optimal actions according in the alphabetic order
        board_coordinates.sort()

        # initialise an empty str
        coordinate_string = str()

        for coordinate in board_coordinates:
            coordinate_string += coordinate + ', '

        # for the final one, remove the coma and space and substitute it with a period.  
        return coordinate_string[:-2] + '.'


    
    def translate_input(self, input):
        """ Translates the input coordinates by the user from board representation back to the x,y coordinates. 

        Input: 
            - input(str): string containing board representation of the action coordinates (e.g., A3, B2)
        
        Returns: 
            - coordinates(tuple(int, int)): tuple containing integer coordinates x,y, representing the gridcell 
                                             location on the board to occupy.

        """
        upper_case_offset = 64
        x = ord(input[0].upper()) - upper_case_offset
        y = int(input[1])
        return(x, y)    


    
    def is_terminal(self, game_state, previous_action, current_player):

        """ Checks whether the given game state is terminal for a given player and the last action taken by this player.

        Using the previous action taken and the order of the player that took the action limits the set of combinations to check for 
        terminal state as it only considers the terminal combinations that involve the last action taken. 

        Example of terminal state in (3,3,3)-game:
                                A   B   C
                              -------------
                            3 | X | O | X | 3
                              -------------
                            2 | X | O | O | 2
                              -------------
                            1 | X | X | O | 1
                              -------------
                                A   B   C

        if the previous action was A3, we can limit our search for terminal state by looking only
        at combinations involving A3 in the terminal check (i.e. horizontal, vertical and diagonal direction from A3)


        Inputs:
            - game_state(tuple(set(), set())): tuple containing previous game history of 2 players which represents 
                                               the current state of the game
            - previos_action(tuple(x,y)): previous action taken by the player described by the x,y coordinates
                                          of the gridcell that were occipied by the move
            - current_player(int): the order of the player. If current_player = 1, then they correspond to Max 
                                   in Minimax algorithm. If current_player = 2, then they correspond to Min in 
                                   Minimax algorithm. 
        Returns: 
            - ifterminal(bool): boolean value which descibes whether the current game state is terminal 
                                if terminal = True, then the state is terminal
                                if terminal = False, then the state is not terminal
            - winner(int): order of the player who won the game
                 if winner = 1, then 'max' won
                 if winner = 2, then 'min' won
                 if winner = 0, then nbo player won and the game is tied
                 if winner = None, then terminal=False and game hasn't finished yet
        """

        self.states_visited += 1

        # initialisation
        ifterminal = False
        winner = None

        # if no previous action has been provided, the state is not terminal, and there's no winner
        if previous_action == None:
            return ifterminal, winner

        else: 
            player_idx = current_player - 1 
            move_history = game_state[player_idx] # selecting the previous history of a given player 

            x,y = previous_action # get the x and y coordinates of the gridcell filled in the previous action

            # check whether the k-length sequence is achieved along at least one of the possible directions
            # (horizontal, vertical, diagonal)

            for direction in self.directions:

                # initialise the counters 
                sequence_length = 1 #counts the length of the consequtive sequence achieved by the player in any direction
                n = 1

                while True:
                    # check if the player occupies a gridsell n-cells away in a given direction
                    if direction(x, y, n) in move_history: 
                        sequence_length += 1
                        n += 1
                    else: 
                        # if the player doesn't occupy the gridcell n-cells away, stop the sequence_length counter
                        break

                # check in the opposite direction 
                n = -1
                while True:
                    if direction(x, y, n) in move_history:
                        sequence_length += 1
                        n -= 1
                    else:
                        break

                # for a given direction, if hte sequence length reaches the k-value specified, player has won.             
                if sequence_length >= self.k:
                    ifterminal = True
                    winner = current_player
                    break
            
            #if no terminal states has been reached but all the grid cells has been occupied, it's a tie. 
            if not ifterminal and len(game_state[0]) + len(game_state[1]) == self.num_all_states:
                winner = 0 # tie
                ifterminal = True

            return ifterminal, winner


    def get_possible_actions(self, game_state):
        """ Calculates the set of possible next actions (moves) using a given game state
        
        It is calculated as the difference between the possible actions on an empty board (self.possible_initial_moves)
        and the occupied cells (history of the moves made by both players)

        Input:
            - game_state(tuple(set(), set())): tuple containing previous game history of 2 players which represents 
                                               the current state of the game

        Returns:   
            - possible_actions(set) - A set of the possible next actions given the board size and the history of moves
        """
        
        possible_actions = self.possible_initial_moves - game_state[0] - game_state[1]
        return possible_actions
    
    def get_new_state(self, game_state, action, current_player):
        """ Calculates the resulting state if a given action is undertaken for a given starting state.

        Input:
            - game_state(tuple(set(), set())): tuple containing previous game history of 2 players which represents 
                                               the current state of the game
            - action(tuple(x,y)): an action to understake - represents the coordinates of a gridcell to occupy.
                                  x - integer representing the gridcell's x-axis coordinates
                                  y - integer representing the gridcell's y-axis coordinates     
            - current_player(int): the order of the player. If current_player = 1, then they correspond to Max 
                                   in Minimax algorithm. If current_player = 2, then they correspond to Min in 
                                   Minimax algorithm.                           
        Returns: 
            - new_game_state(tuple(set(), set())): new game state - tuple containing previous game history of 2 players with
                                                   new move appended to the appropriate history 
        """
        new_game_state = (game_state[0].copy(), game_state[1].copy())
        if current_player == 1:
            new_game_state[0].add(action)
            return(new_game_state[0], new_game_state[1])
        elif current_player == 2:
            new_game_state[1].add(action)
            return(new_game_state[0], new_game_state[1])

    def add_history_entry(self, game_state, value, ifcut):
        """ Add state to buffer. ifcut is True if the value was alpha-beta cut
        """
        history_key = (frozenset(game_state[0]), frozenset(game_state[1]))
        if history_key not in self.history:
            self.history[history_key] = [ifcut, value]
        else:
            pass

    def lookup_history(self, game_state):
        """ Lookup the value for of a given stored game-state
        """
        history_key = (frozenset(game_state[0]), frozenset(game_state[1]))
        if history_key in self.history:
            return(self.history[history_key])
        else:
            return False, None
    
    def minimax_strategy(self, game_state, current_player):
        """ Selects the next action for a given player and game state using the alpha-beta-pruned Minimax algorithm
        
        Inputs: 
            - game_state(tuple(set(), set())): tuple containing previous game history of 2 players which represents 
                                               the current state of the game
            - current_player(int): the order of the player. If current_player = 1, then they correspond to Max 
                                   in Minimax algorithm. If current_player = 2, then they correspond to Min in 
                                   Minimax algorithm. 
        
        Returns: 
            - strategy(list): An ordered list of the optimal actions to taken given the order of the player and the given game state. 
                              Optimal actions are selected based on the Minimax values assigned to them for the given order of the player. 
                              The Minimax values of the actions that were renoved by alpha-beta pruning algorithm are not included in this list. 
       """
        # Initilisation
        
        optimal_actions = []
        self.action_values.clear() #reset the dictionary of action values in the Game attributes

        if self.ifprune: 
            alpha = -float('inf')
            beta = float('inf')
        else:
            alpha = None
            beta = None 

        # If current player makes the first turn, they're Max in Minimax algorithm
        if current_player == 1: 
            optimal_value = self.max(game_state, alpha, beta, previous_action = None, depth = 0)

        # If current player makes the second turn, they're Min in Minimax algorithm
        elif current_player == 2: 
            optimal_value = self.min(game_state, alpha, beta, previous_action = None, depth = 0)
        
        for action, value in self.action_values.items():
            # if the action in the action-value list has an optimal utility value and is not alpha-beta cut
            
     
            if not value[0] and value[1] == optimal_value:
                optimal_actions.append(action) # consider this action optimal 
    
        return optimal_actions

    def max(self, game_state, alpha, beta, previous_action, depth, player=2):
        
        """ Calculates the Minimax value for Max player (player who takes the first turn) for a given game state.

        For a given state, computes the minimax value for player 'max' (player1). 
        Aside from the conventional minimax method, this function has some extra 
        lines for storing state values and retrieving values from previously viewed states. 
        This is required to speed up the calculation, which would otherwise take an inordinate 
        amount of time for any game larger than (3,3,3).

        Inputs: 
            - game_state(tuple(set(), set())): tuple containing previous game history of 2 players which represents 
                                               the current state of the game
            - alpha(float): Cut-off threshold for action utility value for 'Max' player.
                            For 'Max' player, the most optimal action would have the highest utility values, 
                            therefore alpha represents the highest action value identified so far
                            for 'Max' player while traversing along the game-state tree.
                            If a game-state value is less than or equal to alpha,
                            the action leading to that state can be discared as it's not
                            more optimal than the other optimal action that has 
                            already been identified. Such suboptimal actions are stored 
                            as [True, value] in the self.action_value dictionary, with 
                            the first boolean variable representing a flag for being alpha-beta-cut
            - beta(float): Cut-off threshold for action utility value for 'Min' player.
                            For 'Min' player, the most optimal action would have the lowest utility values, 
                            therefore beta represents the lowest action value identified so far 
                            for 'Min' player while traversing along the game-state tree. 
                            If a game-state value is greater than or equal to beta,
                            the action leading to that state can be discared as it's not
                            more optimal than the other optimal action that has 
                            already been identified. Such suboptimal actions are stored 
                            as [True, value] in the self.action_value dictionary, with 
                            the first boolean variable representing a flag for being alpha-beta-cut
            - current_player(int): the order of the player. If current_player = 1, then they correspond to Max 
                                   in Minimax algorithm. If current_player = 2, then they correspond to Min in 
                                   Minimax algorithm. 
            - previos_action(tuple(x,y)): previous action taken by the player described by the x,y coordinates
                                          of the gridcell that were occipied by the move
            - depth(int): denotes the depth of the recursion reached with minimax algorithm. 
                          This parameter is used to store utility values of game states one move away
                          from the current states during the course of minimax algorithm.

            Returns: 
                v(float): the largest action utility value for the current game state and current player 

       """

        # check if the given game state is terminal 
        terminal, winner = self.is_terminal(game_state, previous_action, player)
        
        # if state is terminal, calculate the utility
        if terminal:
            return(self.calculate_utility(winner))
        
        # if state is not terminal, initialise the utility as - infinity 
        v = -float('inf')

        # see if the game state has previosly been explored
        ifcut, v_saved = self.lookup_history(game_state)

        # if state is stored and the value has been previously calculated, return the value
        if v_saved is not None and (not ifcut):
            return v_saved
        
        # if the state is stored, but the value was not calculated (cut by alpha)
        elif v_saved is not None and ifcut:
            if v_saved >= beta: 
                return v_saved

        for action in self.get_possible_actions(game_state):
            new_game_state = self.get_new_state(game_state, action, current_player = 1)
            v_new = self.min(new_game_state, alpha, beta, action, depth + 1)
            
            # select the utility value as the maximum between initialised v and calculated v using min
            v = max(v, v_new)
            # if we're calling the max() function for the first time
            if previous_action == None:
                # store action values
                if action in self.action_values:
                    self.action_values[action][1] = v_new
                else:
                    self.action_values[action] = [False, v_new]
            
            if self.ifprune:
                # if the new value is bigger than beta 
                if v >= beta:
                    
                    # store the new utility value as 
                    self.add_history_entry(game_state, v, True)
                    # if the max function is recursively called from the min function for the first time
                    if depth == 1:
                        # cut the previous action utility value (beta-cut)
                        self.action_values[previous_action] = [True, None] 
                    return v

                # reassign alpha
                alpha = max(alpha, v)

        # save the new game state and associated values in the game state history 
        self.add_history_entry(game_state, v, False)

        return v


    def min(self, game_state, alpha, beta, previous_action, depth, current_player=1):
        """ Calculates the Minimax value for Min player (player who takes the first turn) for a given game state.

        For a given state, computes the minimax value for player 'min' (player2). 
        Aside from the conventional minimax method, this function has some extra 
        lines for storing state values and retrieving values from previously viewed states. 
        This is required to speed up the calculation, which would otherwise take an inordinate 
        amount of time for any game larger than (3,3,3).

        Inputs: 
            - game_state(tuple(set(), set())): tuple containing previous game history of 2 players which represents 
                                               the current state of the game
            - alpha(float): Cut-off threshold for action utility value for 'Max' player.
                            For 'Max' player, the most optimal action would have the highest utility values, 
                            therefore alpha represents the highest action value identified so far
                            for 'Max' player while traversing along the game-state tree.
                            If a game-state value is less than or equal to alpha,
                            the action leading to that state can be discared as it's not
                            more optimal than the other optimal action that has 
                            already been identified. Such suboptimal actions are stored 
                            as [True, value] in the self.action_value dictionary, with 
                            the first boolean variable representing a flag for being alpha-beta-cut
            - beta(float): Cut-off threshold for action utility value for 'Min' player.
                            For 'Min' player, the most optimal action would have the lowest utility values, 
                            therefore beta represents the lowest action value identified so far 
                            for 'Min' player while traversing along the game-state tree. 
                            If a game-state value is greater than or equal to beta,
                            the action leading to that state can be discared as it's not
                            more optimal than the other optimal action that has 
                            already been identified. Such suboptimal actions are stored 
                            as [True, value] in the self.action_value dictionary, with 
                            the first boolean variable representing a flag for being alpha-beta-cut
            - current_player(int): the order of the player. If current_player = 1, then they correspond to Max 
                                   in Minimax algorithm. If current_player = 2, then they correspond to Min in 
                                   Minimax algorithm. 
            - previos_action(tuple(x,y)): previous action taken by the player described by the x,y coordinates
                                          of the gridcell that were occipied by the move
            - depth(int): denotes the depth of the recursion reached with minimax algorithm. 
                          This parameter is used to store utility values of game states one move away
                          from the current states during the course of minimax algorithm.
            Returns: 
                v(float): the smallest action utility value for the current game state and current player 

       """
        # check if the given state is terminal 
        ifterminal, winner = self.is_terminal(game_state, previous_action, current_player)
        
        # if the state is terminal, utility equals to 1 or -1 or 0 
        if ifterminal:
            return(self.calculate_utility(winner))  

        # if state is not terminal, initialise the utility as + infinity 
        v = float('inf')

        ifcut, v_saved = self.lookup_history(game_state)

        if v_saved is not None and (not ifcut): # state stored and the value is certain
            return v_saved
        elif v_saved is not None and (not ifcut): # state stored but the value was alpha-cut
            if v_saved >= alpha:
                return v_saved

        for action in self.get_possible_actions(game_state):
            new_state = self.get_new_state(game_state, action, current_player = 2)
            v_new = self.max(new_state, alpha, beta, action, depth + 1) # increase the depth
            
            # reassing the utility value as the minimum of the old v and the new v 
            v = min(v, v_new)

            # if we're calling the min() function for the first time 
            if previous_action == None:

                if action in self.action_values:
                    self.action_values[action][1] = v_new
                else:
                    self.action_values[action] = [False, v_new]

            if self.ifprune:
                # if the reassigned v is smaller than alpha
                if v <= alpha:
                    self.add_history_entry(game_state, v, True)

                    # if we're callign the min() function for the second time 
                    if depth == 1:

                        # alpha cut the action utility value 
                        self.action_values[previous_action] = [True, None]
                
                    return v

                # reassign beta 
                beta = min(beta, v)

        # update the game state value history 
        self.add_history_entry(game_state, v, False)
        return v


    def calculate_utility(self, winner):
        """ Calculates the utility of a terminal state given the winning player.

        Inputs: 
            - winner(int): integer that denotes the order of the winning player
                           winning_player = 1 means that 'Max' player won
                           winning_player = 2 means that 'Min' player won
                           winning_player = 0 means that the game is tied

        :return: if winner = 1 return 1
                 if winner = 2 return -1
                 if winner = 0 return 0
        """
        if winner == 1:
            return 1
        elif winner == 2:
            return -1
        elif winner == 0:
            return 0


    def horizontal(self, x, y, n):
        """ Function to search for a termninal state in self.is_terminal() across the horizontal axis

        Inputs:
            - x(int): integer denoting the location of the gridcell to occupy using the x-axis of the game-board's gridcell
            - y(int): integer denoting the location of the gridcell to occupy using the y-axis of the game-board's gridcell
            - n(int): An integer representing the number of gridcells to move along the horizontal axis 
                    to the right from (x,y) to get the retunr gridcell

        Returns: 
            - gridcell(tuple(x_new, y_new)): the resulting gridcell after moving n-cells in the chosen direction
        
        """
        return(x+n, y)

    def diagonal_right(self, x, y, n):
        """ Function to search for a termninal state in self.is_terminal() across the right diagonal axis
        
        Inputs:
            - x(int): integer denoting the location of the gridcell to occupy using the x-axis of the game-board's gridcell
            - y(int): integer denoting the location of the gridcell to occupy using the y-axis of the game-board's gridcell
            - n(int): An integer representing the number of gridcells to move along the right diagonal axis 
                    to the right from (x,y) to get the return gridcell

        Returns: 
            - gridcell(tuple(x_new, y_new)): the resulting gridcell after moving n-cells in the chosen direction
        
        """
        return(x+n, y+n)

    def vertical(self, x, y, n):
        """ Function to search for a termninal state in self.is_terminal() across the vertical axis
        

        Inputs:
            - x(int): integer denoting the location of the gridcell to occupy using the x-axis of the game-board's gridcell
            - y(int): integer denoting the location of the gridcell to occupy using the y-axis of the game-board's gridcell
            - n(int): An integer representing the number of gridcells to move along the vertical axis 
                    to the right from (x,y) to get the retunr gridcell

        Returns: 
            - gridcell(tuple(x_new, y_new)): the resulting gridcell after moving n-cells in the chosen direction
        
        """
        return(x, y+n)

    def diagonal_left(self, x, y, n):
        """ Function to search for a termninal state in self.is_terminal() across the diagonal left axis
        

        Inputs:
            - x(int): integer denoting the location of the gridcell to occupy using the x-axis of the game-board's gridcell
            - y(int): integer denoting the location of the gridcell to occupy using the y-axis of the game-board's gridcell
            - n(int): An integer representing the number of gridcells to move along the left diagonal axis 
                    to the right from (x,y) to get the retunr gridcell

        Returns: 
            - gridcell(tuple(x_new, y_new)): the resulting gridcell after moving n-cells in the chosen direction
        
        """
        return(x-n, y+n)


    def draw_board(self, game_state):
        """ Visualise the game board in the terminal for the given game state
        """
        array_board = [[' ' for _ in range(self.m)] for _ in range(self.n)]
        for x, y in game_state[0]:
            array_board[self.n - y][x - 1] = 'X'

        for x, y in game_state[1]:
            array_board[self.n - y][x - 1] = 'O'

        board_str = self.convert_board(array_board)
        print(board_str)


    def convert_board(self, array_board):
        """ Convert array representation of the game board to a printable string.
        """
        upper_case_offset = 64
        list_vert_grids = []

        array_first_hor_line = [chr(code + upper_case_offset) for code in range(1, self.m + 1)]
        first_hor_line = ' ' * (len(str(self.n)) + 3) + (' ' * 3).join(array_first_hor_line) + ' \n'

        for index_line, array_line in enumerate(array_board, 1):
            index_line = self.n + 1 - index_line
            number_spaces_before_line = len(str(self.n)) - len(str(index_line))
            space_before_line = number_spaces_before_line * ' '
            list_vert_grids.append(f'{space_before_line}{index_line} | ' + ' | '.join(array_line) + f' | {index_line}\n')

        line_hor_grids = (len(str(self.n)) + 1)*' ' + '-' * 4 * self.m + '-\n'

        board_str = first_hor_line+ line_hor_grids + line_hor_grids.join(list_vert_grids) +\
                    line_hor_grids + first_hor_line

        return board_str

    def play(self):
        """ Run game simulation and return times for calculating each of the moves.

        This is the main Game class method that simulates an the specified (m,n,k)-game. 
        It prints out the recommended moves for each player's turn (if the automatic playing
        is enabled) as well as the current state of the board (ifdisplay = True). 
        Players in self.manual_players are played manually by User (requires input) 
        and players in self.automatic_players are played automatically by
        the minimax algorithm. If both manual and automatic option are chosen for 
        a player, teh players gets a recommended list of the optimal moves, 
        but inputs the move manually.
        
        Returns: 
            - computing_times(list): list of times required to compute the optimal 
                                     move (when automatic players are used)  with 
                                     the last element being the total game time.
            - states_visited_per_turn(int): number of the game states visited for each turn of the game.
        """

        # Initialise the game 
        current_player = 1 # player1 takes the first turn 

        # in the beginning, the game is not in the terminal state, and the winner has not yet been defined 
        ifterminal = False 
        winner = None

        computing_times = [] # list to store times required to calculate the action using the alpha-beta pruned minimax strategy 
        game_start = time.time() # time of the start of the game 

        states_visited_per_turn = []
        while True:
            
            
            game_state = self.game_state 
            print(game_state)

            # draw the game board at a given state if visialisation is enabled
            if self.ifdisplay:
                self.draw_board(self.game_state)

            # First check if the current game_state is terminal. If it is, print the game results 
            if ifterminal:
                if winner == 1:
                    print('Player 1 won the game!')
                elif winner == 2:
                    print('Player 2 won the game!')
                elif winner == 0:
                    print('No players won, it is a tie!')
                break # break the game loop after the terminal state has been reached

            

            print(f'Player {current_player}, please select select your move...')

            # The current player selects moves and is provided with the list of the best moves 
            # identified by the alpha-beta-pruned Minimax strategy
            if current_player in self.automatic_players and current_player in self.manual_players:
                
                # use the alpha-beta-pruned minimax algorithm to return the list of best actions to take
                actions = self.minimax_strategy(game_state, current_player)

                # display the optimal actions calculated by minmax strategy and take the action selected by the manual user
                string_coordinates = self.translate_move(actions)
                comp_recommend_message = f'The moves recommended by the alpha-beta-pruned Minimax strategy: {string_coordinates}' 
                print(f'Number of states explored: {len(self.history.history)}')
                print(comp_recommend_message)
                input_move = input('Input your move: ')
                
            # if player is fully automatic and doesn't manually input the moves
            elif current_player in self.automatic_players:

                action_start_time = time.time() #start time 
                opt_actions = self.minimax_strategy(game_state, current_player)
                #action = opt_actions[0]
                action = opt_actions[randint(0, len(opt_actions)-1)] # select the random action from the optimal actions list
                action_end_time = time.time() #end time
                
                # print out the recommended moves
                string_coordinates = self.translate_move(opt_actions)
                comp_recommend_message = f'The moves recommended by the alpha-beta-pruned Minimax strategy: {string_coordinates}' 
                print(comp_recommend_message)

                # calculate the time it took to find the optimal values and store them
                time_to_compute = action_end_time-action_start_time 
                computing_times.append(time_to_compute) 
                print(f'Number of states explored: {len(self.history)}')
                string_coordinates = self.translate_move([action])
                automatic_player_message = f'Action taken by automatic player: {string_coordinates}'
                print(automatic_player_message)
            
            # if player is fully manual
            elif current_player in self.manual_players:
                input_move = input('Input your move: ')
                action = self.translate_input(input_move)

            #check if the move is valid
            if self.is_valid_move(self.game_state, action):
                #if valid update state and check if new state is terminal
                self.game_state = self.get_new_state(game_state, action, current_player)
                ifterminal, winner = self.is_terminal(self.game_state, action, current_player)
                #clear saved states to avoid running ou of RAM
                self.history.clear()
                #switch current player
                if current_player == 1:
                    current_player = 2
                elif current_player == 2: 
                    current_player = 1
                
                states_visited_per_turn.append(self.states_visited)
                self.states_visited = 0
            

            else:
                # if move invalid return to top of loop without changing the state
                # or current player.
                invalid_move_message = 'The action you have selected is invalid: the cell selected is either occupied or out of board bounds.'
                print(invalid_move_message)
            

        game_end = time.time()

        # final entry in the time storing array is the how long has the whole game took. 
        computing_times.append(game_end - game_start)

        return computing_times, states_visited_per_turn


if __name__ == "__main__":
    main()
