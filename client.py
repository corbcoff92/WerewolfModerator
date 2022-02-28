import threading
import time
from shared import Roles
import socket
import tkinter as tk
from tkinter.messagebox import askyesno, showerror, showinfo

HOST = 'localhost'
PORT = 55555

class WerewolfModeratorClientJoinFrame(tk.Frame):
    def __init__(self, client):
        super().__init__(master=client.window)
        self.client = client
        self.name_frame = tk.Frame(master=self)
        tk.Label(master=self.name_frame, text='Name: ').pack(side=tk.LEFT)
        self.name_ent = tk.Entry(master=self.name_frame)
        self.name_ent.pack(side=tk.LEFT)
        self.name_ent.focus()
        self.connect_btn = tk.Button(master=self.name_frame, text='Join', command=self.connect_to_server)
        self.name_ent.bind('<Return>', lambda event: self.connect_to_server())
        self.connect_btn.pack(side=tk.LEFT)
        self.name_frame.pack(side=tk.TOP)
    
    def connect_to_server(self):
        name = self.name_ent.get()
        if name:
            self.name_ent.unbind('<Return>')
            server_thread = threading.Thread(target=self.client.connect_to_server, args=(name,))
            server_thread.daemon = True
            server_thread.start()
        else:
            showerror(title='Invalid Name', message='Name cannot be blank, try again...')
    
    def connected(self):
        self.name_ent.config(state=tk.DISABLED)
        self.connect_btn.config(state=tk.DISABLED)


class WerewolfClientDisplay(tk.Frame):
    def __init__(self, frame):
        super().__init__(master=frame)

        self.clients = []

        self.selection_frame = tk.Frame(master=self)
        self.clients_lb = tk.Listbox(master=self.selection_frame, selectmode=tk.SINGLE, width=40, height=10)
        self.clients_lb.pack(side=tk.TOP)
        self.scroll_bar = tk.Scrollbar(master=self)
        self.scroll_bar.config(command=self.clients_lb.yview)
        self.scroll_bar.pack(side=tk.RIGHT, fill=tk.Y)
        self.clients_lb.config(yscrollcommand=self.scroll_bar.set)
        self.selection_frame.pack(side=tk.TOP)
    
    def update(self, clients, excluded_clients=[]):
        self.clients = clients
        self.clients_lb.config(state=tk.NORMAL)
        self.clients_lb.delete(0, tk.END)
        self.clients = [client for client in self.clients if client.name not in excluded_clients]
        self.clients_lb.insert(tk.END, *[client.name for client in self.clients])

class WerewolfClientDisplayRoles(WerewolfClientDisplay):
    def __init__(self, frame):
        super().__init__(frame)
    
    def update(self, clients):
        self.clients_lb.delete(0, tk.END)
        villagers = [client for client in clients if client.role != Roles.WEREWOLF]
        werewolves = [client for client in clients if client.role == Roles.WEREWOLF]
        self.clients_lb.insert(tk.END, f'-------------- VILLAGERS ---------------')
        self.clients_lb.insert(tk.END, *[f'{client.name} : {client.role}' for client in villagers])
        self.clients_lb.insert(tk.END, f'-------------- WEREWOLVES --------------')
        self.clients_lb.insert(tk.END, *[f'{client.name} : {client.role}' for client in werewolves])
        

class WerewolfSelectableClientDisplay(WerewolfClientDisplay):
    def __init__(self, frame, client):
        super().__init__(frame)
        self.client = client
        self.select_btn = tk.Button(master=self, text='Select', command=self.select_client)
        self.select_btn.pack()
    
    def select_client(self):
        selection = self.clients_lb.curselection()
        if selection:
            idx = selection[0]
            self.client.selected_player = self.clients[idx]
        else:
            showerror(title='No Selection', message='You must select an item...')

