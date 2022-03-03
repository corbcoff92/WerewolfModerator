import threading
import time
from shared import HOST, PORT, Roles, WerewolfModeratorClientDisplay
import socket
import tkinter as tk
from tkinter.messagebox import askyesno, showerror, showinfo


class Player:
    """ 
    Partial representation of a player for a game of werewolf. 

    This representation contains only the basic elements of a player for a game of werewolf,
    and does not include a socket connection to the main werewolf moderator server.
    """
    def __init__(self, name: str=None, role: Roles=None) -> None:
        """
        Creates an instance of a Player for a game of werewolf.
        
        Optional Arguments:
            name: str, default=None
                Name to which this instance should be initialized.
            role: Roles, default=None
                Role to which this instance should be initialized.
        """
        self.name = name
        self.role = role


class Client(socket.socket, Player):
    """ 
    Representation of a client and player for a game of werewolf.

    This representation is a complete representation of a player for the werewolf moderator,
    including a socket connection to the main werewolf moderator server. It also includes a
    Graphical User Interface (GUI) that facilitates user interaction.

    Extends:
        socket.socket
        Player
    """
    def __init__(self):
        """
        Creates an instance of a client for a game of werewolf.

        This instance is a complete representation of a player for the werewolf moderator,
        as it is a socket which connects to the main werewolf moderator server. It also 
        includes a Graphical User Interface (GUI) that facilitates user interaction.
        """
        Player.__init__(self)
        self.selected_player = None

        self.window = tk.Tk()
        self.window.title('Werewolf')
        self.window.resizable(False, False)
        self.window.geometry('300x300')
        
        self.join_frame = WerewolfModeratorClientJoinFrame(self)
        self.join_frame.pack(side=tk.TOP)

        self.role_lbl = tk.Label(master=self.window, text='Enter your name and click to join the server...')
        self.role_lbl.pack(side=tk.TOP)

        self.main_frame = WerewolfModeratorMainFrame(self.window)
        self.player_select_frame = WerewolfModeratorPlayerSelectionFrame(self)
        self.eliminated_frame = WerewolfModeratorEliminationFrame(self.window)
        self.gameover_frame = WerewolfGameOverClientDisplay(self)
        self.frame_windows = [self.main_frame, self.player_select_frame, self.eliminated_frame, self.gameover_frame]

        self.display_frame(self.main_frame)

    def display_frame(self, frame_to_display: tk.Frame) -> None:
        """
        Displays the given frame to the client's current Tk root window instance.

        The given frame is packed and expanded into the current Tk root window. Any frames 
        currently displayed are unpacked.

        Arguments:
            frame_to_display: tk.Frame
                Frame that is to be displayed to the screen.
        """
        for frame in self.frame_windows:
            if frame != frame_to_display:
                frame.pack_forget()
            else:
                frame.pack(fill=tk.BOTH, padx=(10,10), pady=(0,10), expand=True)
    
    def connect_to_server(self, name: str) -> None:
        """
        Initializes an attempt to connect to the main werewolf moderator server using the given name.

        If the connection attempt is succesful, a "permanent" connection to the server is 
        established in a new thread. Otherwise, a message is shown indicating that the 
        connection attempt was unsucceseful, and the reason why.

        Arguments:
            name: str
                The name that should be used to initialize the attempt to connect to the werewolf moderator
                main server.
        """
        self.name = name
        try:
            socket.socket.__init__(self, socket.AF_INET, socket.SOCK_STREAM)
            self.connect((HOST, PORT))
            self.send(self.name.encode())
        except Exception as e:
            showerror(title='Unable to Connect to Server', message='Unable to connect to the server, please try again later...')
        else:
            accepted, msg = self.recv(4096).decode().strip().split('|')
            if accepted == 'True':
                self.join_frame.connected()
                self.role_lbl['text'] = 'Welcome to Werewolf'
                self.main_frame.main_message_lbl['text'] = msg
                send_receive_thread = threading.Thread(target=self.receive_from_server)
                send_receive_thread.daemon = True
                send_receive_thread.start()
            else:
                self.main_frame.main_message_lbl['text'] = msg

    def parse_players(self, players_encoded: str) -> list[Player]:
        """
        Parses the given encoded string obtained from the server that contains a list of players and their
        respective roles.

        Arguments:
            players_encoded: str
                Encoded string that contains a list of players and their respective roles 
        """
        players_encoded_list = players_encoded.split(',')
        players = []
        for player in players_encoded_list:
            name, role = player.split(':')
            role = Roles(role)
            players.append(Player(name, role))
        return players

    def receive_from_server(self) -> None:
        """
        Indefinite loop that allows the client to recieve & process data acquired from the werewolf 
        moderator main server.

        This loop is terminated by the server, which results in a message being displayed to the user
        indicating as such.
        """
        while True:
            from_server = self.recv(4096).decode().strip()

            if not from_server:
                break
            
            action, rem = from_server.split('|')            
            if action == 'ROLE':
                role = rem
                self.role = Roles(role)
                self.main_frame.main_message_lbl['text'] = f'The game is beginning...\nNo action required until day or night begin...'
                self.role_lbl['text'] = f'Role: {self.role}'
                self.display_frame(self.main_frame)
            elif action == 'NIGHT':
                self.selected_player = None
                players_encoded = rem
                players = self.parse_players(players_encoded)
                self.night(players)
            elif action == 'DAY':
                self.selected_player = None
                players_encoded = rem
                players = self.parse_players(players_encoded)
                self.day(players)
            elif action == 'ELIMINATED':
                self.role_lbl['text'] = 'ELIMINATED'
                self.display_frame(self.eliminated_frame)
            elif action == 'NOT_ELIMINATED':
                msg = rem
                self.main_frame.main_message_lbl['text'] = f'{msg}\nNo other action required until day or night...'
            elif action == 'DONE':
                werewolves_won_encoded = rem
                werewolves_won = (werewolves_won_encoded == 'True')
                self.role_lbl['text'] = 'Game Over'
                self.main_frame.main_message_lbl['text'] = f'{"Werewolves" if werewolves_won else "Villagers"} have won!'
                self.gameover_frame.display(self.role, werewolves_won)
                self.display_frame(self.gameover_frame)
        showerror(title='Server Disconnected', message='Disconnected from server')
        self.exit()

    def wait_select_player(self):
        """ Waits until a response has been received from each of the currently connected clients. """
        while not self.selected_player:
            time.sleep(1)

    def night(self, players: list[Player]) -> None:
        """
        Implementation of the night phase for a client during a game of werewolf.

        The user must select a player from the given list of currently connected clients,
        which will perform an action corresponding with thier assigned role. The selection 
        is sent through this client's socket connection.

         Arguments:
            players: list[Player]
                List of players indicating the clients currently connected to the werewolf moderator main server
                from which the selected player should be chosen.
        """
        self.player_select_frame.message_lbl['text'] = f'Night'
        if self.role == Roles.VILLAGER:
            self.player_select_frame.selection_lbl['text'] = 'Select a random person...'
            excluded_players = []
        elif self.role == Roles.WEREWOLF:
            werewolves = [player.name for player in players if player.role == Roles.WEREWOLF]
            excluded_players=werewolves
            self.player_select_frame.message_lbl['text'] += f'\nOther werewolves: {", ".join([werewolf for werewolf in werewolves if werewolf != self.name]) if len(werewolves) > 1 else "None"}'
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
        self.main_frame.main_message_lbl['text'] = f'Waiting for other players to respond...'
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
            
    def day(self, players: list[Player]) -> None:
        """
        Implementation of the day phase for a game of werewolf.

        The user must vote for another from the given list of players that they would like to jail. 
        If any player receives a majority of the votes, they are immediately jailed and eliminated. 
        The selection is sent through this client's socket connection.

        Arguments:
            players: list[Player]
                List of players indicating the clients currently connected to the werewolf moderator main server
                from which the selected player should be chosen.
        """
        self.player_select_frame.message_lbl['text'] = f'Day'
        self.player_select_frame.selection_lbl['text'] = 'Please select a person for trial...'
        self.player_select_frame.update([player.name for player in players], [self.name])
        
        self.display_frame(self.player_select_frame)
        self.wait_select_player()
        self.main_frame.main_message_lbl['text'] = f'Waiting for other players to respond...'
        self.display_frame(self.main_frame)
        
        try:
            self.send(self.selected_player.encode())
        except Exception as e:
            showerror(title='Reponse Not Sent', message=str(e))

    def on_close(self) -> None:
        """
        Prompts the user for confirmation before exiting the application. A message is displayed 
        indicating that the client will be disconnected from the main werewolf moderator server.
        """
        if askyesno(title='Exit?', message='Are you sure you want to exit? You will be disconnected from the server...'):
            self.exit()

    def play_again(self) -> None:
        """
        Resets the client allowing the user to remain connected to the main werewolf moderator server 
        and play another game of werewolf.
        """
        self.main_frame.main_message_lbl['text'] = 'Please wait for the next game to begin...'
        self.display_frame(self.main_frame)
    
    def exit(self):
        """ 
        Closes the application. 
        
        Terminates this client's socket connection to the main werewolf moderator server and also the Graphical 
        User Interface (GUI) by destroying the main root tkinter.Tk window. 
        """
        self.shutdown(socket.SHUT_WR)
        self.window.destroy()


