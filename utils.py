from random import randint

def shuffle_list(l):
    num_items = len(l)
    for _ in range(5):
        for item in l:
            idx = randint(0, num_items - 1)
            l.append(l.pop(idx))