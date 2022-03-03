import socket
import time
from shared import HOST, PORT, Roles, WerewolfModeratorClientDisplay, WerewolfModeratorClientRolesDisplay, shuffle_list
import threading
import socketserver
import tkinter as tk
from tkinter.messagebox import askyesno, showerror, showinfo


ROLES_TO_ASSIGN = [Roles.WEREWOLF, Roles.DOCTOR, Roles.SEER]            


class AcceptClientsFrame(tk.Frame):
    def __init__(self, server, num_clients_required_to_begin):
        super().__init__(master=server.window)
        self.num_clients_required_to_begin = num_clients_required_to_begin

        self.top_frame = tk.Frame(master=self)
        self.connection_lbl = tk.Label(master=self.top_frame, text=f'Connected Players')
        self.connection_lbl.pack(side=tk.TOP)
        self.top_frame.pack(side=tk.TOP)

        self.connected_clients_display = WerewolfModeratorClientDisplay(self)
        self.connected_clients_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.bottom_frame = tk.Frame(master=self)
        self.begin_game_btn = tk.Button(master=self.bottom_frame, text='Begin Game', state=tk.DISABLED, command=server.begin)
        self.begin_game_btn.pack()
        self.bottom_frame.pack(side=tk.BOTTOM, pady=(10,0))
    
    def update(self, clients):
        self.connected_clients_display.update(clients)
        if len(clients) >= self.num_clients_required_to_begin:
            self.begin_game_btn.config(state=tk.NORMAL)
        else:
            self.begin_game_btn.config(state=tk.DISABLED)


class WerewolfModeratorMainMenu(tk.Frame):
    def __init__(self, werewolf_moderator):
        super().__init__(master=werewolf_moderator.window)
        self.werewolf_moderator = werewolf_moderator

        self.message_lbl = tk.Label(master=self, text='Select an option below...')
        self.message_lbl.pack(side=tk.TOP, pady=(5,5))

        self.night_btn = tk.Button(master=self, text='Night', height=4, command=self.night)
        self.night_btn.pack(side=tk.TOP, fill=tk.X, expand=True, padx=(10,10), pady=(5,0))

        self.day_btn = tk.Button(master=self, text='Day', height=4, command=self.day)
        self.day_btn.pack(side=tk.TOP, fill=tk.X, expand=True, padx=(10,10), pady=(5,0))

        self.exit_btn = tk.Button(master=self, text='Exit', height=4, command=werewolf_moderator.ask_close)
        self.exit_btn.pack(side=tk.TOP, fill=tk.X, expand=True, padx=(10,10), pady=(5,0))
    
    def night(self):
        night_thread = threading.Thread(target=self.werewolf_moderator.night)
        night_thread.daemon = True
        night_thread.start()

    def day(self):
        day_thread = threading.Thread(target=self.werewolf_moderator.day)
        day_thread.daemon = True
        day_thread.start()


class WerewolfModeratorWaitingFrame(tk.Frame):
    def __init__(self, werewolf_moderator):
        super().__init__(master=werewolf_moderator.window)
        self.werewolf_moderator = werewolf_moderator

        self.main_lbl = tk.Label(master=self, text='Waiting')
        self.main_lbl.pack(side=tk.TOP)
        self.message_lbl = tk.Label(master=self, text='Waiting for responses from: ')
        self.message_lbl.pack(side=tk.TOP)

        self.waiting_clients_display = WerewolfModeratorClientDisplay(self)
        self.waiting_clients_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def update(self):
        self.waiting_clients_display.update([client['name'] for client in self.werewolf_moderator.active_players if client not in self.werewolf_moderator.clients_responded])


