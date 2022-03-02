import threading
import time
from shared import Roles, WerewolfModeratorClientRolesDisplay, WerewolfModeratorSelectableClientDisplay
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
        self.name_ent = tk.Entry(master=self.name_frame, justify='center')
        self.name_ent.pack(side=tk.LEFT)
        self.name_ent.focus()
        self.connect_btn = tk.Button(master=self.name_frame, text='Join', command=self.connect_to_server)
        self.name_ent.bind('<Return>', lambda event: self.connect_to_server())
        self.connect_btn.pack(side=tk.LEFT)
        self.name_frame.pack(side=tk.TOP)
    
    def connect_to_server(self):
        name = self.name_ent.get()
        if 1 <= len(name) <= 15:
            self.client.connect_to_server(name)
        else:
            showerror(title='Invalid Name', message='Name must be between 1 and 15 characters long, try again...')
    
    def connected(self):
        self.name_ent.config(state=tk.DISABLED)
        self.connect_btn.config(state=tk.DISABLED)
        self.name_ent.unbind('<Return>')
        self.client.window.protocol('WM_DELETE_WINDOW', self.client.on_close)        

class WerewolfGameOverClientDisplay(tk.Frame):
    def __init__(self, werewolf_moderator):
        super().__init__(master=werewolf_moderator.window)
        self.werewolf_moderator = werewolf_moderator
        self.role_lbl = tk.Label(master=self, text='')
        self.role_lbl.pack(side=tk.TOP)
        self.winning_lbl = tk.Label(master=self, text='')
        self.winning_lbl.pack(side=tk.TOP)
        
        self.btn_frame = tk.Frame(master=self)
        self.server_btn = tk.Button(master=self.btn_frame, text='Play Again', width=10,  command=werewolf_moderator.play_again)
        self.server_btn.pack(side=tk.LEFT, padx=(0,5))
        self.exit_btn = tk.Button(master=self.btn_frame, text='Exit', width=10, command=werewolf_moderator.on_close)
        self.exit_btn.pack(side=tk.LEFT, padx=(5,0))
        self.btn_frame.pack(side=tk.BOTTOM, pady=(10,0))
         
            
    def display(self, role, werewolves_won):
        self.role_lbl['text'] = f'You were a {role}{", and thus a Villager. " if role != Roles.WEREWOLF and role != Roles.VILLAGER else ". "}'
        if (werewolves_won and role == Roles.WEREWOLF) or (not werewolves_won and role != Roles.WEREWOLF):
            self.winning_lbl['text'] = 'You have won!'
        else:
            self.winning_lbl['text'] = 'You have lost!'

class WerewolfModeratorEliminationFrame(tk.Frame):
    def __init__(self, window):
        super().__init__(master=window)
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

        self.client_display = WerewolfModeratorSelectableClientDisplay(self, client)
        self.client_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.select_btn = tk.Button(master=self, text='Select', command=self.client_display.select_client)
        self.select_btn.pack(side=tk.BOTTOM, pady=(10,0))
    
    def update(self, client_names, excluded_clients=[]):
        self.client_display.update(client_names, excluded_clients=excluded_clients)    

class Player:
    def __init__(self, name=None, role=None):
        self.name = name
        self.role = role
    
    def as_dict(self):
        return {'name':self.name, 'role':self.role}
    
