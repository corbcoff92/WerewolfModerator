import time
from shared import Roles, WerewolfModeratorClientDisplay, WerewolfModeratorClientRolesDisplay
from shared import shuffle_list
import threading
import socketserver
import tkinter as tk
from tkinter.messagebox import askyesno, showerror, showinfo

ROLES_TO_ASSIGN = [Roles.WEREWOLF, Roles.DOCTOR, Roles.SEER]

HOST, PORT = 'localhost', 55555            

class WerewolfModeratorRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        name = self.request.recv(4096).decode()
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
                
                self.request.close()
                self.server.remove_client(client)
            else:
                self.request.send(f"{False}|That name is already being used...".encode())
        else:
            self.request.send(f'{False}|Game has already begun...'.encode())
            self.request.close()

class AcceptClientsFrame(tk.Frame):
    def __init__(self, server):
        super().__init__(master=server.window)
        self.top_frame = tk.Frame(master=self)
        self.connection_lbl = tk.Label(master=self.top_frame, text=f'Connected Players')
        self.connection_lbl.pack(side=tk.TOP)
        self.top_frame.pack(side=tk.TOP)

        self.connected_clients_display = WerewolfModeratorClientDisplay(self)
        self.connected_clients_display.pack(side=tk.TOP)

        self.bottom_frame = tk.Frame(master=self)
        self.begin_game_btn = tk.Button(master=self.bottom_frame, text='Begin Game', state=tk.DISABLED, command=server.begin)
        self.begin_game_btn.pack()
        self.bottom_frame.pack(side=tk.BOTTOM)
    
    def update(self, clients, num_clients_required_to_begin):
        self.connected_clients_display.update(clients)
        if len(clients) >= num_clients_required_to_begin:
            self.begin_game_btn.config(state=tk.NORMAL)
        else:
            self.begin_game_btn.config(state=tk.DISABLED)



class WerewolfModeratorWaitingFrame(tk.Frame):
    def __init__(self, werewolf_moderator):
        super().__init__(master=werewolf_moderator.window)
        self.werewolf_moderator = werewolf_moderator

        self.main_lbl = tk.Label(master=self, text='Waiting')
        self.main_lbl.pack(side=tk.TOP)
        self.message_lbl = tk.Label(master=self, text='Waiting for responses from: ')
        self.message_lbl.pack(side=tk.TOP)

        self.waiting_clients_display = WerewolfModeratorClientDisplay(self)
        self.waiting_clients_display.pack(side=tk.TOP)

        # self.bottom_frame = tk.Frame(master=self)
        # self.begin_game_btn = tk.Button(master=self.bottom_frame, text='Begin Game', command=server.begin)
        # self.begin_game_btn.pack()
        # self.bottom_frame.pack(side=tk.BOTTOM)

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
        self.client_display.pack(side=tk.TOP)

        self.btn_frame = tk.Frame(master=self)
        self.exit_btn = tk.Button(master=self, text='Exit', command=server.on_close)
        self.exit_btn.pack(side=tk.RIGHT)
        self.server_btn = tk.Button(master=self, text='Main Menu', command=server.accept_clients)
        self.server_btn.pack(side=tk.LEFT)
        self.btn_frame.pack(side=tk.TOP)
        

    def update(self, clients, werewolves_won):
        self.message_lbl['text'] = f'{"Werewolves" if werewolves_won else "Villagers"} have won!'
        self.client_display.update(clients)


class WerewolfModeratorMainMenu(tk.Frame):
    def __init__(self, werewolf_moderator):
        super().__init__(master=werewolf_moderator.window)
        
        self.werewolf_moderator = werewolf_moderator

        self.message_lbl = tk.Label(master=self, text='Select an option below...')
        self.message_lbl.grid(row=0, column=0)

        self.night_btn = tk.Button(master=self, text='Night', command=self.night)
        self.night_btn.grid(row=1, column=0, sticky='EW', padx=5, pady=(5, 0))

        self.day_btn = tk.Button(master=self, text='Day', command=self.day)
        self.day_btn.grid(row=2, column=0, sticky='EW', padx=5, pady=(5, 0))

        self.exit_btn = tk.Button(master=self, text='Exit', command=werewolf_moderator.on_close)
        self.exit_btn.grid(row=3, column=0, sticky='EW', padx=5, pady=(5, 0))
    
    def night(self):
        night_thread = threading.Thread(target=self.werewolf_moderator.night)
        night_thread.start()

    def day(self):
        day_thread = threading.Thread(target=self.werewolf_moderator.day)
        day_thread.start()