class WerewolfModeratorClientJoinFrame(tk.Frame):
    """ 
    Tkinter frame containing elements allowing a client to join the server for a game of werewolf. 
    
    Extends:
        tkinter.Frame
    """
    def __init__(self, client: Client) -> None:
        """
        Creates an instance of a WerewolfModeratorClientJoinFrame.

        This frame contains a text entry allowing the user to enter thier name for the game of werewolf. 
        It also contains a join button allowing the user to initiate an attempt to connect to the server.
        
        Arguments:
            client: Client
                Instance of client that this frame will control.
        """
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
    
    def connect_to_server(self) -> None:
        """
        Initiates an attempt to connect to the werewolf moderator main server.

        The users name is retrieved from the text entry, including validation 
        (must be between 1 and 15 characters long).
        """
        name = self.name_ent.get().strip()
        if 1 <= len(name) <= 15:
            self.client.connect_to_server(name)
        else:
            showerror(title='Invalid Name', message='Name must be between 1 and 15 characters long, try again...')
    
    def connected(self) -> None:
        """
        Implementation of this frame's client being succesfully connected to the werewolf moderator main server.

        Name entry & join button are disabled, enter key is unbound from connecting to server, and the client's root
        window protocol is adjusted to require confirmation before closing. 
        """
        self.name_ent.config(state=tk.DISABLED)
        self.connect_btn.config(state=tk.DISABLED)
        self.name_ent.unbind('<Return>')
        self.client.window.protocol('WM_DELETE_WINDOW', self.client.on_close)        


