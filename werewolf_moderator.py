from player import Player, Roles
import os
from random import randint

class SalemModerator:
    def __init__(self):
        self.player_names = []
        self.players = []
        self.game_over = False
        self.winners = None
        
    def begin(self):
        return self.assign_roles()
    
    def assign_roles(self):
        roles_to_assign = [Roles.WEREWOLF, Roles.DOCTOR, Roles.SEER]
        
        if len(self.player_names) < len(roles_to_assign) + 2:
            print('Not enough players to begin...')
            return False
        else:    
            if len(self.player_names) >= 15:
                roles_to_assign.extend([Roles.WEREWOLF]*((len(self.player_names) - 11)//4))
            
            while roles_to_assign and self.player_names:
                idx = randint(0, len(self.player_names)-1)
                self.players.append(Player(self.player_names.pop(idx), roles_to_assign.pop()))
            
            while self.player_names:
                self.players.append(Player(self.player_names.pop(), Roles.VILLAGER))
                return True
                
    @property
    def werewolves(self):
        return [player for player in self.players if player.role == Roles.WEREWOLF]
 
    @property
    def num_werewolves_remaining(self):
        return len(self.werewolves)
    
    def night(self):
        player_saved = None
        player_hunted = None
        for player in self.players:
            role = player.role
            os.system('cls')
            input(f'{player.name}, press enter when you are ready...')
            print(f'You are a {player.role}')
            if role == Roles.VILLAGER:
                print('Please select a random person...')
                self.ask_player()
            elif role == Roles.WEREWOLF:
                if self.num_werewolves_remaining > 1:
                    print(f'The other werewolves are: {" ".join([werewolf.name for werewolf in self.werewolves if werewolf != player])}')
                else:
                    print(f"You are the only remaining werewolf, ")
                print('Please select a player to hunt...')
                player_hunted = self.ask_player(excluded_players=self.werewolves)
            elif role == Roles.DOCTOR:
                print('Please select a player that you would like to save...')
                player_saved = self.ask_player()
            elif role == Roles.SEER:
                print('Please select a player that you would like to know about...')
                selected_player = self.ask_player(excluded_players=[player])
                print(f'{selected_player.name} {"is NOT" if selected_player.role != Roles.WEREWOLF else "IS"} a Werewolf...')
                input('Press enter to continue...')

        if player_saved == player_hunted:
            print(f'{player_hunted.name} was hunted, but saved...')
        else:
            print(f'{player_hunted.name} was hunted during the night...')
            self.players.remove(player_hunted)
            self.check_game_over()
    
    def day(self):
        votes = []
        for player in self.players:
            print(f'{player.name} please select the person you would like to put on trial...')
            votes.append(self.ask_player(excluded_players=[player]))

        player_with_most_votes = max(votes, key=votes.count)
        if (votes.count(player_with_most_votes) > len(self.players) // 2):
            print(f'{player_with_most_votes.name} has been jailed...')
            self.players.remove(player_with_most_votes)
            self.check_game_over()
        else:
            print('No player recieved a majority vote...')

    def check_game_over(self):
        if len(self.players) <= self.num_werewolves_remaining:
            self.winners = Roles.WEREWOLF
            self.game_over = True
        elif self.num_werewolves_remaining <= 0:
            self.winners = Roles.VILLAGER
            self.game_over = True

    def ask_player(self, excluded_players=None):
        if excluded_players:
            available_players = [player for player in self.players if player not in excluded_players]
        else:
            available_players = self.players
            
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

    def add_player(self, name):
        self.player_names.append(name)        

if __name__ == '__main__':
    s = SalemModerator()
    role = Roles.VILLAGER
    done = False
    adding_players = True
    while adding_players:
        selection = int(input('\t1. Add player\n\t2. Begin\n\t3. Exit\nPlease make a selection: '''))    
        if selection == 1:
            name = ''
            while not name:
                name = input('Please enter your name: ')
                if not name:
                    print('Name cannot be blank, try again...')
            s.add_player(name)
        elif selection == 2:
            adding_players = not s.begin()
        elif selection == 3:
            adding_players = False
            done = True

    while not done and not s.game_over:
        if not done:        
            selection = int(input('\t1. Night\n\t2. Day\n\t3. Exit\nPlease make a selection: '''))
            if selection == 1:
                s.night()
            elif selection == 2:
                s.day()
            elif selection == 3:
                done = True
    
        if s.game_over:
            if s.winners == Roles.WEREWOLF:
                print('The werewolves have won!')
            else:
                print('The villagers have won!')
    print('Exiting...')