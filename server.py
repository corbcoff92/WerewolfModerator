from shared import Roles
from shared import shuffle_list
import threading
import socketserver
import os


ROLES_TO_ASSIGN = [Roles.WEREWOLF, Roles.DOCTOR, Roles.SEER]

HOST, PORT = 'localhost', 55555    

class WerewolfModeratorRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        name = self.request.recv(4096).decode()
        if self.server.adding_players:
            client = {
                'name': name,
                'socket': self.request,
                'role': Roles.VILLAGER
            }
            self.server.add_client(client)
            self.request.send("Welcome to Werewolf, please wait for all of the players to join...".encode())
            while True:
                response = self.request.recv(4096).decode().strip()

                if not response:
                    break

                self.server.responses.append(response)
        else:
            self.request.send('Game has already begun...'.encode())


class WerewolfModeratorServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(self):
        super().__init__((HOST, PORT), WerewolfModeratorRequestHandler)
        self.clients = []
        self.active_players = []
        self.responses = []
        self.done = False
        self.exit = False
        self.adding_players = False
        self.start_server()
        self.accept_players()
    
    def start_server(self):
        print(f'Server listening on {HOST}:{PORT}')
        server_thread = threading.Thread(target=self.serve_forever)
        server_thread.daemon = True
        server_thread.start()                

    def add_client(self, client):
        print(f'\n{client["name"]} joined...')
        self.clients.append(client)


    def accept_players(self):
        self.adding_players = True
        while self.adding_players and not self.exit:
            selection = int(input('\t1. Begin\n\t2. Exit\nPlease make a selection: '''))    
            if selection == 1:
                if len(self.clients) >= len(ROLES_TO_ASSIGN) + 1:
                    self.adding_players = False
                    self.active_players = list(self.clients)
                    self.assign_roles()
                    self.begin()
                else:
                    print('Not enough players to begin...')        
            elif selection == 2:
                self.adding_players = False
                self.exit = True
                self.shutdown()

    def broadcast(self, clients, msg):
        for client in clients:
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

    def wait_for_responses(self):
        while len(self.responses) < len(self.active_players):
            pass

    def day(self):
        self.responses = []
        encoded_players = ','.join([f'{player["name"]}:{player["role"]}' for player in self.active_players])
        self.broadcast(self.active_players, f'DAY|{encoded_players}')
        
        os.system('cls')
        print('Daytime, waiting for responses...')
        self.wait_for_responses()

        votes = self.responses
        player_with_most_votes = max(votes, key=votes.count)
        if (votes.count(player_with_most_votes) > len(self.active_players) // 2):
            print(f'{player_with_most_votes} has been jailed...')
            self.remove_active_player(player_with_most_votes)
        else:
            print('No player recieved a majority vote...')
        self.check_game_over()

    def night(self):
        self.responses = []
        encoded_players = ','.join([f'{player["name"]}:{player["role"]}' for player in self.active_players])
        self.broadcast(self.active_players, f'NIGHT|{encoded_players}')

        print('Night time, waiitng for repsonses')
        self.wait_for_responses()
        
        selected_players = [player.split('|') for player in self.responses]
        saved_players = [selected_player[1] for selected_player in selected_players if selected_player[0] == 'SAVED']
        hunted_players = [selected_player[1] for selected_player in selected_players if selected_player[0] == 'HUNTED']

        if saved_players:
            player_saved = max(saved_players, key=saved_players.count)
        else:
            player_saved = None
        
        if hunted_players:
            player_hunted = max(hunted_players, key=hunted_players.count)

        if player_saved == player_hunted:
            print(f'{player_hunted} was hunted, but saved...')
        else:
            print(f'{player_hunted} was hunted during the night...')
            self.remove_active_player(player_hunted)
        self.check_game_over()
    
    def remove_active_player(self, player_name):
        removed_player = [player for player in self.active_players if player['name'] == player_name][0]
        removed_player['socket'].send(f'ELIMINATED|'.encode())
        self.active_players = [player for player in self.active_players if player != removed_player]

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
            print('The werewolves have won!')
        else:
            print('The villagers have won!')

        self.broadcast(self.clients, f'DONE|{werewolves_won}')
    

if __name__ == '__main__':
    server = WerewolfModeratorServer()
    server.shutdown()