class WerewolfModeratorMainFrame(tk.Frame):
    """ 
    Tkinter frame containing the main message label used for displaying the important 
    information of a game of werewolf to the user.  
    
    Extends:
        tkinter.Frame
    """
    def __init__(self, window: tk.Tk) -> None:
        """
        Creates an instance of a WerewolfModeratorMainFrame.

        This frame contains the main message label used for displaying the important 
        information of a game of werewolf to the user.
        
        Arguments:
            window: tkinter.Tk
                Root tkinter.Tk window instance to which this frame should be added.
        """
        super().__init__(master=window)
        self.main_message_lbl = tk.Label(master=self, text='')
        self.main_message_lbl.pack(side=tk.TOP)


class WerewolfGameOverClientDisplay(tk.Frame):
    """ 
    Tkinter frame containing the elements used for displaying the results of a game of werewolf to the user.

    This frame also contains buttons allowing the user to remain connected to the server to play another 
    game of werewolf, or to exit and disconnect from the main werewolf moderator server.  
    
    Extends:
        tkinter.Frame
    """
    def __init__(self, client: Client) -> None:
        """
        Creates an instance of a WerewolfGameOverClientDisplay.

        This frame contains the elements used for displaying the results of a game of werewolf to the user, 
        as well as buttons allowing the user to remain connected to the server to play another game of 
        werewolf, or to exit and disconnect from the main werewolf moderator server.  
        
        Arguments:
            client: Client
                Instance of client that this frame will control.
        """
        super().__init__(master=client.window)
        self.werewolf_moderator = client

        self.role_lbl = tk.Label(master=self, text='')
        self.role_lbl.pack(side=tk.TOP)
        self.winning_lbl = tk.Label(master=self, text='')
        self.winning_lbl.pack(side=tk.TOP)
        
        self.btn_frame = tk.Frame(master=self)
        self.server_btn = tk.Button(master=self.btn_frame, text='Play Again', width=10,  command=client.play_again)
        self.server_btn.pack(side=tk.LEFT, padx=(0,5))
        self.exit_btn = tk.Button(master=self.btn_frame, text='Exit', width=10, command=client.exit)
        self.exit_btn.pack(side=tk.LEFT, padx=(5,0))
        self.btn_frame.pack(side=tk.BOTTOM, pady=(10,0))
         
    def display(self, role: Roles, werewolves_won: bool) -> None:
        """
        Updates the game over display frame to reflect the given results.

        Arguments:
            role: Roles
                This frame's client's respective role during the game of werewolf.
            werewolves_won: bool
                Indication of whether or not the werewolves won the game of werewolf.
                Should be True if the werewolves won the game of werewolf, False otherwise. 
        """
        self.role_lbl['text'] = f'You were a {role}{", and thus a Villager. " if role != Roles.WEREWOLF and role != Roles.VILLAGER else ". "}'
        if (werewolves_won and role == Roles.WEREWOLF) or (not werewolves_won and role != Roles.WEREWOLF):
            self.winning_lbl['text'] = 'You have won!'
        else:
            self.winning_lbl['text'] = 'You have lost!'


