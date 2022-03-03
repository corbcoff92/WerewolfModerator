from enum import Enum
import tkinter as tk


# IP address & port number for server & clients
HOST, PORT = 'localhost', 55555


class Roles(Enum):
    """ Roles for a game of werewolf. """
    VILLAGER = 'VILLAGER'
    WEREWOLF = 'WEREWOLF'
    DOCTOR = 'DOCTOR'
    SEER = 'SEER'
    
    def __str__(self):
        return self.value


class WerewolfModeratorClientDisplay(tk.Frame):
    """ 
    Tkinter frame containing a listbox for displaying clients.
    
    Extends:
            tkinter.Frame
    """
    def __init__(self, frame: tk.Frame) -> None:
        """
        Creates an instance of a WerewolfModeratorClientDisplay.

        This frame contains a listbox for displaying clients.
        
        Arguments:
            frame: tkinter.Frame
                Frame to which this client display should be added.
        """
        super().__init__(master=frame)
        self.client_names = []

        # Clients display
        self.clients_frame = tk.Frame(master=self)
        self.clients_lb = tk.Listbox(master=self.clients_frame, selectmode=tk.SINGLE, font=('Consolas', 14), height=5)
        self.clients_lb.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.scroll_bar = tk.Scrollbar(master=self)
        self.scroll_bar.config(command=self.clients_lb.yview)
        self.scroll_bar.pack(side=tk.RIGHT, fill=tk.Y)
        self.clients_lb.config(yscrollcommand=self.scroll_bar.set)
        self.clients_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    def clear(self) -> None:
        """ Clears the client display list box. """
        # Enable clients display for editing
        self.clients_lb.config(state=tk.NORMAL)
        self.clients_lb.delete(0, tk.END)

    def update(self, client_names: list[str], excluded_clients: list[str]=[]) -> None:
        """
        Updates the clients display listbox to reflect all of the clients in the given list of clients that
        are not contained in the optional excluded clients list.

        Aruments:
            client_names: list[str]
                Names of the clients that should be displayed and allowed for selection.
        Optional:
            excluded_clients: list[str], Default=[]
                Names of the clients that should not be displayed and allowed for selection.
        """
        self.clear()

        # Determine unexcluded clients
        self.client_names = [name for name in client_names if name not in excluded_clients]
        
        self.clients_lb.insert(tk.END, *[name for name in self.client_names])
        
        # Disable selectability of clients display
        self.clients_lb.config(state=tk.DISABLED)


class WerewolfModeratorClientRolesDisplay(WerewolfModeratorClientDisplay):
    """ 
    Tkinter frame containing a listbox for displaying clients and thier respective werewolf roles.
    
    Extends:
            tkinter.Frame
    """
    def __init__(self, frame: tk.Frame) -> None:
        """
        Creates an instance of a WerewolfModeratorClientRolesDisplay.

        This frame contains a listbox for displaying clients and thier respective werewolf roles.
        
        Arguments:
            frame: tkinter.Frame
                Frame to which this client display should be added.
        """
        super().__init__(frame)
        
    def update(self, clients: list[dict]) -> None:
        """
        Updates the clients display listbox to reflect all of the names and werewolf 
        roles for the clients in the given list of client dictionaries.

        Aruments:
            clients: list[dict]
                List of dictionaries containing client information, including their name and respective werewolf role.
        """
        self.clear()

        # Determine werewolves and villagers
        werewolves = [client for client in clients if client['role'] == Roles.WEREWOLF]
        villagers = [client for client in clients if client['role'] != Roles.WEREWOLF]

        # Enable listbox for editing
        self.clients_lb.config(state=tk.NORMAL)

        # Calculate width of name column
        max_name_len = len(max(clients, key=lambda client: len(client['name']))['name']) + 2
        
        # Display villagers
        self.clients_lb.insert(tk.END, f'{" VILLAGERS ":^25}')
        for client in villagers:
            self.clients_lb.insert(tk.END, f'{client["name"].ljust(max_name_len)}{client["role"].value.capitalize()}')
        
        # Display werewolves
        self.clients_lb.insert(tk.END, f'{" WEREWOLVES ":^25}\n')
        for client in werewolves:
            self.clients_lb.insert(tk.END, f'{client["name"].ljust(max_name_len)}{client["role"].value.capitalize()}')

        # Disable selectability of clients display
        self.clients_lb.config(state=tk.DISABLED)