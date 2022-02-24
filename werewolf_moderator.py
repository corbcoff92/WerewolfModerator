from player import Player, Roles
import os
from random import randint

class NotEnoughPlayersException(Exception):
    def __init__(self):
        super().__init__()

ROLES_TO_ASSIGN = [Roles.WEREWOLF, Roles.DOCTOR, Roles.SEER]

class Server:
    def __init__(self):
        self.players = []
        self.client = Client()
        self.done = False
        self.exit = False

    def serve(self):
        self.accept_players()

    
    def accept_players(self):
        players_joined = []
        adding_players = True
        while adding_players and not self.exit:
            selection = int(input('Server\n\t1. Add player\n\t2. Begin\n\t3. Exit\nPlease make a selection: '''))    
            if selection == 1:
                name = ''
                while not name:
                    name = input('Please enter your name: ')
                    if not name:
                        print('Name cannot be blank, try again...')
                players_joined.append(name)
            elif selection == 2:
                if len(players_joined) >= len(ROLES_TO_ASSIGN) + 2:
                    self.assign_roles(players_joined)
                    self.begin()
                else:
                    print('Not enough players to begin...')        
            elif selection == 3:
                adding_players = False
                self.exit = True
    
    def begin(self):
        while not self.exit and not self.done:
            if not self.exit:        
                selection = int(input('\t1. Night\n\t2. Day\n\t3. Exit\nPlease make a selection: '''))
                if selection == 1:
                    self.night()
                elif selection == 2:
                    self.day()
                elif selection == 3:
                    self.exit = True

    def assign_roles(self, players_joined):
        roles_to_assign = ROLES_TO_ASSIGN        
        if len(players_joined) >= 15:
            roles_to_assign.extend([Roles.WEREWOLF]*((len(players_joined) - 11)//4))
        
        while roles_to_assign and players_joined:
            idx = randint(0, len(players_joined)-1)
            self.players.append(Player(players_joined.pop(idx), roles_to_assign.pop()))
        
        while players_joined:
            self.players.append(Player(players_joined.pop(), Roles.VILLAGER))
    
    def day(self):
        votes = self.client.day(self.players)
        player_with_most_votes = max(votes, key=votes.count)
        if (votes.count(player_with_most_votes) > len(self.players) // 2):
            print(f'Server: {player_with_most_votes.name} has been jailed...')
            self.players.remove(player_with_most_votes)
            self.check_game_over()
        else:
            print('Server: No player recieved a majority vote...')

    def night(self):
        player_saved, player_hunted = self.client.night(self.players)
        if player_saved == player_hunted:
            print(f'Server: {player_hunted.name} was hunted, but saved...')
        else:
            print(f'Server: {player_hunted.name} was hunted during the night...')
            self.players.remove(player_hunted)
            self.check_game_over()
    
    def check_game_over(self):
        num_werewolves = len([player for player in self.players if player.role == Roles.WEREWOLF])
        num_villagers = len([player for player in self.players if player.role != Roles.WEREWOLF])
        if num_villagers <= num_werewolves:
            self.game_over(True)
        elif num_werewolves <= 0:
            self.game_over(False)
    
    def game_over(self, werewolves_won):
        self.done = True
        if werewolves_won:
            print('Server: The werewolves have won!')
        else:
            print('Server: The villagers have won!')
        self.client.winners(werewolves_won, self.players)
        

class Client:    
    def night(self, players):
        player_saved = None
        for player in players:
            role = player.role
            os.system('cls')
            input(f'Client: {player.name}, press enter when you are ready...')
            print(f'Client: You are a {player.role}')
            if role == Roles.VILLAGER:
                print('Please select a random person...')
                self.ask_player(players)
            elif role == Roles.WEREWOLF:
                werewolves = [player for player in players if player.role == Roles.WEREWOLF]
                if len(werewolves) > 1:
                    print(f'The other werewolves are: {" ".join([werewolf.name for werewolf in werewolves])}')
                else:
                    print(f"You are the only remaining werewolf, ")
                print('Please select a player to hunt...')
                player_hunted = self.ask_player(players, excluded_players=werewolves)
            elif role == Roles.DOCTOR:
                print('Please select a player that you would like to save...')
                player_saved = self.ask_player(players)
            elif role == Roles.SEER:
                print('Please select a player that you would like to know about...')
                selected_player = self.ask_player(players, excluded_players=[player])
                print(f'{selected_player.name} {"is NOT" if selected_player.role != Roles.WEREWOLF else "IS"} a Werewolf...')
                input('Press enter to continue...')
        return player_saved, player_hunted

    def day(self, players):
        votes = []
        print('Client: Time for trial...')
        for player in players:
            print(f'{player.name} please select the person you would like to put on trial...')
            votes.append(self.ask_player(players, excluded_players=[player]))
        return votes

    def winners(self, werewolves_won, players):
        for player in players:
            print(f'Client: You were a {player.role}. ', end='')
            if (werewolves_won and player.role == Roles.WEREWOLF) or (not werewolves_won and player.role != Roles.WEREWOLF):
                print('You have won!')
            else:
                print('You have lost!')

    def ask_player(self, players, excluded_players=None):
        if excluded_players:
            available_players = [player for player in players if player not in excluded_players]
        else:
            available_players = players
            
        num_players = len(available_players)
        for i, player in enumerate(available_players):
            print(f'\t{i+1}. {player.name}')
        valid = False
        while not valid:
            selection = int(input('Please select a player: '))
            valid = (1 <= selection <= num_players)
            if not valid:
                print('Invalid selection, please try again...')
        return available_players[selection - 1]        

if __name__ == '__main__':
    server = Server()
    players_joined = [f'Player {i}' for i in range(1, 5)]
    server.assign_roles(players_joined)
    server.begin()
