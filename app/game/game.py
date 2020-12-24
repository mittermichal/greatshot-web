from enum import Enum


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

    def init_regions_dict(self):
        self.regions_dict = {region.value: region.name for region in self.regions}

    def is_headshot(self, region: int) -> bool:
        return self.regions.HEAD.value == region

    @staticmethod
    def by_mod(mod):
        switcher = {
            'etpro': Etpro,
            'osp': Osp
        }
        return switcher.get(mod, Game)


class Etpro(Game):
    def __init__(self):
        super().__init__()
        self.regions = EtproRegions
        self.init_regions_dict()


class Osp(Game):
    def __init__(self):
        super().__init__()
        self.regions = OspRegions
        self.init_regions_dict()