class WerewolfModeratorEliminationFrame(tk.Frame):
    """ 
    Tkinter frame containing the labels indicating that the client has been eliminated
    from the game of werewolf.
    
    Extends:
        tkinter.Frame
    """
    def __init__(self, window: tk.Tk) -> None:
        """
        Creates an instance of a WerewolfModeratorEliminationFrame.

        This frame contains the elements labels indicating that the client has been eliminated
        from the game of werewolf.  
        
        Arguments:
            window: tkinter.Tk
                Root tkinter.Tk window instance to which this frame should be added.
        """
        super().__init__(master=window)

        tk.Label(master=self, text= f'You have been eliminated').pack()
        tk.Label(master=self, text='Please do not disclose your role...').pack(side=tk.TOP)
        tk.Label(master=self, text='All roles will be displayed when the game is over...').pack(side=tk.TOP)


class WerewolfModeratorSelectableClientDisplay(WerewolfModeratorClientDisplay):
    """ 
    Tkinter frame containing a selectable listbox for displaying clients.
    
    Extends:
            tkinter.Frame
    """
    def __init__(self, frame: tk.Frame, client: Client) -> None:
        """
        Creates an instance of a WerewolfModeratorSelectableClientDisplay.

        The clients are displayed in a selectable listbox. Includes validation 
        ensuring that the user selects one and only one client. 
        
        Arguments:
            frame: tkinter.Frame
                Frame to which this client display should be added.
        """
        super().__init__(frame)
        self.client = client

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
        super().update(client_names=client_names, excluded_clients=excluded_clients)
        self.clients_lb.config(state=tk.NORMAL)
        
    def select_client(self) -> None:
        """
        Implementation of the user selecting a client from the selectable clients display list.

        Includes validation ensuring that the user selects one and only one client.
        """
        selection = self.clients_lb.curselection()
        if selection:
            idx = selection[0]
            self.client.selected_player = self.client_names[idx]
        else:
            showerror(title='No Selection', message='You must select an item...')


class WerewolfModeratorPlayerSelectionFrame(tk.Frame):
    """ 
    Tkinter frame containing the elements allowing the user to select a player during a game of werewolf.
    
    This includes message labels for displaying instructions, as well as a selectable listbox containing
    the player's available options.

    Extends:
        tkinter.Frame
    """
    def __init__(self, client: Client) -> None:
        """
        Creates an instance of a WerewolfModeratorPlayerSelectionFrame.

        This frame contains the elements allowing the user to select a player during a game of werewolf,
        including message labels for displaying instructions, as well as a selectable listbox containing
        the player's available options. The listbox includes validation ensuring that one and only one 
        option has been selected.  
        
        Arguments:
            client: Client
                Instance of client that this frame will control.
        """
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
    
    def update(self, client_names: list[str], excluded_clients: list[str]=[]) -> None:
        """
        Updates the selectable clients display frame to reflect all of the clients in the given list of clients that
        are not contained in the optional excluded clients list.

        Aruments:
            client_names: list[str]
                Names of the clients that should be displayed and allowed for selection.
        Optional:
            excluded_clients: list[str], Default=[]
                Names of the clients that should not be displayed and allowed for selection.
        """
        self.client_display.update(client_names, excluded_clients=excluded_clients)    


if __name__ == "__main__":
    client = Client()
    client.window.mainloop()