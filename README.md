# Overview
This network application serves as a moderator for the popular "social/party" activity, werewolf. In werewolf, individuals are assigned roles that must remain secret. During the different phases of werewolf, each person must also secretely select other indivduals to perform actions corresponding to their secret role. Secrecy is traditionally accomplished by delegating an individual to be the moderator. However, this means that the group will have one less participant, as the moderator does not get the opportunity to participate. 

This program automates the process, allowing each member of the group the opportunity to participate. It also helps to alleviate the accusations of cheating, as each member of the group inputs their choices on their own computer.

The main program is executed on a shared computer, which acts as both a server and also a common display among all participants. Individual clients then connect to the server from unique computers, allowing their inputs to be received and processed anonymously.

Both the client and server applications utilize Python's built-in `tkinter` library to implement a Graphical User Interface (GUI) which better facilitates user interaction.

A demonstration of the app is provided here: [Werewolf Moderator App Demonstration Video](https://youtu.be/V_FojDt12Ds)

# Network Communication
This software utilizes TCP sockets organized in a  client-server network connection model. Individual computers (clients) are connected to the main werewolf moderator program (server). This server receives data from the clients, and distributes the resutls and other data as necessary. The main server also acts as a common display among all participants. TCP sockets provide the neccessary insurance that each clients response is precisely and entirely received. Port number '55555' was arbitrarily chosen to ensure that no reserved ports are disturbed.  

A custom format is used to send data between client and server. The format is comprised of an action and content separted by the pipe character (`|`). The content usually consists of either a message, or a list of the active werewolf participants and thier respective roles, encoded in a comma separated list with the names and roles separated by a colon. This shared format allows the client to factilitate the participants actions, and the server to determine and display the results.

# Development Environment
* Python 3.10.1 
    - `socket` & `socketserver` libraries
    - `tkinter` library (GUI)
* Visual Studio Code | Version 1.64.2

# Useful Websites
* [Python Socket Libraries](https://docs.python.org/3.6/library/socket.html) (official site)
* [Python Server Libraries](https://docs.python.org/3.6/library/socketserver.html) (official site)
* [Socket Programming HOWTO — Python 3.10.2 documentation](https://docs.python.org/3/howto/sockets.html#sockets) (official tutorial site)
* [Build a Multi-User Group Chat Application - Level Up Coding](https://levelup.gitconnected.com/learn-python-by-building-a-multi-user-group-chat-gui-application-af3fa1017689) (tutorial site)
* [Multi-Users Online Network Game in Python - Level Up Coding](https://levelup.gitconnected.com/program-your-first-multiple-user-network-game-in-python-9f4cc3650de2) (tutorial site)

# Future Work
* Improved handling of unanticipated socket disconnections 
    - Possibly allowing client to immediately rejoin server
* Porting of client application to mobile devices 
    - Possible development of mobile app or web browser application