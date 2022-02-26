import threading
import time
from utils import Roles
import os
import socket

HOST = 'localhost'
PORT = 55555

class Player:
    def __init__(self, name, role):
        self.name = name
        self.role = role
    
    @classmethod
    def prompt_name(cls):
        name = ''
        while not name:
            name = input('Please enter your name: ')
            if not name:
                print('Name cannot be blank, try again...')
        return name

class Client(Player):
    def __init__(self):
        name = Player.prompt_name()
        super().__init__(name, None)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def connect_to_server(self):
        self.socket.connect((HOST, PORT))
        self.socket.send(self.name.encode())
        msg = self.socket.recv(4096).decode()
        print(msg)
        role = self.socket.recv(4096).decode()
        if role:
            self.role = Roles(role)
            print(f'The game is beginning, you are a {self.role}')
            print(f'Wait until day/night begin...')

            self.receive_from_server()
        else:
            self.socket.close()

    def parse_players(self, players_encoded):
        players_encoded_list = players_encoded.split(',')
        other_players = []
        for player in players_encoded_list:
            name, role = player.split(':')
            role = Roles(role)
            other_players.append(Player(name, role))
        return other_players

    def receive_from_server(self):
        while True:
            from_server = self.socket.recv(4096).decode().strip()
            
            if not from_server:
                break

            action, rem = from_server.split('|')
            
            if action == 'NIGHT':
                other_players = self.parse_players(rem)
                selected_player = self.night(other_players)
                self.socket.send(selected_player.encode())
            elif action == 'DAY':
                other_players = self.parse_players(rem)
                vote = self.day(other_players)
                self.socket.send(vote.encode())
            elif action == 'ELIMINATED':
                os.system('cls')
                print('You have been eliminated')
            elif action == 'DONE':
                werewolves_won = (rem == 'True')
                self.check_winner(werewolves_won)
            
                    
        self.socket.close()
        print('Disconnected from server')

    def night(self, players):
        os.system('cls')
        input(f'{self.name}, press enter when you are ready...')
        print(f'You are a {self.role}')
        if self.role == Roles.VILLAGER:
            print('Please select a random person...')
            self.ask_player(players)
            return 'NONE|NONE'
        elif self.role == Roles.WEREWOLF:
            werewolves = [player.name for player in players if player.role == Roles.WEREWOLF]
            if len(werewolves) > 1:
                print(f'The other werewolves are: {" ".join([werewolf.name for werewolf in werewolves])}')
            else:
                print(f"You are the only remaining werewolf.")
            print('Please select a player to hunt...')
            player_hunted = self.ask_player(players, excluded_players=werewolves)
            return f'HUNTED|{player_hunted.name}'
        elif self.role == Roles.DOCTOR:
            print('Please select a player that you would like to save...')
            player_saved = self.ask_player(players)
            return f'SAVED|{player_saved.name}'
        elif self.role == Roles.SEER:
            print('Please select a player that you would like to know about...')
            selected_player = self.ask_player(players, excluded_players=[self.name])
            print(f'{selected_player.name} {"is NOT" if selected_player.role != Roles.WEREWOLF else "IS"} a Werewolf...')
            input('Press enter to continue...')
            return 'NONE|NONE'

    def day(self, players):
        os.system('cls')
        print(f'Client{self.name}: Time for trial...')
        print(f'{self.name} please select the person you would like to put on trial...')
        player = self.ask_player(players, excluded_players=[self.name])
        return player.name

    def check_winner(self, werewolves_won):
        print(f'You were a {self.role}{", and thus a Villager. " if self.role != Roles.WEREWOLF and self.role != Roles.VILLAGER else ". "}', end='')
        if (werewolves_won and self.role == Roles.WEREWOLF) or (not werewolves_won and self.role != Roles.WEREWOLF):
            print('You have won!')
        else:
            print('You have lost!')

    def ask_player(self, players, excluded_players=None):
        if excluded_players:
            available_players = [player for player in players if player.name not in excluded_players]
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

if __name__ == "__main__":
    client = Client()
    client.connect_to_server()
