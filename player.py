from enum import Enum, auto

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
