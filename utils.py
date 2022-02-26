from random import randint
from enum import Enum

class Roles(Enum):
    VILLAGER = 'VILLAGER'
    WEREWOLF = 'WEREWOLF'
    DOCTOR = 'DOCTOR'
    SEER = 'SEER'
    
    def __str__(self):
        return self.value

def shuffle_list(l):
    num_items = len(l)
    for _ in range(5):
        for item in l:
            idx = randint(0, num_items - 1)
            l.append(l.pop(idx))