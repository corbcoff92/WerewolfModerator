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
        self.clients_lb = tk.Listbox(master=self.clients_frame, selectmode=tk.SINGLE, width=40, height=10)
        self.clients_lb.pack(side=tk.TOP)
        self.scroll_bar = tk.Scrollbar(master=self)
        self.scroll_bar.config(command=self.clients_lb.yview)
        self.scroll_bar.pack(side=tk.RIGHT, fill=tk.Y)
        self.clients_lb.config(yscrollcommand=self.scroll_bar.set)
        self.clients_frame.pack(side=tk.TOP)
    
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
        self.select_btn = tk.Button(master=self, text='Select', command=self.select_client)
        self.select_btn.pack()

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
        self.clients_lb.insert(tk.END, '--------------- VILLAGERS --------------\n')
        for client in villagers:
            self.clients_lb.insert(tk.END, f'{client["name"]}:{client["role"].value.capitalize()}\n')
        
        self.clients_lb.insert(tk.END, '-------------- WEREWOLVES --------------\n')
        for client in werewolves:
            self.clients_lb.insert(tk.END, f'{client["name"]} : {client["role"].value.capitalize()}\n')
        self.clients_lb.config(state=tk.DISABLED)

def shuffle_list(l):
    num_items = len(l)
    for _ in range(5):
        for item in l:
            idx = randint(0, num_items - 1)
            l.append(l.pop(idx))