class WerewolfModeratorGameOverFrame(tk.Frame):
    def __init__(self, server):
        super().__init__(master=server.window)

        self.main_lbl = tk.Label(master=self, text='Game Over')
        self.main_lbl.pack(side=tk.TOP)
        self.message_lbl = tk.Label(master=self, text='')
        self.message_lbl.pack(side=tk.TOP)

        self.client_display = WerewolfModeratorClientRolesDisplay(self)
        self.client_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.btn_frame = tk.Frame(master=self)
        self.server_btn = tk.Button(master=self.btn_frame, text='Main Menu', width=10,  command=server.accept_clients)
        self.server_btn.pack(side=tk.LEFT, padx=(0,5))
        self.exit_btn = tk.Button(master=self.btn_frame, text='Exit', width=10, command=server.exit)
        self.exit_btn.pack(side=tk.LEFT, padx=(5,0))
        self.btn_frame.pack(side=tk.BOTTOM, pady=(10,0))
        
    def update(self, clients, werewolves_won):
        self.message_lbl['text'] = f'{"Werewolves" if werewolves_won else "Villagers"} have won!'
        self.client_display.update(clients)


class WerewolfModeratorRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        name = self.request.recv(4096).decode().strip()
        if self.server.adding_players:
            if name not in [client['name'] for client in self.server.clients]:
                client = {
                    'name': name,
                    'socket': self.request,
                    'role': Roles.VILLAGER
                }
                self.server.add_client(client)
                self.request.send(f"{True}|Roles will be assigned when game begins...".encode())
                while True:
                    response = self.request.recv(4096).decode().strip()

                    if not response:
                        break

                    self.server.responses.append(response)
                    self.server.clients_responded.append(client)
                    self.server.waiting_frame.update()
                
                self.server.remove_client(client)
                self.request.shutdown(socket.SHUT_WR)
            else:
                self.request.send(f"{False}|That name is already being used...".encode())
        else:
            self.request.send(f'{False}|Game has already begun...'.encode())


