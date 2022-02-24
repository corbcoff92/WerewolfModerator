from enum import Enum, auto

class InvalidPlayerRole(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = message
    
    def __str__(self):
        return f'InvalidPlayerRole: Role must be of type Roles.'

class Roles(Enum):
    VILLAGER = auto()
    WEREWOLF = auto()
    DOCTOR = auto
    SEER = auto()
    
    def __str__(self):
        return self.name.capitalize()

class Player:
    def __init__(self, name, role):
        self.name = name
        self.role = role
    
    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, role):
        if isinstance(role, Roles):
            self._role = role
        else:
            raise Exception