class WerewolfGameOverClientDisplay(tk.Frame):
    def __init__(self, window):
        super().__init__(master=window)
        self.role_lbl = tk.Label(master=self, text='')
        self.role_lbl.pack(side=tk.TOP)
        self.winning_lbl = tk.Label(master=self, text='')
        self.winning_lbl.pack(side=tk.TOP)
    
    def display(self, role, werewolves_won):
        self.role_lbl['text'] = f'You were a {role}{", and thus a Villager. " if role != Roles.WEREWOLF and role != Roles.VILLAGER else ". "}'
        if (werewolves_won and role == Roles.WEREWOLF) or (not werewolves_won and role != Roles.WEREWOLF):
            self.winning_lbl['text'] = 'You have won!'
        else:
            self.winning_lbl['text'] = 'You have lost!'

class WerewolfModeratorEliminationFrame(tk.Frame):
    def __init__(self, window):
        super().__init__(master=window)
    
    def display(self):
        tk.Label(master=self, text= f'You have been eliminated').pack()
        tk.Label(master=self, text='Please do not disclose your role...').pack(side=tk.TOP)
        tk.Label(master=self, text='All roles will be displayed when the game is over...').pack(side=tk.TOP)


class WerewolfModeratorPlayerSelectionFrame(tk.Frame):
    def __init__(self, client):
        super().__init__(master=client.window)
        self.players = []

        self.message_lbl = tk.Label(master=self, text='')
        self.message_lbl.pack(side=tk.TOP)
        self.selection_lbl = tk.Label(master=self, text='')
        self.selection_lbl.pack(side=tk.TOP)

        self.client_display = WerewolfSelectableClientDisplay(self, client)
        self.client_display.pack(side=tk.TOP)
    
    def update(self, clients, excluded_clients=[]):
        self.client_display.update(clients, excluded_clients=excluded_clients)    

class Player:
    def __init__(self, name=None, role=None):
        self.name = name
        self.role = role
    
