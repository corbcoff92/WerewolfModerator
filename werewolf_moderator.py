from player import Player, Roles
import os
from random import randint

class NotEnoughPlayersException(Exception):
    def __init__(self):
        super().__init__()

ROLES_TO_ASSIGN = [Roles.WEREWOLF, Roles.DOCTOR, Roles.SEER]

def shuffle_list(l):
    num_items = len(l)
    for _ in range(5):
        for item in l:
            idx = randint(0, num_items - 1)
            l.append(l.pop(idx))

class Server:
    def __init__(self):
        self.clients = []
        self.active_players = []
        self.done = False
        self.exit = False

    def serve(self):
        self.accept_players()

    
    def accept_players(self):
        adding_players = True
        while adding_players and not self.exit:
            selection = int(input('Server\n\t1. Add player\n\t2. Begin\n\t3. Exit\nPlease make a selection: '''))    
            if selection == 1:
                name = ''
                while not name:
                    name = input('Please enter your name: ')
                    if not name:
                        print('Name cannot be blank, try again...')
                self.client_join(name)
            elif selection == 2:
                if len(self.clients) >= len(ROLES_TO_ASSIGN) + 2:
                    self.active_players = list(self.clients)
                    self.assign_roles()
                    self.begin()
                else:
                    print('Not enough players to begin...')        
            elif selection == 3:
                adding_players = False
                self.exit = True
    
    def client_join(self, name):
        self.clients.append(Client(name))
        num_joined = len(self.clients)
        print(f'{num_joined} Current Players:')
        for i,client in enumerate(self.clients):
            print(f'\t{i+1}. {client.name}')

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

    def assign_roles(self):
        roles_to_assign = ROLES_TO_ASSIGN
        if len(self.active_players) >= 15:
            roles_to_assign.extend([Roles.WEREWOLF]*((len(self.active_players) - 11)//4))

        shuffle_list(roles_to_assign)
        shuffle_list(self.active_players)

        for player, role in zip(self.active_players, roles_to_assign):
            player.role = role
        
        shuffle_list(self.active_players)
            
    def day(self):
        votes = []
        for player in self.active_players:
            votes.append(player.day(self.active_players))
        
        player_with_most_votes = max(votes, key=votes.count)
        if (votes.count(player_with_most_votes) > len(self.active_players) // 2):
            print(f'Server: {player_with_most_votes.name} has been jailed...')
            self.active_players.remove(player_with_most_votes)
            self.check_game_over()
        else:
            print('Server: No player recieved a majority vote...')

    def night(self):
        selected_players = []
        for player in self.active_players:
            selected_player = player.night(self.active_players)
            if selected_player:
                selected_players.append(selected_player)
            
        saved_players = [selected_player[1] for selected_player in selected_players if selected_player[0] == 'SAVED']
        hunted_players = [selected_player[1] for selected_player in selected_players if selected_player[0] == 'HUNTED']

        if saved_players:
            player_saved = max(saved_players, key=saved_players.count)
        else:
            player_saved = None
        
        if hunted_players:
            player_hunted = max(hunted_players, key=hunted_players.count)

        if player_saved == player_hunted:
            print(f'Server: {player_hunted.name} was hunted, but saved...')
        else:
            print(f'Server: {player_hunted.name} was hunted during the night...')
            self.active_players.remove(player_hunted)
            self.check_game_over()
    
    def check_game_over(self):
        num_werewolves = len([player for player in self.active_players if player.role == Roles.WEREWOLF])
        num_villagers = len([player for player in self.active_players if player.role != Roles.WEREWOLF])
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

        for client in self.clients:
            client.check_winner(werewolves_won)
        

class Client(Player):
    def __init__(self, name):
        super().__init__(name)

    def night(self, players):
        os.system('cls')
        input(f'Client-{self.name}: {self.name}, press enter when you are ready...')
        print(f'Client-{self.name}: You are a {self.role}')
        if self.role == Roles.VILLAGER:
            print('Please select a random person...')
            self.ask_player(players)
            return None
        elif self.role == Roles.WEREWOLF:
            werewolves = [player for player in players if player.role == Roles.WEREWOLF]
            if len(werewolves) > 1:
                print(f'The other werewolves are: {" ".join([werewolf.name for werewolf in werewolves])}')
            else:
                print(f"You are the only remaining werewolf.")
            print('Please select a player to hunt...')
            player_hunted = self.ask_player(players, excluded_players=werewolves)
            return ('HUNTED', player_hunted)
        elif self.role == Roles.DOCTOR:
            print('Please select a player that you would like to save...')
            player_saved = self.ask_player(players)
            return ('SAVED', player_saved)
        elif self.role == Roles.SEER:
            print('Please select a player that you would like to know about...')
            selected_player = self.ask_player(players, excluded_players=[self])
            print(f'{selected_player.name} {"is NOT" if selected_player.role != Roles.WEREWOLF else "IS"} a Werewolf...')
            input('Press enter to continue...')
            return None

    def day(self, players):
        os.system('cls')
        print(f'Client{self.name}: Time for trial...')
        print(f'{self.name} please select the person you would like to put on trial...')
        vote = self.ask_player(players, excluded_players=[self])
        return vote

    def check_winner(self, werewolves_won):
        print(f'Client-{self.name}: You were a {self.role}{", and thus a Villager. " if self.role != Roles.WEREWOLF and self.role != Roles.VILLAGER else ". "}', end='')
        if (werewolves_won and self.role == Roles.WEREWOLF) or (not werewolves_won and self.role != Roles.WEREWOLF):
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
    server.clients = [Client(f'Player {i}') for i in range(1, 5)]
    server.serve()
