from roles import Roles
from utils import shuffle_list
import threading
import socket
import os


ROLES_TO_ASSIGN = [Roles.WEREWOLF, Roles.DOCTOR, Roles.SEER]

HOST, PORT = 'localhost', 55555    

class WerewolfModeratorServer(socket.socket):
    def __init__(self):
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []
        self.active_players = []
        self.done = False
        self.exit = False
        self.adding_players = False

        self.start_server()
        self.accept_players()
    
    def start_server(self):
        print(f'Server listening on {HOST}:{PORT}')
        self.bind((HOST, PORT))
        self.listen(5)            
        server_thread = threading.Thread(target=self.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    def serve_forever(self):
        while True:
            conn, adr = self.accept()
            if self.adding_players:
                name = conn.recv(4096).decode()
                client = {
                    'name': name,
                    'socket': conn,
                    'role': Roles.VILLAGER
                }
                self.clients.append(client)
                conn.send("Welcome to Werewolf, please wait for all of the players to join...".encode())
            else:
                conn.send('Game has already begun...'.encode())
                conn.close()
    
    def accept_players(self):
        self.adding_players = True
        while self.adding_players and not self.exit:
            print(f'Current Players: {[client["name"] for client in self.clients]}')
            selection = int(input('\t1. Begin\n\t2. Exit\nPlease make a selection: '''))    
            if selection == 1:
                # if len(self.clients) >= len(ROLES_TO_ASSIGN) + 2:
                if len(self.clients) >= 1:
                    self.adding_players = False
                    self.active_players = list(self.clients)
                    self.assign_roles()
                    self.begin()
                else:
                    print('Not enough players to begin...')        
            elif selection == 2:
                self.adding_players = False
                self.exit = True
                self.close()

    def broadcast(self, msg):
        for client in self.clients:
            client['socket'].send(msg.encode())
        
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
            player['role'] = role
        
        shuffle_list(self.active_players)
        for client in self.clients:
            client['socket'].send(client['role'].value.encode())
            
    def day(self):
        encoded_players = ','.join([f'{player["name"]}:{player["role"]}' for player in self.active_players])
        votes = []
        for player in self.active_players:
            player['socket'].send(f'DAY|{encoded_players}'.encode())
            vote = player['socket'].recv(4096).decode()
            votes.append(vote)
        
        player_with_most_votes = max(votes, key=votes.count)
        if (votes.count(player_with_most_votes) > len(self.active_players) // 2):
            print(f'Server: {player_with_most_votes} has been jailed...')
            self.active_players = [player for player in self.active_players if player['name'] != player_with_most_votes]
        else:
            print('Server: No player recieved a majority vote...')
        self.check_game_over()

    def night(self):
        encoded_players = ','.join([f'{player["name"]}:{player["role"]}' for player in self.active_players])
        selected_players_encoded = []
        for player in self.active_players:
            player['socket'].send(f'NIGHT|{encoded_players}'.encode())
            selected_player_encoded = player['socket'].recv(4096).decode()
            if selected_player_encoded:
                selected_players_encoded.append(selected_player_encoded)

        selected_players = [player.split('|') for player in selected_players_encoded]
        saved_players = [selected_player[1] for selected_player in selected_players if selected_player[0] == 'SAVED']
        hunted_players = [selected_player[1] for selected_player in selected_players if selected_player[0] == 'HUNTED']

        if saved_players:
            player_saved = max(saved_players, key=saved_players.count)
        else:
            player_saved = None
        
        if hunted_players:
            player_hunted = max(hunted_players, key=hunted_players.count)

        if player_saved == player_hunted:
            print(f'Server: {player_hunted} was hunted, but saved...')
        else:
            print(f'Server: {player_hunted} was hunted during the night...')
            self.active_players = [player for player in self.active_players if player['name'] != player_hunted]
        self.check_game_over()
    
    def check_game_over(self):
        num_werewolves = len([player for player in self.active_players if player['role'] == Roles.WEREWOLF])
        num_villagers = len([player for player in self.active_players if player['role'] != Roles.WEREWOLF])
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
            client['socket'].send(f'DONE|{werewolves_won}'.encode())
    

if __name__ == '__main__':
    server = WerewolfModeratorServer()