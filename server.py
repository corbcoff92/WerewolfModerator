import socket
import time
from shared import HOST, PORT, Roles, WerewolfModeratorClientDisplay, WerewolfModeratorClientRolesDisplay, shuffle_list
import threading
import socketserver
import tkinter as tk
from tkinter.messagebox import askyesno, showerror, showinfo


ROLES_TO_ASSIGN = [Roles.WEREWOLF, Roles.DOCTOR, Roles.SEER]            


class WerewolfModeratorRequestHandler(socketserver.BaseRequestHandler):
    """ Defines the method that will be used to handle new socket connection requests to the WerewolfModerator server. """
    def handle(self) -> None:
        """
        Defines the handling procedure of new socket connection requests to the WerewolfModerator server.

        This procedure includes accepting requests if the game has not yet begun, and continuing to listen for additional 
        socket data recieved from the client. The socket is closed when the connection is closed by the client.
        Any new socket connection request recieved while a game of werewolf is already in progress is rejected with a 
        message indicating as such.
        """
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
    """
    Class containing the implementation of a moderator for the classic social/party game, Werewolf.

    This implementation contains a graphical user interface (GUI). It is also a server, allowing clients to play using their own
    individual devices. 
    """
    daemon_threads = True
    def __init__(self) -> None:
        """
        Initializes a new instance of the WerewolfModerator.

        This instance contains a graphical user interface (GUI) and also acts as a server, allowing clients to play using their own
        individual devices. The server automatically begins listening for new socket connections from clients, using the IP adress
        and port contained in the shared file.
        """
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

    def display_frame_window(self, frame_to_display: tk.Frame) -> None:
        """
        Displays the given frame to the WerewolfModerators current Tk root window instance.

        The given frame is packed and expanded into the current Tk root window. Any frames 
        currently displayed are unpacked.

        Arguments:
            frame_to_display: tk.Frame
                Frame that is to be displayed to the screen.
        """
        for frame in self.frames:
            if frame_to_display == frame:
                frame.pack(fill=tk.BOTH, padx=(10,10), pady=(10,10), expand=True)
            else:
                frame.pack_forget()

    def start_server(self) -> None:
        """
        Initializes the listening process for this server insance.

        This process continues indefinitely until it is eplicitly stopped. 
        This process is executed in a new thread.
        """
        super().__init__((HOST, PORT), WerewolfModeratorRequestHandler)
        server_thread = threading.Thread(target=self.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    def accept_clients(self) -> None:
        """
        Allows new socket client connections to be accepted before the game of werewolf is begun.

        This method makes use of the AcceptClientsFrame, which shows the currently connected clients
        as well as a button allowing the game to begin. This button only becomes enabled when the 
        required number of clients are connected.
        """
        self.adding_players = True
        self.accept_clients_frame.update([client['name'] for client in self.clients])
        self.display_frame_window(self.accept_clients_frame)

    def add_client(self, client: dict) -> None:
        """
        Adds the given newly connected client to the currently connected clients list.

        Adds a newly connected client to the currently connected clients list.
        The displayed client list is also updated to reflect modified connected 
        clients list containing the newly connected client.

        Arguments:
            client: dict
                Dictionary containing the information of the newly connected client.
                This information includes a name, socket, and werewolf role.
        """
        self.clients.append(client)
        self.accept_clients_frame.update([client['name'] for client in self.clients])
    
    def remove_client(self, client: dict) -> None:
        """
        Removes the given client from the currently connected clients list.

        Removes a connected client from the currently connected clients list.
        The displayed client list is also updated to reflect modified connected 
        clients list deleting the newly disconnected client. If a game of werewolf
        is in progress, the client is also removed from the list of active players. 

        Arguments:
            client: dict
                Dictionary containing the information of the disconnected client.
                This information includes a name, socket, and werewolf role.
        """
        removed_client = next((current_client for current_client in self.clients if current_client['name'] == client['name']))
        self.clients.remove(removed_client)

        if not self.exiting:
            if self.adding_players or self.done:
                self.accept_clients_frame.update([client['name'] for client in self.clients])
            else:
                self.remove_active_player(removed_client['name'])
    
    def remove_active_player(self, player_name: str):
        """
        Attempts to remove the client with the given name from the list of currently active players.

        Attempts to remove the client with the given name from the list of currently active players.
        If this is unsucessful, it is most likely the result of the client being disconnected from
        the server.

        Arguments:
            player_name: str
                Name of the player that is to be removed from the currently active players list.
        """
        try:
            removed_player = next((player for player in self.active_players if player['name'] == player_name))
            removed_player['socket'].send(f'ELIMINATED|'.encode())
            self.active_players = [player for player in self.active_players if player != removed_player]
        except Exception as e:
            showerror(title='Player disconnected', message=f'{player_name} has been disconnected from the server...')
    
    def begin(self) -> None:
        """
        Begins a game of werewolf for the currently connected clients.
        
        Begins a game of werewolf for the currently connected clients. 
        Roles are randomly assigned to each player. The main menu is 
        automatically displayed.
        """
        self.done = False
        self.adding_players = False
        self.active_players = list(self.clients)
        self.display_frame_window(self.main_menu)
        self.assign_roles()

    def assign_roles(self) -> None:
        """
        Randomly assigns a werewolf role to each currently connected client. 
        
        Randomly assigns a werewolf role to each currently connected client. 
        The roles assigned are dynamically depending on the number of currently 
        connected clients. The list of clients are also shuffled to help facilitate
        secretization.
        """
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

    def broadcast(self, clients: list[dict], msg: str) -> None:
        """
        Sends the given message to each of the clients in the given list.

        Sends the given message to each of the clients in the given list.
        The message is sent using each clients respective socket.
        """
        for client in clients:
            client['socket'].send(msg.encode())

    def wait_for_responses(self) -> None:
        """ Waits until a response has been received from each of the currently connected clients. """
        while len(self.responses) < len(self.active_players):
            time.sleep(1)
            self.waiting_frame.update()

    def night(self) -> None:
        """
        Implementation of the night phase for a game of werewolf.

        Implementation of the night phase for a game of werewolf. Each of the currently 
        connected clients selects a player  corresponding with thier assigned role. 
        Their selection is aquired through thier respective socket connection.
        """
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

    def day(self) -> None:
        """
        Implementation of the day phase for a game of werewolf.

        Implementation of the day phase for a game of werewolf. Each currently connected client
        votes for another player that they would like to jail. If any player receives a majority
        of the votes, he is immediately jailed and eliminated.
        """
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
            
    def check_game_over(self) -> None:
        """
        Checks whether or not the game of werewolf should be ended.

        Checks whether or not the game of werewolf should be ended. The two ending contitions are
        that the number of remaining werewolves equals the number of remaining villagers, or that
        all of the werewolves have been eliminated.
        """
        num_werewolves = len([player for player in self.active_players if player['role'] == Roles.WEREWOLF])
        num_villagers = len([player for player in self.active_players if player['role'] != Roles.WEREWOLF])
        if num_villagers <= num_werewolves:
            self.game_over(True)
        elif num_werewolves <= 0:
            self.game_over(False)
    
    def game_over(self, werewolves_won: bool) -> None:
        """
        Implementation of the game of werewolf ending.

        Implementation of the game of werewolf ending. The results are displayed and
        a message is sent to each of the currently connected clients indicating as
        such.

        Arguments:
            werewolves_won: bool
                Indication of whether or not the werewolves won.
                Should be True if the werewolves won, False otherwise.
        """
        self.done = True
        self.broadcast(self.clients, f'DONE|{werewolves_won}')
        
        self.game_over_frame.update(self.clients, werewolves_won)
        self.display_frame_window(self.game_over_frame)
        
        if werewolves_won:
            showinfo(title='Game Over', message='The werewolves have won!')
        else:
            showinfo(title='Game Over', message='The villagers have won!')
    
    def ask_close(self) -> None:
        """
        Prompts the user to choose whether or not they would actually like to close the application.

        Prompts the user to choose whether or not they would actually like to close the application.
        A message is displayed indicating that all of the currently connected clients will be disconnected
        from the server.
        """
        if askyesno(title='Exit?', message='Are you sure you want to exit? All clients will be disconnected...'):
            self.exit()

    def exit(self) -> None:
        """
        Implementation of the Werewolf Moderator application being exited.

        Implementation of the Werewolf Moderator application being exited. All individual currently connected 
        client socket connections are shutdown, and the root Tk GUI window is destroyed.
        """
        self.exiting = True
        for client in self.clients:
            client['socket'].shutdown(socket.SHUT_WR)
        self.window.destroy()


class AcceptClientsFrame(tk.Frame):
    """ 
    Tkinter frame containing elements for accepting new clients and beginning a game of werewolf. 
    
    Extends:
        tkinter.Frame
    Methods:
        update
    """
    def __init__(self, server: socketserver.TCPServer, num_clients_required_to_begin: int) -> None:
        """
        Creates an instance of an AcceptClientsFrame.

        This frame contains elements for accepting new clients and beginning a game of werewolf.
        
        Arguments:
            server:socketserver.BaseServer
                The server that this frame will control.
            num_clients_required_to_begin:int
                The number of clients that must be connected before the game of werewolf can begin
        """
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
    
    def update(self, clients: list[str]) -> None:
        """
        Updates the currently connected clients display to reflect the given list of clients.

        Updates the currently connected clients display to reflect the given list of clients.
        Also enables/disables the begin button depending on whether or not the list contains
        the number of clients required to begin a game of werewolf

        Arguments:
            clients: list[str]
                List conataining client names to be displayed.
        """
        self.connected_clients_display.update(clients)
        if len(clients) >= self.num_clients_required_to_begin:
            self.begin_game_btn.config(state=tk.NORMAL)
        else:
            self.begin_game_btn.config(state=tk.DISABLED)


class WerewolfModeratorMainMenu(tk.Frame):
    """ 
    Tkinter frame containing elements for navigating between the main phases of a game of werewolf. 

    Extends:
            tkinter.Frame
    """
    def __init__(self, werewolf_moderator: WerewolfModerator) -> None:
        """
        Creates an instance of a WerewolfModeratorMainMenu.

        This frame contains elements for navigating between the main phases of a game of werewolf.
        
        Arguments:
            werewolf_moderator: WerewolfModerator
                Instance of WerewolfModerator that this frame will control.
        """
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
    
    def night(self) -> None:
        """
        Begins the night phase for this frame's werewolf moderator instance.

        Begins the night phase for this frame's werewolf moderator instance. The WerewolfModerator's night 
        function is executed in a new thread.
        """
        night_thread = threading.Thread(target=self.werewolf_moderator.night)
        night_thread.daemon = True
        night_thread.start()

    def day(self) -> None:
        """
        Begins the day phase for this frame's werewolf moderator instance.

        Begins the day phase for this frame's werewolf moderator instance. The WerewolfModerator's day 
        function is executed in a new thread.
        """
        day_thread = threading.Thread(target=self.werewolf_moderator.day)
        day_thread.daemon = True
        day_thread.start()


class WerewolfModeratorWaitingFrame(tk.Frame):
    """ 
    Tkinter frame containing elements for displaying a message while game of werewolf is waiting for all client responses. 
    
    Extends:
            tkinter.Frame
    """
    def __init__(self, werewolf_moderator: WerewolfModerator) -> None:
        """
        Creates an instance of a WerewolfModeratorWaitingFrame.

        This frame contains elements for displaying a message while game of werewolf is waiting for all client responses.
        This frame displays a list containing the names of this instances' clients who have not yet returned a response.
        
        Arguments:
            werewolf_moderator: WerewolfModerator
                Instance of WerewolfModerator that this frame will control.
        """
        super().__init__(master=werewolf_moderator.window)
        self.werewolf_moderator = werewolf_moderator

        self.main_lbl = tk.Label(master=self, text='Waiting')
        self.main_lbl.pack(side=tk.TOP)
        self.message_lbl = tk.Label(master=self, text='Waiting for responses from: ')
        self.message_lbl.pack(side=tk.TOP)

        self.waiting_clients_display = WerewolfModeratorClientDisplay(self)
        self.waiting_clients_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def update(self) -> None:
        """
        Updates the waiting clients display to reflect the clients that have not yet returned a response.
        """
        self.waiting_clients_display.update([client['name'] for client in self.werewolf_moderator.active_players if client not in self.werewolf_moderator.clients_responded])


class WerewolfModeratorGameOverFrame(tk.Frame):
    """ 
    Tkinter frame containing elements for displaying the game over information for a game of werewolf. 

    Extends:
            tkinter.Frame
    """
    def __init__(self, werewolf_moderator: WerewolfModerator) -> None:
        """
        Creates an instance of a WerewolfModeratorGameOverFrame.

        This frame contains elements for displaying the game over information for a game of werewolf. 
        This includes a message indicating who won, and also displays a list of the participating clients
        and their respective roles.
        
        Arguments:
            werewolf_moderator: WerewolfModerator
                Instance of WerewolfModerator that this frame will control.
        """
        super().__init__(master=werewolf_moderator.window)

        self.main_lbl = tk.Label(master=self, text='Game Over')
        self.main_lbl.pack(side=tk.TOP)
        self.message_lbl = tk.Label(master=self, text='')
        self.message_lbl.pack(side=tk.TOP)

        self.client_display = WerewolfModeratorClientRolesDisplay(self)
        self.client_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.btn_frame = tk.Frame(master=self)
        self.server_btn = tk.Button(master=self.btn_frame, text='Main Menu', width=10,  command=werewolf_moderator.accept_clients)
        self.server_btn.pack(side=tk.LEFT, padx=(0,5))
        self.exit_btn = tk.Button(master=self.btn_frame, text='Exit', width=10, command=werewolf_moderator.exit)
        self.exit_btn.pack(side=tk.LEFT, padx=(5,0))
        self.btn_frame.pack(side=tk.BOTTOM, pady=(10,0))
        
    def update(self, clients: list[dict], werewolves_won: bool) -> None:
        """
        Updates the game over display to reflect the given results of the game of werewolf. 
        
        Updates the game over display to reflect the results of the game of werewolf. This includes updating
        the client list display to include all of the participants and thier respective roles.

        Arguments:
            clients: list[dict]
                List of dictionaries containing the game of werewolf's participants and their respective roles.
            werewolves_won: bool
                Inidication of whether or not the werewolves won the game of werewolf.
                Should be True if the werewolves won, False otherwise.
        """
        self.message_lbl['text'] = f'{"Werewolves" if werewolves_won else "Villagers"} have won!'
        self.client_display.update(clients)


if __name__ == '__main__':
    server = WerewolfModerator()
    server.window.mainloop()
    server.shutdown()