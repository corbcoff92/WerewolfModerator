from random import randint
from enum import Enum
import tkinter as tk
from tkinter.messagebox import showerror

class Roles(Enum):
    VILLAGER = 'VILLAGER'
    WEREWOLF = 'WEREWOLF'
    DOCTOR = 'DOCTOR'
    SEER = 'SEER'
    
    def __str__(self):
        return self.value

class WerewolfModeratorClientDisplay(tk.Frame):
    def __init__(self, frame):
        super().__init__(master=frame)

        self.client_names = []

        self.clients_frame = tk.Frame(master=self)
        self.clients_lb = tk.Listbox(master=self.clients_frame, selectmode=tk.SINGLE, font=('Consolas', 14), height=5)
        self.clients_lb.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.scroll_bar = tk.Scrollbar(master=self)
        self.scroll_bar.config(command=self.clients_lb.yview)
        self.scroll_bar.pack(side=tk.RIGHT, fill=tk.Y)
        self.clients_lb.config(yscrollcommand=self.scroll_bar.set)
        self.clients_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    def clear(self):
        self.clients_lb.config(state=tk.NORMAL)
        self.clients_lb.delete(0, tk.END)

    def update(self, client_names, excluded_clients=[]):
        self.clear()
        self.client_names = [name for name in client_names if name not in excluded_clients]
        self.clients_lb.insert(tk.END, *[name for name in self.client_names])
        self.clients_lb.config(state=tk.DISABLED)

class WerewolfModeratorSelectableClientDisplay(WerewolfModeratorClientDisplay):
    def __init__(self, frame, werewolf_moderator):
        super().__init__(frame)
        self.werewolf_moderator = werewolf_moderator

    def update(self, client_names, excluded_clients=[]):
        super().update(client_names=client_names, excluded_clients=excluded_clients)
        self.clients_lb.config(state=tk.NORMAL)
        
    def select_client(self):
        selection = self.clients_lb.curselection()
        if selection:
            idx = selection[0]
            self.werewolf_moderator.selected_player = self.client_names[idx]
        else:
            showerror(title='No Selection', message='You must select an item...')

class WerewolfModeratorClientRolesDisplay(WerewolfModeratorClientDisplay):
    def __init__(self, frame):
        super().__init__(frame)
        
    def update(self, clients):
        self.clear()
        werewolves = [client for client in clients if client['role'] == Roles.WEREWOLF]
        villagers = [client for client in clients if client['role'] != Roles.WEREWOLF]

        self.clients_lb.config(state=tk.NORMAL)
        max_name_len = len(max(clients, key=lambda client: len(client['name']))['name']) + 2
        print(max_name_len)
        self.clients_lb.insert(tk.END, f'{" VILLAGERS ":^25}')
        for client in villagers:
            self.clients_lb.insert(tk.END, f'{client["name"].ljust(max_name_len)}{client["role"].value.capitalize()}')
        
        self.clients_lb.insert(tk.END, f'{" WEREWOLVES ":^25}\n')

        for client in werewolves:
            self.clients_lb.insert(tk.END, f'{client["name"].ljust(max_name_len)}{client["role"].value.capitalize()}')
        self.clients_lb.config(state=tk.DISABLED)

def shuffle_list(l):
    num_items = len(l)
    for _ in range(5):
        for item in l:
            idx = randint(0, num_items - 1)
            l.append(l.pop(idx))