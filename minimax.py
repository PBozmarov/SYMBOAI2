from typing import List, Tuple
import random
import numpy as np
import time

def main():
    '''
    Setup and play the game.
    '''
    game = Game(4, 4, 4, automatic_players = [1,2], display = True)
    game.play()

UPPER_CASE_OFFSET = 64

class Game(object):
    """
    Class representing the (m, n, k)-game.
    """


    def __init__(self, m,n,k,
                automatic_players=[1, 2],
                manual_players=[1],
                display:bool = True
                    ):
        """
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

        - param m: an integer specifying the grid's size along the x-axis
        - param n: an integer specifying the grid size along the y-axis
        - param k: an integer reflecting the number of consecutive squares a player must occupy on the grid in order to win the game
        - automatic players parameter: The list of players that will be played automatically by the minimax algorithm. [1, 2] indicates that both player1 and player2 are automatically played. 
          And an empty list [] indicates that none are played automatically: 
        - manual players: A list of players to be played manually using the minimax algorithm.
        - display: A Boolean indicating whether or not the game's graphical representation will be displayed. 
        """

        # Setting m,n,k
        self.m = m
        self.n = n
        self.k = k

        # Setting the players and the display
        self.automatic_players = automatic_players
        self.manual_players = manual_players
        self.display = display

        # initialize the possible moves and the moves of player 1 and player 2, the state and the win 
        # directions
        self.possible_moves = set([(i,j) for i in range(1,self.m+1) for j in range(1, self.n+1)])
        self.previous_moves_player1 = set()
        self.previous_moves_player2 = set()
        self.state = (self.previous_moves_player1, self.previous_moves_player2)
        self.directions =(self.horizontal, self.diagonal_R, self.vertical, self.diagonal_L)

        # set experience buffer to speed up our algorithm
        self.buffer = ExperienceBuffer()
        
        # initialize the action values
        self.action_values = {}


    def play(self):
        """
        It simulates the full game. Prints the essential information regarding the board's present state. 
        Players in self.manual players are controlled by the user, whereas players in self.automatic players
        are controlled automatically by the minimax algorithm. The minimax algorithm recommends movements for
        players in both self.manual players and self.automatic players, but the user selects which move to make. 
        - return: a list of the execution times of moves performed by automatic players, with the last element 
                  representing the total game duration.
        """
        
        player = 1
        terminal = False
        winner = None

        msg_manual = 'PC recommended move(s): '
        msg_automatic = 'PC makes a move: '
        msg_invalid = 'This move is invalid!. The cell is already occupied or is out of bounds.'

        times = []
        start_game = time.time()
        #This loop represents the game
        while True:
            state = self.state
            if self.display:
                self.drawboard(self.state)
            # Print terminal message
            if terminal:
                if winner == 1:
                    print('The Player 1 has WON!')
                elif winner == 2:
                    print('The Player 2 has WON!')
                elif winner == 0:
                    print('The game ends with a TIE!')
                break

            print(f'Player {player} move...')

            # The Manual player
            if player in self.automatic_players and player in self.manual_players:
                chosen_actions = self.minimax_strategy(state, player)
                board_coordinates = self.convert_array_to_board_coordinates(chosen_actions)
                msg = msg_manual + board_coordinates
                print(msg)
                board_coordinates = input('Input move: ')
                chosen_action = self.convert_board_to_array_coordinates(board_coordinates)
            
            # The automatic player
            elif player in self.automatic_players:
                start_action = time.time()
                chosen_action = self.minimax_strategy(state, player)[0]
                end_action = time.time()
                times.append(end_action-start_action)
                board_coordinates = self.convert_array_to_board_coordinates([chosen_action])
                msg = msg_automatic + board_coordinates
                print(msg)

            #the manual player
            elif player in self.manual_players:
                board_coordinates = input('Input move: ')
                chosen_action = self.convert_board_to_array_coordinates(board_coordinates)

            # check the validity of our action
            if self.is_valid(self.state, chosen_action):

                # if the action is valid, check if our new state is terminal
                self.state = self.resulting_state(state, chosen_action, player)
                terminal, winner = self.is_terminal(self.state, chosen_action, player)
                
                #delete our saved states
                self.buffer.clear()
                
                #switch the player
                player = player%2 + 1
            else:
                # if move invalid return to top of loop without changing the state
                # or current player.
                print(msg_invalid)

        end_game = time.time()
        times.append(end_game - start_game)
        return times


    def minimax_strategy(self, state, player):
        """
        The minimax action for a given player in a given game state is calculated. 

        - param state: a tuple of sets(set(), set()) describing the game's current state. 
        - param player: The player who is about to make a move: 
          player = 1 -> max-action
          player = 2 -> min-action
          max-action = player = 1 
        - return: a list of all feasible optimal actions in the current game state. Specifically, 
          actions with values equal to the action value of the minimax actions for the given player.
       """
        
        # initialize the optimal actions
        opt_actions = []
        self.action_values.clear()

        if player == 1:
            opt_value = self.max(state, last_action = None, depth = 0)
        elif player == 2: 
            opt_value = self.min(state, last_action = None, depth = 0)
        for action, value in self.action_values.items():
            if value == opt_value:
                opt_actions.append(action)
        return opt_actions


    def max(self, state, last_action, depth, player=2):
        """
        For a given state, computes the minimax value for player'max'(player1). 
        Aside from the conventional minimax method, this function has some extra 
        lines for storing state values and retrieving values from previously viewed states. 
        This is required to speed up the calculation, which would otherwise take an inordinate 
        amount of time for any game larger than (3,3,3).

        - param state: tuple of sets(set(), set()) that reperesenting our current
                      game state.

        - param last_action: The latest action which was taken in the game

        - param depth: Keep track of the recursion's depth to store values of states one step distant from 
                       the current state when the recursion unwinds.
        - param player: The player that made the latest move.

        - return: maximum action value corresponding to the current state.
       """
        terminal_state, winner = self.is_terminal(state, last_action, player)
        
        # if the state is terminal
        if terminal_state:
            return(self.calculate_utility(winner))
        V = -float('inf')

        # In order to speed up our calculations, the following
        # code lines search for the the values of the previous states
      
        V_buff = self.buffer.lookup(state)
        if V_buff == None:
            pass
        elif V_buff != None:
            return V_buff
        
        # In order to speed up our calculations, the following
        # code lines search for the the values of the previous states   
        for chosen_action in self.actions(state):
            new_state = self.resulting_state(state, chosen_action, 1)
            V_new = self.min(new_state, chosen_action, depth + 1)
            V = max(V, V_new)
            if depth == 0:
                self.action_values[chosen_action] = V_new

        self.buffer.add(state, V)
        return V


    def min(self, state, last_action, depth, player=1):
        """
        For a given state, computes the minimax value for player'min'(player2). 
        Aside from the conventional minimax method, this function has some extra 
        lines for storing state values and retrieving values from previously viewed states. 
        This is required to speed up the calculation, which would otherwise take an inordinate 
        amount of time for any game larger than (3,3,3).

        - param state: tuple of sets(set(), set()) that reperesenting our current
                      game state.

        - param last_action: The latest action which was taken in the game

        - param depth: Keep track of the recursion's depth to store values of states one step distant from 
                       the current state when the recursion unwinds.
        - param player: The player that made the latest move.

        - return: minimum action value corresponding to the current state.
       """
        terminal_state, winner = self.is_terminal(state, last_action, player)
        if terminal_state:
            return(self.calculate_utility(winner))
        V = float('inf')
        
        # In order to speed up our calculations, the following
        # code lines search for the the values of the previous states
        V_buff = self.buffer.lookup(state)
        if V_buff == None:
            pass
        elif V_buff != None:
            return V_buff
        
        # In order to speed up our calculations, the following
        # code lines search for the the values of the previous states
        for action in self.actions(state):
            new_state = self.resulting_state(state, action, 2)
            V_new = self.max(new_state, action, depth + 1)
            V = min(V, V_new)
            if depth == 0:
                self.action_values[action] = V_new

        self.buffer.add(state, V)
        return V


    def actions(self, state):
        """
      The difference between the available action on an empty board and the present state is used to calculate
      the possible action in a given condition. 

      - param state: tuple of sets(set(), set()) describing the game's current state. 

      - return: A list of actions that could be taken in the given condition.
        """
        return(self.possible_moves - state[0] - state[1])


    def resulting_state(self, state:tuple, action:tuple, player):
        """ Returns the subsequent state if a particular action is performed in a given state. 

            - param state: a tuple of sets(set(), set()) representing the game's current state. 
            - param action: tuple (coord x, coord y) representing an action, where coord x is an integer reflecting 
                            the projection of a coordinate on the board's x-axis, i.e. a column of the game-grid. coord y is an integer 
                            that represents the y-axis projection of a coordinate. 
            - return: a tuple of sets(set(), set()) representing the game's final state. 
"""
        new_state = (state[0].copy(), state[1].copy())
        if player == 1:
            new_state[0].add(action)
            return(new_state[0], new_state[1])
        elif player == 2:
            new_state[1].add(action)
            return(new_state[0], new_state[1])


    def calculate_utility(self, winner):
        """
        Determines the utility of a terminal state given the winner. 

        - param winner: integer representing the winning player:
                               winner = 1 --> 'max' won
                               winner = 2 --> 'min' won
                               winner = 0 --> the game ends in a tie

        - return: if winner = 1 --> 1
                 if winner = 2 --> -1
                 if winner = 0 --> 0
        """
        if winner == 1:
            return 1
        elif winner == 2:
            return -1
        elif winner == 0:
            return 0


    def horizontal(self, x, y, step):
        """
        Helper function that searches for is_terminal in order to find terminal states. 

        -param x: An integer encoding the x-axis projection of a coordinate. 
        -param y:An integer encoding the y-axis projection of a coordinate. 
        -param step: An integer denoting the number of horizontal "steps" to take from (x, y). 
        -return: (x+step, y)
        """
        return(x+step, y)

    def diagonal_R(self, x, y, step):
        """
        Helper function that searches for is_terminal in order to find terminal states.

        -param x: An integer encoding the x-axis projection of a coordinate. 
        -param y:An integer encoding the y-axis projection of a coordinate. 
        -param step: An integer denoting the number of right diagonal 'steps' from (x, y).

        :return: (x+step, y+step)
        """
        return(x+step, y+step)

    def vertical(self, x, y, step):
        """
        Helper function that searches for is_terminal in order to find terminal states.

        -param x: An integer representing the projection of a coordinate on the x-axis.
        -param y: An integer representing the projection of a coordinate on the y-axis.
        -param step: An integer denoting the number of vertical 'steps' from (x, y).

        :return: (x, y+step)
        """
        return(x, y+step)

    def diagonal_L(self, x, y, step):
        """
        Helper function that searches for is_terminal in order to find terminal states.

        -param x: An integer representing the projection of a coordinate on the x-axis.
        -param y: An integer representing the projection of a coordinate on the y-axis.
        -param step: An integer denoting the number of left diagonal 'steps' from (x, y).


        :return: (x-step, y+step)
        """
        return(x-step, y+step)


    def is_terminal(self, state, previous_action, player):
        """
        From the supplied state, perform a terminal check. Uses the most recent action done and the 
        player who took it to speed up calculations by looking solely for terminal combinations that 
        involve the most recent action taken. 
        For example, consider the following state of a (3,3,3)-game:
                                A   B   C
                              -------------
                            3 | O | O | X | 3
                              -------------
                            2 | X | X | X | 2
                              -------------
                            1 | O | X | O | 1
                              -------------
                                A   B   C
        Knowing that the last action was, say, C2, allows you to limit your search to combinations 
        involving C2 in the terminal check.

        - param state: tuple of sets(set(), set()) reperesenting the current
                      state of the game.

        - param last_action: The latest action taken.

        - param player: The player who made the latest move.

        - return: (terminal, winner) where terminal is a boolean such that:
                 terminal = True --> state is terminal
                 terminal = False --> state is not terminal
                 and winner representing the winner of the game:

                 winner = 1 --> 'max' won
                 winner = 2 --> 'min' won
                 winner = 0 --> game is tied
                 winner = None if terminal=False
        """
        terminal = False
        winner = None
        if previous_action == None:
            return terminal, winner
        previous_moves = state[player - 1]
        x = previous_action[0]
        y = previous_action[1]

        # we loop through the directions
        for direction in self.directions:
            combination_length = 1
            step = 1
            while True:
                
                #This cell is also occupied by a player.
                if direction(x, y, step) in previous_moves:
                    combination_length += 1
                    step += 1
                # This cell is not occopied by a player
                else:
                    break
            
            #check the opposite
            step = -1
            while True:

                #This cell is also occupied by a player.
                if direction(x, y, step) in previous_moves:
                    combination_length += 1
                    step -= 1

                # This cell is not occopied by a player
                else:
                    break

            if combination_length >= self.k:
                terminal = True
                winner = player
                break

        if not terminal and len(state[0]) + len(state[1]) == self.n*self.m:#check if tied
            winner = 0
            terminal = True

        return terminal, winner


    def is_valid(self, state, action):
        """ Determine whether a particular action is valid in a given state. The action must take place 
        within the board's boundaries and in an unoccupied cell. 

        -param state: a tuple of sets(set(), set()) representing the game's current state. 
        -param action: tuple (coord x, coord y) indicating an action, where coord x is an integer 
         reflecting the projection of a coordinate on the board's x-axis, i.e. a column of the game-grid. 
         coord y is an integer that represents the y-axis projection of a coordinate. 

        -return: True if the action is valid, False otherwise 
        
        """

        x_boundary = 1 <= action[0] <= self.m
        y_boundary = 1 <= action[1] <= self.n
        not_occupied_player1 = action not in state[0]
        not_occupied_player2 = action not in state[1]

        return(all([x_boundary, y_boundary, not_occupied_player1, not_occupied_player2]))


    def drawboard(self, state):
        """
        Draw the board on screen for a state.
        """
        board_array = [[' ' for _ in range(self.m)] for _ in range(self.n)]
        for x, y in state[0]:
            board_array[self.n - y][x - 1] = 'X'

        for x, y in state[1]:
            board_array[self.n - y][x - 1] = 'O'

        board_str = self.get_board_string(board_array)
        print(board_str)


    def get_board_string(self, array_board):
        """
        Convert an array representing the state of the board to a printable string.
        """
        lines_list = []

        first_line_array =[chr(code + UPPER_CASE_OFFSET) for code in range(1, self.m + 1)]
        first_line = ' ' * (len(str(self.n)) + 3) + (' ' * 3).join(first_line_array) + ' \n'

        for index_line, array_line in enumerate(array_board, 1):
            index_line = self.n + 1 - index_line
            number_spaces_before_line = len(str(self.n)) - len(str(index_line))
            space_before_line = number_spaces_before_line * ' '
            lines_list.append(f'{space_before_line}{index_line} | ' +\
                            ' | '.join(array_line) + f' | {index_line}\n')

        line_dashes = (len(str(self.n)) + 1)*' ' + '-' * 4 * self.m + '-\n'

        board_str = first_line + line_dashes + line_dashes.join(lines_list) +\
                    line_dashes + first_line

        return board_str


    def convert_array_to_board_coordinates(self, coordinates):
        """
        Convert array index coordinates to their printed representation.
        """
        coordinates_board = []
        for x, y in coordinates:
            x_board = chr(x + UPPER_CASE_OFFSET)
            y_board = str(y)
            coordinates_board.append(x_board + y_board)
        coordinates_board.sort()
        coordinate_string = str()
        for coordinate in coordinates_board:
            coordinate_string += coordinate + ', '
        return coordinate_string[:-2] + '.'


    def convert_board_to_array_coordinates(self, coordinate):
        """
        Convert coordinates from their printed form to array indexes.
        """
        x_array = ord(coordinate[0].upper()) - UPPER_CASE_OFFSET
        y_array = int(coordinate[1])
        return(x_array, y_array)


class ExperienceBuffer:
    '''
    A class for configuring the storage of state values. This is utilised to achieve suitable 
    execution times on the PCs that I have at my disposal.
    '''

    def __init__(self):
        self.buffer = {}

    def add(self, state, value):
        '''
        Add state to the buffer.
        '''
        state_frozen = (frozenset(state[0]), frozenset(state[1]))
        if frozenset not in self.buffer:
            self.buffer[state_frozen] = value
        else:
            pass

    def lookup(self, state):
        '''
        Look up the value of a previously saved state.
        '''
        frozen_state = (frozenset(state[0]), frozenset(state[1]))
        if frozen_state in self.buffer:
            return(self.buffer[frozen_state])
        else:
            return None

    def clear(self):
        '''
        Clear the stored states
        '''
        self.buffer.clear()

if __name__ == "__main__":
    main()
