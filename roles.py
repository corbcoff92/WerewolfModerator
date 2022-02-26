from enum import Enum, auto

class Roles(Enum):
    VILLAGER = 'VILLAGER'
    WEREWOLF = 'WEREWOLF'
    DOCTOR = 'DOCTOR'
    SEER = 'SEER'
    
    def __str__(self):
        return self.value