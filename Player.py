import time
import pymem
import math

pymem.logger.disabled = True
pymem.process.logger.disabled = True


class Player:
    def __init__(self, x, y, player_id, pymem_obj):
        self.x = x
        self.y = y
        self.validated = False
        self.player_id = player_id
        self.pymem_obj = pymem_obj
        self.name = None

    def get_coords(self):
        x = math.ceil(self.pymem_obj.read_float(self.x) * 10 ** 2) / 10 ** 2
        y = math.ceil(self.pymem_obj.read_float(self.y) * 10 ** 2) / 10 ** 2
        return x, y

    def validate(self, name):
        current_x = self.get_coords()[0]
        time.sleep(0.5)
        if self.get_coords()[0] > current_x + 0.5 or self.get_coords()[0] < current_x - 0.5:
            self.name = name
            self.validated = True
            print(f"{name} is player {self.player_id}")
            return True
        else:
            return False

    def reset_coordinates(self, addr, offset):
        self.x = addr + offset*self.player_id
        self.y = self.x + 0x4

    def distance(self, other_player):
        return math.dist(self.get_coords(), other_player.get_coords())

    def __repr__(self):
        return f"{self.name}: {self.player_id}"