class WerewolfModerator(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(self):
        super().__init__((HOST, PORT), WerewolfModeratorRequestHandler)

        self.window = tk.Tk()
        self.window.title('Werewolf Moderator')
        self.window.resizable(False, False)
        self.window.geometry("300x300")
        self.window.protocol('WM_DELETE_WINDOW', self.on_close)

        self.clients = []
        self.active_players = []
        self.clients_responded = []
        self.responses = []
        self.done = False
        self.exit = False
        self.adding_players = False
        
        # Frames
        self.accept_clients_frame = AcceptClientsFrame(self)
        self.main_menu = WerewolfModeratorMainMenu(self)
        self.waiting_frame = WerewolfModeratorWaitingFrame(self)
        self.game_over_frame = WerewolfModeratorGameOverFrame(self)
        self.frames = [self.accept_clients_frame, self.main_menu, self.waiting_frame, self.game_over_frame]

        self.accept_clients()
        self.start_server()

    def display_frame_window(self, frame_to_display):
        for frame in self.frames:
            if frame_to_display == frame:
                frame.pack()
            else:
                frame.pack_forget()

    def accept_clients(self):
        self.adding_players = True
        self.display_frame_window(self.accept_clients_frame)

    def on_close(self):
        if askyesno(title='Exit?', message='Are you sure you want to exit? All clients will be disconnected...'):
            self.shutdown()
            self.window.destroy()

    def start_server(self):
        server_thread = threading.Thread(target=self.serve_forever)
        server_thread.start()

    def add_client(self, client):
        self.clients.append(client)
        num_players_required = len(ROLES_TO_ASSIGN) + 1
        self.accept_clients_frame.update([client['name'] for client in self.clients], 2)

    def broadcast(self, clients, msg):
        for client in clients:
            client['socket'].send(msg.encode())
        
    def begin(self):
        num_players_required = len(ROLES_TO_ASSIGN) + 1
        if len(self.clients) >= 1:
            self.adding_players = False
            self.active_players = list(self.clients)
            self.accept_clients_frame.pack_forget()
            self.main_menu.pack()
            self.assign_roles()
        else:
            showerror(title='Not Enough Players', message=f'Not enough players to begin the game. You must have at least {num_players_required} players to begin, please wait for other players to join...')

    def assign_roles(self):
        roles_to_assign = list(ROLES_TO_ASSIGN)
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

    def wait_for_responses(self):
        while len(self.responses) < len(self.active_players):
            time.sleep(1)
            self.waiting_frame.update()
    
    def day(self):
        self.responses = []
        self.clients_responded = []
        encoded_players = ','.join([f'{player["name"]}:{player["role"]}' for player in self.active_players])
        self.broadcast(self.active_players, f'DAY|{encoded_players}')
        
        self.waiting_frame.main_lbl['text'] = 'Day...'
        self.main_menu.pack_forget()
        self.waiting_frame.update()
        self.waiting_frame.pack()
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
        self.waiting_frame.pack_forget()
        self.main_menu.pack()
        self.check_game_over()

    def night(self):
        self.responses = []
        self.clients_responded = []
        encoded_players = ','.join([f'{player["name"]}:{player["role"]}' for player in self.active_players])
        self.broadcast(self.active_players, f'NIGHT|{encoded_players}')
        
        self.waiting_frame.main_lbl['text'] = 'Night...'
        self.main_menu.pack_forget()
        self.waiting_frame.update()
        self.waiting_frame.pack()
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

        if player_saved == player_hunted:
            showinfo(title='No Player Eliminated', message=f'{player_hunted} was hunted, but saved...')
            self.broadcast(self.active_players, 'NOT_ELIMINATED|No player was eliminated during the night')
        else:
            showinfo(title='Player Eliminated', message=f'{player_hunted} was hunted during the night...')
            self.remove_active_player(player_hunted)
            self.broadcast(self.active_players, 'NOT_ELIMINATED|You were NOT eliminated during the night')
        
        self.waiting_frame.pack_forget()
        self.main_menu.pack()
        self.check_game_over()            

    def remove_active_player(self, player_name):
        try:
            removed_player = next((player for player in self.active_players if player['name'] == player_name))
            removed_player['socket'].send(f'ELIMINATED|'.encode())
            self.active_players = [player for player in self.active_players if player != removed_player]
        except IndexError as e:
            showerror(title='Player disconnected', message=f'{player_name} has been disconnected from the server...')

    def remove_client(self, client):
        self.clients = [current_client for current_client in self.clients if current_client == client]
        self.active_players = [player for player in self.active_players if player != client]
        print(f'{client["name"]} has been disconnected')

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
        
        self.main_menu.pack_forget()
        self.game_over_frame.update(self.clients, werewolves_won)
        self.game_over_frame.pack()
        
        if werewolves_won:
            showinfo(title='Game Over', message='The werewolves have won!')
        else:
            showinfo(title='Game Over', message='The villagers have won!')
    

if __name__ == '__main__':
    with WerewolfModerator() as server:
        server.window.mainloop()