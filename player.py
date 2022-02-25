from enum import Enum, auto

class InvalidPlayerRole(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = message
    
    def __str__(self):
        return f'InvalidPlayerRole: {self.message}'

class Roles(Enum):
    VILLAGER = auto()
    WEREWOLF = auto()
    DOCTOR = auto
    SEER = auto()
    
    def __str__(self):
        return self.name.capitalize()

class Player:
    def __init__(self, name):
        self.name = name
        self.role = Roles.VILLAGER
    
    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, role):
        if isinstance(role, Roles):
            self._role = role
        else:
            raise InvalidPlayerRole('Role must be of type Roles.')