class Client(socket.socket, Player):
    def __init__(self):
        Player.__init__(self)

        self.window = tk.Tk()
        self.window.title('Werewolf')
        self.window.resizable(False, False)
        self.window.geometry('300x300')
        
        self.join_frame = WerewolfModeratorClientJoinFrame(self)
        self.join_frame.pack(side=tk.TOP)
        self.role_lbl = tk.Label(master=self.window, text='Enter your name and click to join the server...')
        self.role_lbl.pack(side=tk.TOP)

        self.main_frame = tk.Frame(master=self.window)
        self.main_message_lbl = tk.Label(master=self.main_frame, text='')
        self.main_message_lbl.pack(side=tk.TOP)

        self.player_select_frame = WerewolfModeratorPlayerSelectionFrame(self)
        self.eliminated_frame = WerewolfModeratorEliminationFrame(self.window)
        self.gameover_frame = WerewolfGameOverClientDisplay(self)
        self.frame_windows = [self.main_frame, self.player_select_frame, self.eliminated_frame, self.gameover_frame]
        
        self.selected_player = []

        self.display_frame(self.main_frame)

    def display_frame(self, frame_to_display):
        for frame in self.frame_windows:
            if frame != frame_to_display:
                frame.pack_forget()
            else:
                frame.pack(fill=tk.BOTH, padx=(10,10), pady=(0,10), expand=True)

    def on_close(self):
        if askyesno(title='Exit?', message='Are you sure you want to exit? You will be disconnected from the server...'):
            self.shutdown(socket.SHUT_WR)
            self.window.destroy()        
    
    def connect_to_server(self, name):
        self.name = name
        try:
            socket.socket.__init__(self, socket.AF_INET, socket.SOCK_STREAM)
            self.connect((HOST, PORT))
            self.send(self.name.encode())
        except Exception as e:
            print(e)
            showerror(title='Unable to Connect to Server', message='Unable to connect to the server, please try again later...')
        else:
            accepted, msg = self.recv(4096).decode().split('|')
            if accepted == 'True':
                self.join_frame.connected()
                self.role_lbl['text'] = 'Welcome to Werewolf'
                self.main_message_lbl['text'] = msg
                send_receive_thread = threading.Thread(target=self.receive_from_server)
                send_receive_thread.daemon = True
                send_receive_thread.start()
            else:
                self.main_message_lbl['text'] = msg

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
            
            if action == 'ROLE':
                role = rem
                self.role = Roles(role)
                self.main_message_lbl['text'] = f'The game is beginning...\nNo action required until day or night begin...'
                self.role_lbl['text'] = f'Role: {self.role}'
                self.display_frame(self.main_frame)
            elif action == 'NIGHT':
                self.selected_player = []
                players = self.parse_players(rem)
                self.night(players)
            elif action == 'DAY':
                self.selected_player = []
                players = self.parse_players(rem)
                self.day(players)
            elif action == 'ELIMINATED':
                self.role_lbl['text'] = 'ELIMINATED'
                self.display_frame(self.eliminated_frame)
            elif action == 'NOT_ELIMINATED':
                msg = rem
                self.main_message_lbl['text'] = f'{msg}\nNo other action required until day or night...'
            elif action == 'DONE':
                werewolves_won = (rem == 'True')
                self.role_lbl['text'] = 'Game Over'
                self.main_message_lbl['text'] = f'{"Werewolves" if werewolves_won else "Villagers"} have won!'
                self.gameover_frame.display(self.role, werewolves_won)
                self.display_frame(self.gameover_frame)
        showerror(title='Server Disconnected', message='Disconnected from server')
        self.shutdown(socket.SHUT_WR)
        self.window.destroy()

    def night(self, players):
        self.player_select_frame.message_lbl['text'] = f'Night'
        if self.role == Roles.VILLAGER:
            self.player_select_frame.selection_lbl['text'] = 'Select a random person...'
            excluded_players = []
        elif self.role == Roles.WEREWOLF:
            werewolves = [player.name for player in players if player.role == Roles.WEREWOLF]
            excluded_players=werewolves
            self.player_select_frame.message_lbl['text'] += f'\nOther werewolves: {", ".join([werewolf.name for werewolf in werewolves]) if len(werewolves) > 1 else "None"}'
            self.player_select_frame.selection_lbl['text'] = 'Select the player you would like to hunt...'
        elif self.role == Roles.DOCTOR:
            self.player_select_frame.selection_lbl['text'] = 'Select the player you would like to save...'
            excluded_players = []
        elif self.role == Roles.SEER:
            self.player_select_frame.selection_lbl['text'] = 'Select the player you would like to identify...'
            excluded_players = [self.name]


        self.player_select_frame.update([player.name for player in players], excluded_players)
        self.display_frame(self.player_select_frame)
        self.wait_select_player()
        self.main_message_lbl['text'] = f'Waiting for other players to respond...'
        self.display_frame(self.main_frame)

        try:
            if self.role == Roles.VILLAGER:
                showinfo(title='Send Selection', message='Sending selection to server...')
                self.send(f'NONE|{self.selected_player}'.encode())
            elif self.role == Roles.WEREWOLF:
                showinfo(title='Send Selection', message='Sending selection to server...')
                self.send(f'HUNTED|{self.selected_player}'.encode())
            elif self.role == Roles.DOCTOR:
                showinfo(title='Send Selection', message='Sending selection to server...')
                self.send(f'SAVED|{self.selected_player}'.encode())
            elif self.role == Roles.SEER:
                selected_player_role = next((player.role for player in players if player.name == self.selected_player)) 
                werewolf_found = selected_player_role == Roles.WEREWOLF
                showinfo(title=f'{"Werewolf" if werewolf_found else "Villager"} Identified', message=f'{self.selected_player} {"is NOT" if not werewolf_found else "IS"} a Werewolf...')
                self.send(f'NONE|{self.selected_player}'.encode())
        except Exception as e:
            showerror(title='Reponse Not Sent', message=str(e))
            
    
    def day(self, players):
        self.player_select_frame.message_lbl['text'] = f'Day'
        self.player_select_frame.selection_lbl['text'] = 'Please select a person for trial...'
        self.player_select_frame.update([player.name for player in players], [self.name])
        
        self.display_frame(self.player_select_frame)
        self.wait_select_player()
        self.main_message_lbl['text'] = f'Waiting for other players to respond...'
        self.display_frame(self.main_frame)

        self.send(self.selected_player.encode())


    def wait_select_player(self):
        while not self.selected_player:
            time.sleep(1)
    
    def play_again(self):
        self.main_message_lbl['text'] = 'Please wait for the next game to begin...'
        self.display_frame(self.main_frame)

if __name__ == "__main__":
    client = Client()
    client.window.mainloop()
    
