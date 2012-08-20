# Giles: y.py
# Copyright 2012 Phil Bordelon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from giles.state import State
from giles.games.game import Game
from giles.games.seat import Seat

# What are the minimum and maximum sizes for the board?
Y_MIN_SIZE = 2
Y_MAX_SIZE = 26

#      . 0
#     . . 1
#    . . . 2
#   . . . . 3
#  0 1 2 3
#
# (1, 2) is adjacent to (1, 1), (2, 2), (0, 2), (1, 3), (2, 3), and (0, 1).
Y_DELTAS = ((0, -1), (0, 1), (-1, 0), (1, 0), (1, 1), (-1, -1))

# Because we're lazy and use a square board despite the shape of the Y, we
# fill the rest of the square with invalid characters that match neither
# side.  Define white and black here too.
INVALID = "invalid"
WHITE = "white"
BLACK = "black"


COL_CHARACTERS="abcdefghijklmnopqrstuvwxyz"

class Y(Game):
    """A Y game table implementation.  Invented by Claude Shannon.
    Adapted from my Volity implementation.
    """

    def __init__(self, server, table_name):

        super(Y, self).__init__(server, table_name)

        self.game_display_name = "Y"
        self.game_name = "y"
        self.seats = [
            Seat("White"),
            Seat("Black"),
        ]
        self.min_players = 2
        self.max_players = 2
        self.state = State("config")
        self.prefix = "(^RY^~): "
        self.log_prefix = "%s/%s " % (self.game_display_name, self.game_name)
        self.debug = True

        # Y-specific guff.
        self.seats[0].color = WHITE
        self.seats[0].color_code = "^W"
        self.seats[1].color = BLACK
        self.seats[1].color_code = "^K"
        self.board = None
        self.size = 19
        self.turn = None
        self.turn_number = 0
        self.move_list = []
        self.resigner = None
        
        self.init_board()

    def init_board(self):

        self.board = []
        # We're going to be lazy and build a square board, then fill the
        # half that doesn't make the proper shape with invalid marks.
        for x in range(self.size):
            self.board.append([None] * self.size)

            # Looking at the grid above, you can see that for a given column,
            # all row values less than that value are invalid.
            for y in range(x):
                self.board[x][y] = INVALID

        # That's it!

    def set_size(self, player, size_str):

        if not size_str.isdigit():
            player.tell_cc(self.prefix + "You didn't even send a number!\n")
            return False

        new_size = int(size_str)
        if new_size < Y_MIN_SIZE or new_size > Y_MAX_SIZE:
            player.tell_cc(self.prefix + "Too small or large.  Must be 2 to 52 inclusive.\n")
            return False

        # Got a valid size.
        self.size = new_size
        self.init_board()
        self.channel.broadcast_cc(self.prefix + "^M%s^~ has changed the size of the board to ^C%s^~.\n" % (player.display_name, str(new_size)))
        return True

    def move_to_values(self, move_str):

        # All valid moves are of the form g22, J15, etc.  Ditch blatantly
        # invalid moves.
        if type(move_str) != str or len(move_str) < 2 or len(move_str) > 3:
            return None

        # First character must be in COL_CHARACTERS.
        col_char = move_str[0].lower()
        if col_char not in COL_CHARACTERS:
            return None
        else:
            x = COL_CHARACTERS.index(col_char)

        # Next one or two must be digits.
        row_chars = move_str[1:]
        if not row_chars.isdigit():
            return None
        else:
            y = int(row_chars) - 1

        # Now verify that these are even in range for this board.  Remember
        # that column values greater than the row value are invalid; that
        # provides a bound on the column value, so we only then need to
        # check the row against the upper bound.
        if (x < 0 or x > y or y >= self.size):
            return None
        
        # Valid!
        return (x, y)

    def move(self, seat, move_str):

        # Get the actual values of the move.
        values = self.move_to_values(move_str)
        if not values:
            seat.player.tell_cc(self.prefix + "Invalid move.\n")
            return None

        x, y = values
        if self.board[x][y]:
            seat.player.tell_cc(self.prefix + "That space is already occupied.\n")
            return None

        # Okay, it's an unoccupied space!  Let's make the move.
        self.board[x][y] = seat.color
        self.channel.broadcast_cc(self.prefix + seat.color_code + "%s^~ has moved to ^C%s^~.\n" % (seat.player.display_name, move_str))
        return (x, y)

    def swap(self):

        # This is an easy one.  Take the first move and change the piece
        # on the board from white to black.
        self.board[self.move_list[0][0]][self.move_list[0][1]] = BLACK
        self.channel.broadcast_cc(self.prefix + "^Y%s^~ has swapped ^WWhite^~'s first move.\n" % self.seats[1].player.display_name)

    def print_board(self, player):

        slash_line = " "
        char_line = ""
        for x in range(self.size):
            msg = " "
            color_char = "^W"
            if x % 2 == 0:
                color_char = "^K"
            slash_line += color_char + "/^~ "
            char_line += "%s " % COL_CHARACTERS[x]
            for spc in range(self.size - x):
                msg += " "
            for y in range(x + 1):
                piece = self.board[y][x]
                if piece == BLACK:
                    msg += "^Kx^~ "
                elif piece == WHITE:
                    msg += "^Wo^~ "
                elif y % 2 == 0:
                    msg += "^m.^~ "
                else:
                    msg += "^M.^~ "
            msg += str(x + 1) + "\n"
            player.tell_cc(msg)
        player.tell_cc(slash_line + "\n")
        player.tell_cc(char_line + "\n")

    def get_turn_str(self):
        if self.state.get() == "playing":
            if self.seats[0].color == self.turn:
                color_word = "^WWhite^~"
                name_word = "^R%s^~" % self.seats[0].player.display_name
            else:
                color_word = "^KBlack^~"
                name_word = "^Y%s^~" % self.seats[1].player.display_name
            return "It is %s's turn (%s).\n" % (name_word, color_word)
        else:
            return "The game is not currently active.\n"

    def send_board(self):

        for player in self.channel.listeners:
            self.print_board(player)

    def resign(self, seat):

        # Okay, this person can resign; it's their turn, after all.
        self.channel.broadcast_cc(self.prefix + "^R%s^~ is resigning from the game.\n" % seat.player.display_name)
        self.resigner = seat.color
        return True

    def show(self, player):
        self.print_board(player)
        player.tell_cc(self.get_turn_str())

    def show_help(self, player):

        super(Y, self).show_help(player)
        player.tell_cc("\nY SETUP PHASE:\n\n")
        player.tell_cc("              ^!size^. <size>, ^!sz^.     Set board to size <size>.\n")
        player.tell_cc("            ^!ready^., ^!done^., ^!r^., ^!d^.     End setup phase.\n")
        player.tell_cc("\nY PLAY:\n\n")
        player.tell_cc("      ^!move^. <ln>, ^!play^., ^!mv^., ^!pl^.     Make move <ln> (letter number).\n")
        player.tell_cc("                         ^!swap^.     Swap the first move (only Black, only their first).\n")
        player.tell_cc("                       ^!resign^.     Resign.\n")

    def handle(self, player, command_str):

        # Handle common commands.
        handled = self.handle_common_commands(player, command_str)

        state = self.state.get()

        command_bits = command_str.strip().split()
        primary = command_str.split()[0].lower()
        if state == "config":

            if primary in ('size', 'sz'):
                if len(command_bits) == 2:
                    self.set_size(player, command_bits[1])
                else:
                    player.tell_cc(self.prefix + "Invalid size command.\n")
                handled = True

            elif primary in ('done', 'ready', 'd', 'r'):

                self.channel.broadcast_cc(self.prefix + "The game is now ready for players.\n")
                self.state.set("need_players")
                handled = True

        elif state == "need_players":

            # If both seats are full and the game is active, time to
            # play!

            if self.seats[0].player and self.seats[1].player and self.active:
                self.state.set("playing")
                self.channel.broadcast_cc(self.prefix + "^WWhite^~: ^R%s^~; ^KBlack^~: ^Y%s^~\n" %
                   (self.seats[0].player.display_name, self.seats[1].player.display_name))
                self.turn = WHITE
                self.turn_number = 1
                self.send_board()
                self.channel.broadcast_cc(self.prefix + self.get_turn_str())

        elif state == "playing":

            made_move = False

            # For all move types, don't bother if it's not this player's turn.
            if primary in ('move', 'mv', 'play', 'pl', 'swap', 'resign'):

                seat = self.get_seat_of_player(player)
                if not seat:
                    player.tell_cc(self.prefix + "You can't move; you're not playing!\n")
                    return

                elif seat.color != self.turn:
                    player.tell_cc(self.prefix + "You must wait for your turn to move.\n")
                    return

            if primary in ('move', 'mv', 'play', 'pl'):
                if len(command_bits) == 2:
                    success = self.move(seat, command_bits[1])
                    if success:
                        move = success
                        made_move = True
                    else:
                        player.tell_cc(self.prefix + "Unsuccessful move.\n")
                else:
                    player.tell_cc(self.prefix + "Unsuccessful move.\n")

                handled = True

            elif primary in ('swap',):

                if self.turn_number == 2 and seat.player == player:
                    self.swap()
                    move = "swap"
                    made_move = True

                else:
                    player.tell_cc(self.prefix + "Unsuccessful swap.\n")

                handled = True

            elif primary in ('resign',):

                if self.resign(seat):
                    move = "resign"
                    made_move = True

                handled = True
                    
            if made_move:

                self.send_board()
                self.move_list.append(move)
                self.turn_number += 1

                winner = self.find_winner()
                if winner:
                    self.resolve(winner)
                    self.finish()
                else:
                    if self.turn == WHITE:
                        self.turn = BLACK
                    else:
                        self.turn = WHITE
                    self.channel.broadcast_cc(self.prefix + self.get_turn_str())

        if not handled:
            player.tell_cc(self.prefix + "Invalid command.\n")

    def find_winner(self):

        
        # First, check resignations; that's a fast bail.
        if self.resigner:
            if self.resigner == WHITE:
                return self.seats[1].player
            elif self.resigner == BLACK:
                return self.seats[0].player
            else:
                self.server.log.log(self.log_prefix + "Weirdness; a resign that's not a player.")
                return None

        # Well, darn, we have to do actual work.  Time for recursion!
        # To calculate a winner:
        #    - Pick a side.
        #    - For each piece on that side, see if it's connected to
        #      both other sides.  If so, that player is a winner.
        #    - If not, there is no winner (as winners must connect all
        #      three sides).

        self.found_winner = None
        self.adjacency = []

        # Set up our adjacency checker.
        for i in range(self.size):
            self.adjacency.append([None] * self.size)

        # For each piece on the left side of the board...
        for i in range(self.size):
            if self.board[0][i]:
                
                # We're not touching the other two sides yet.
                self.touch_bottom = False
                self.touch_right = False
                self.update_adjacency(0, i, self.board[0][i])

                if self.found_winner == WHITE:
                    return self.seats[0].player
                elif self.found_winner == BLACK:
                    return self.seats[1].player

        # No winner yet.
        return None

    def update_adjacency(self, x, y, color):

        # Skip work if a winner's already found.
        if self.found_winner:
            return

        # Skip work if we're off the board.
        if (x < 0 or x > y or y >= self.size):
            return

        # Skip work if we've been here already.
        if self.adjacency[x][y]:
            return

        # Skip work if it's empty or for the other player.
        this_cell = self.board[x][y]
        if this_cell != color:
            return

        # All right, it's this player's cell.  Mark it visited.
        self.adjacency[x][y] = color

        # If we're on either the bottom or right edges, mark that.
        if (y == self.size - 1):
            self.touch_bottom = True

        if (x == y):
            self.touch_right = True

        # Bail if we've met both win conditions.
        if self.touch_bottom and self.touch_right:
            self.found_winner = color

        # Okay, no winner yet.  Recurse on the six adjacent cells.
        for x_delta, y_delta in Y_DELTAS:
            self.update_adjacency(x + x_delta, y + y_delta, color)
        
    def resolve(self, winner):
        self.channel.broadcast_cc(self.prefix + "^C%s^~ wins!\n" % (winner.display_name))