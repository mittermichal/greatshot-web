from enum import Enum
from app import Libtech3


class Regions(Enum):
    HEAD = None
    BODY = None
    SHIELD = None
    TEAMMATE = None
    UNKNOWN = None


class OspRegions(Enum):
    HEAD = 2
    BODY = 1
    UNKNOWN = 0


class EtproRegions(Enum):
    HEAD = 130
    BODY = 131
    SHIELD = 0
    TEAMMATE = 132


class Game:
    def __init__(self):
        self.regions = None
        self.regions_dict = None
        self.weapons = None

    def is_headshot(self, region: int) -> bool:
        return self.regions.HEAD.value == region

    @staticmethod
    def by_mod(mod):
        mod = mod.split(' ')[0]
        switcher = {
            'etpro': Etpro,
            'osp': Osp,
            'RtcwPro': Osp
        }
        return switcher.get(mod, Etpro)


class Etpro(Game):
    def __init__(self):
        super().__init__()
        self.regions = EtproRegions
        self.weapons = Libtech3.Weapon


class Osp(Game):
    def __init__(self):
        super().__init__()
        self.regions = OspRegions
        self.weapons = Libtech3.RtcwWeapon