class WerewolfModerator(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    def __init__(self):
        self.clients = []
        self.active_players = []
        self.clients_responded = []
        self.responses = []
        self.done = False
        self.exiting = False
        self.adding_players = False

        self.window = tk.Tk()
        self.window.title('Werewolf Moderator')
        self.window.resizable(False, False)
        self.window.geometry("300x300")
        self.window.protocol('WM_DELETE_WINDOW', self.ask_close)
        
        self.accept_clients_frame = AcceptClientsFrame(self, len(ROLES_TO_ASSIGN) + 1)
        self.main_menu = WerewolfModeratorMainMenu(self)
        self.waiting_frame = WerewolfModeratorWaitingFrame(self)
        self.game_over_frame = WerewolfModeratorGameOverFrame(self)
        self.frames = [self.accept_clients_frame, self.main_menu, self.waiting_frame, self.game_over_frame]

        self.start_server()
        self.accept_clients()

    def display_frame_window(self, frame_to_display):
        for frame in self.frames:
            if frame_to_display == frame:
                frame.pack(fill=tk.BOTH, padx=(10,10), pady=(10,10), expand=True)
            else:
                frame.pack_forget()

    def start_server(self):
        super().__init__((HOST, PORT), WerewolfModeratorRequestHandler)
        server_thread = threading.Thread(target=self.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    def accept_clients(self):
        self.adding_players = True
        self.accept_clients_frame.update([client['name'] for client in self.clients])
        self.display_frame_window(self.accept_clients_frame)

    def add_client(self, client):
        self.clients.append(client)
        self.accept_clients_frame.update([client['name'] for client in self.clients])
    
    def remove_client(self, client):
        removed_client = next((current_client for current_client in self.clients if current_client['name'] == client['name']))
        self.clients.remove(removed_client)

        if not self.exiting:
            if self.adding_players or self.done:
                self.accept_clients_frame.update([client['name'] for client in self.clients])
            else:
                self.remove_active_player(removed_client['name'])
    
    def remove_active_player(self, player_name):
        try:
            removed_player = next((player for player in self.active_players if player['name'] == player_name))
            removed_player['socket'].send(f'ELIMINATED|'.encode())
            self.active_players = [player for player in self.active_players if player != removed_player]
        except Exception as e:
            showerror(title='Player disconnected', message=f'{player_name} has been disconnected from the server...')
    
    def begin(self):
        self.done = False
        self.adding_players = False
        self.active_players = list(self.clients)
        self.display_frame_window(self.main_menu)
        self.assign_roles()

    def assign_roles(self):
        roles_to_assign = list(ROLES_TO_ASSIGN)

        if len(self.active_players) > len(ROLES_TO_ASSIGN) + 2:
            roles_to_assign.append(Roles.WEREWOLF)

        if len(self.active_players) >= 15:
            roles_to_assign.extend([Roles.WEREWOLF]*((len(self.active_players) - 11)//4))

        shuffle_list(roles_to_assign)
        shuffle_list(self.active_players)

        for player in self.active_players:
            if roles_to_assign:
                player['role'] = roles_to_assign.pop()
            else:
                player['role'] = Roles.VILLAGER
        
        shuffle_list(self.active_players)
        for client in self.clients:
            client['socket'].send(f'ROLE|{client["role"].value}'.encode())

    def broadcast(self, clients, msg):
        for client in clients:
            client['socket'].send(msg.encode())

    def wait_for_responses(self):
        while len(self.responses) < len(self.active_players):
            time.sleep(1)
            self.waiting_frame.update()

    def night(self):
        self.responses = []
        self.clients_responded = []
        
        encoded_players = ','.join([f'{player["name"]}:{player["role"]}' for player in self.active_players])
        self.broadcast(self.active_players, f'NIGHT|{encoded_players}')
        
        self.waiting_frame.main_lbl['text'] = 'Night...'
        self.waiting_frame.update()
        self.display_frame_window(self.waiting_frame)
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
        else:
            player_hunted = None

        if player_hunted:
            if player_saved == player_hunted:
                showinfo(title='No Player Eliminated', message=f'{player_hunted} was hunted, but saved...')
                self.broadcast(self.active_players, 'NOT_ELIMINATED|No player was eliminated during the night')
            else:
                showinfo(title='Player Eliminated', message=f'{player_hunted} was hunted during the night...')
                self.remove_active_player(player_hunted)
                self.broadcast(self.active_players, 'NOT_ELIMINATED|You were NOT eliminated during the night')
        
        self.display_frame_window(self.main_menu)
        self.check_game_over()

    def day(self):
        self.responses = []
        self.clients_responded = []
        
        encoded_players = ','.join([f'{player["name"]}:{player["role"]}' for player in self.active_players])
        self.broadcast(self.active_players, f'DAY|{encoded_players}')
        
        self.waiting_frame.main_lbl['text'] = 'Day...'
        self.waiting_frame.update()
        self.display_frame_window(self.waiting_frame)
        self.wait_for_responses()

        votes = self.responses
        player_with_most_votes = max(votes, key=votes.count)
        if (votes.count(player_with_most_votes) > len(self.active_players) // 2):
            showinfo(title='Player Eliminated', message=f'{player_with_most_votes} has been jailed...')
            self.remove_active_player(player_with_most_votes)
            self.broadcast(self.active_players, 'NOT_ELIMINATED|You were NOT jailed during the day...')
        else:
            showinfo(title='No Player Eliminated', message='No player recieved a majority vote...')
            self.broadcast(self.active_players, 'NOT_ELIMINATED|No player was jailed during the day...')
        
        self.display_frame_window(self.main_menu)
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
        self.broadcast(self.clients, f'DONE|{werewolves_won}')
        
        self.game_over_frame.update(self.clients, werewolves_won)
        self.display_frame_window(self.game_over_frame)
        
        if werewolves_won:
            showinfo(title='Game Over', message='The werewolves have won!')
        else:
            showinfo(title='Game Over', message='The villagers have won!')
    
    def ask_close(self):
        if askyesno(title='Exit?', message='Are you sure you want to exit? All clients will be disconnected...'):
            self.exit()

    def exit(self):
        self.exiting = True
        for client in self.clients:
            client['socket'].shutdown(socket.SHUT_WR)
        self.window.destroy()
    

if __name__ == '__main__':
    server = WerewolfModerator()
    server.window.mainloop()
    server.shutdown()