class Client(socket.socket, Player):
    def __init__(self):
        Player.__init__(self)
        socket.socket.__init__(self, socket.AF_INET, socket.SOCK_STREAM)

        self.window = tk.Tk()
        self.window.resizable(False, False)
        self.window.geometry('300x300')
        self.window.protocol('WM_DELETE_WINDOW', self.on_close)
        
        self.join_frame = WerewolfModeratorClientJoinFrame(self)
        self.join_frame.pack(side=tk.TOP)
        self.role_lbl = tk.Label(master=self.window, text='Enter your name and click to join the server...')
        self.role_lbl.pack(side=tk.TOP)
        self.main_frame = tk.Frame(master=self.window)
        self.main_message_lbl = tk.Label(master=self.main_frame, text='')
        self.main_message_lbl.pack(side=tk.TOP)

        self.player_select_frame = WerewolfModeratorPlayerSelectionFrame(self)
        self.eliminated_frame = WerewolfModeratorEliminationFrame(self.window)
        self.gameover_frame = WerewolfGameOverClientDisplay(self.window)
        self.frame_windows = [self.main_frame, self.player_select_frame, self.eliminated_frame, self.gameover_frame]
        
        self.selected_player = []

    def display_frame(self, frame_to_display):
        for frame in self.frame_windows:
            if frame != frame_to_display:
                frame.pack_forget()
            else:
                frame.pack()

    def on_close(self):
        if askyesno(title='Exit?', message='Are you sure you want to exit? You will be disconnected from the server...'):
            self.window.destroy()
            self.close()

    def begin(self):
        self.display_frame(self.join_frame)
        self.window.mainloop()
    
    def connect_to_server(self, name):
        self.name = name
        try:
            self.connect((HOST, PORT))
            self.send(self.name.encode())
        except Exception:
            showerror(title='Unable to Connect to Server', message='Unable to connect to the server, please try again later...')
        else:
            self.join_frame.connected()
            msg = self.recv(4096).decode()
            self.role_lbl['text'] = 'Welome to Werewolf'
            self.main_message_lbl['text'] = 'Roles will be assigned when game begins...'
            role = self.recv(4096).decode()
            if role:
                self.role = Roles(role)
                self.main_message_lbl['text'] = f'The game is beginning...\nNo action required until day or night begin...'
                self.role_lbl['text'] = f'Role: {self.role}'
                self.receive_from_server()
            else:
                self.close()

        

    def parse_players(self, players_encoded):
        players_encoded_list = players_encoded.split(',')
        players = []
        for player in players_encoded_list:
            name, role = player.split(':')
            role = Roles(role)
            players.append(Player(name, role))
        return players

    def receive_from_server(self):
        while True:
            from_server = self.recv(4096).decode().strip()
            
            if not from_server:
                break

            action, rem = from_server.split('|')
            
            if action == 'NIGHT':
                self.selected_player = []
                players = self.parse_players(rem)
                self.night(players)
            elif action == 'DAY':
                self.selected_player = []
                players = self.parse_players(rem)
                self.day(players)
            elif action == 'ELIMINATED':
                self.eliminated_frame.display()
                self.display_frame(self.eliminated_frame)
            elif action == 'DONE':
                werewolves_won = (rem == 'True')
                self.gameover_frame.display(self.role, werewolves_won)
                self.display_frame(self.gameover_frame)
        self.close()
        showerror(title='Server Disconnected', message='Disconnected from server')

    def night(self, players):
        self.main_message_lbl['text'] = f'Night'
        if self.role == Roles.VILLAGER:
            self.player_select_frame.message_lbl['text'] = 'Select a random person...'
            excluded_players = []
        elif self.role == Roles.WEREWOLF:
            werewolves = [player.name for player in players if player.role == Roles.WEREWOLF]
            excluded_players=werewolves
            self.player_select_frame.selection_lbl['text'] = f'Other werewolves: {", ".join([werewolf.name for werewolf in werewolves]) if len(werewolves) > 1 else "None"}'
            self.player_select_frame.message_lbl['text'] = 'Select the player you would like to hunt...'
        elif self.role == Roles.DOCTOR:
            self.player_select_frame.message_lbl['text'] = 'Select the player you would like to save...'
            excluded_players = []
        elif self.role == Roles.SEER:
            self.player_select_frame.message_lbl['text'] = 'Select the player you would like to identify...'
            excluded_players = [self.name]


        self.player_select_frame.update(players, excluded_players)
        self.display_frame(self.player_select_frame)
        self.wait_select_player()
        self.main_message_lbl['text'] = f'Waiting for other players to respond...'
        self.display_frame(self.main_frame)

        try:
            if self.role == Roles.VILLAGER:
                self.send(f'NONE|{self.selected_player.name}'.encode())
                showinfo(title='Selection Sent', message='Your selection has been sent...')
            elif self.role == Roles.WEREWOLF:
                self.send(f'HUNTED|{self.selected_player.name}'.encode())
                showinfo(title='Selection Sent', message='Your selection has been sent...')
            elif self.role == Roles.DOCTOR:
                self.send(f'SAVED|{self.selected_player.name}'.encode())
                showinfo(title='Selection Sent', message='Your selection has been sent...')
            elif self.role == Roles.SEER:
                werewolf_found = self.selected_player.role == Roles.WEREWOLF
                self.send(f'NONE|{self.selected_player.name}'.encode())
                showinfo(title=f'{"Werewolf" if werewolf_found else "Villager"} Identified', message=f'{self.selected_player.name} {"is NOT" if not werewolf_found else "IS"} a Werewolf...')
        except Exception as e:
            showerror(title='Reponse Not Sent')
            
    
    def day(self, players):
        self.main_message_lbl['text'] = 'Day'
        self.player_select_frame.selection_lbl['text'] = 'Please select a person for trial...'
        self.player_select_frame.update(players, [self.name])
        
        self.display_frame(self.player_select_frame)
        self.wait_select_player()
        self.main_message_lbl['text'] = f'Waiting for other players to respond...'
        self.display_frame(self.main_frame)

        self.send(self.selected_player.name.encode())


    def wait_select_player(self):
        while not self.selected_player:
            time.sleep(1)

if __name__ == "__main__":
    with Client() as client:
        client.begin()
    
