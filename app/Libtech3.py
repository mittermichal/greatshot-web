import subprocess
import sys
import os
from enum import Enum
from sqlalchemy import Column, Integer, String, ForeignKey, SmallInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def cut(bin_path, input_file, output_file, start, end, type, pov):
    subprocess.call(
        [bin_path, 'cut', input_file, output_file, str(start),
         str(end), str(type), str(pov)])
    # print(os.getcwd())
    if os.stat(output_file).st_size == 0:
        raise Exception("Cutted demo is empty, probably wrong start-end time interval")


class Demo(Base):
    __tablename__ = 'demo'
    dwSeq = Column(Integer, primary_key=True)
    szMd5 = Column(String(32), index=True)
    szName = Column(String(64))
    szMapName = Column(String(64))
    szPOVName = Column(String(64))
    szTeamA = Column(String(128))
    szTeamB = Column(String(128))


# TODO not all columns here


class Player(Base):
    __tablename__ = 'player'
    dwSeq = Column(Integer, primary_key=True)
    szMd5 = Column(String(32), index=True)
    szName = Column(String(128))
    szCleanName = Column(String(64))
    bClientNum = Column(SmallInteger)
    szInfoString = Column(String(128))
    bTeam = Column(SmallInteger)
    bTVClient = Column(SmallInteger)

    def team_name(self, session):
        demo = session.query(Demo).filter(Demo.szMd5 == self.szMd5)[0]
        if self.bTeam == 1:
            return demo.szTeamB
        elif self.bTeam == 2:
            return demo.szTeamA
        else:
            return 'SPECTATOR'


class Revive(Base):
    __tablename__ = 'revive'
    dwSeq = Column(Integer, primary_key=True)
    szMd5 = Column(String(32), index=True)
    bRevived = Column(SmallInteger)
    bReviver = Column(SmallInteger)
    dwTime = Column(Integer)


class Obituary(Base):
    __tablename__ = 'obituary'
    dwSeq = Column(Integer, primary_key=True)
    szMd5 = Column(String(32), index=True)
    bAttacker = Column(SmallInteger)
    bTarget = Column(SmallInteger)
    bWeapon = Column(SmallInteger)
    dwTime = Column(Integer)
    bIsTeamkill = Column(SmallInteger)
    szTimeString = Column(String(32))
    szMessage = Column(String(256))


class BulletEvent(Base):
    __tablename__ = 'bulletevent'
    dwSeq = Column(Integer, primary_key=True)
    szMd5 = Column(String(32), index=True)
    bRegion = Column(SmallInteger)
    bTarget = Column(SmallInteger)
    bAttacker = Column(SmallInteger)
    dwTime = Column(Integer)
    bWeapon = Column(SmallInteger)


class Weapon(Enum):
    # wolfet src bg_public.h
    # ^\s(\w+),\s*// (\d+)
    # \t\1 = \2
    WP_UNKNOWN = -1
    WP_NONE = 0
    WP_KNIFE = 1
    WP_LUGER = 2
    WP_MP40 = 3
    WP_GRENADE_LAUNCHER = 4
    WP_PANZERFAUST = 5
    WP_FLAMETHROWER = 6
    WP_COLT = 7
    WP_THOMPSON = 8
    WP_GRENADE_PINEAPPLE = 9
    WP_STEN = 10
    WP_MEDIC_SYRINGE = 11
    WP_AMMO = 12
    WP_ARTY = 13
    WP_SILENCER = 14
    WP_DYNAMITE = 15
    WP_SMOKETRAIL = 16
    WP_MAPMORTAR = 17
    VERYBIGEXPLOSION = 18
    WP_MEDKIT = 19
    WP_BINOCULARS = 20
    WP_PLIERS = 21
    WP_SMOKE_MARKER = 22
    WP_KAR98 = 23
    WP_CARBINE = 24
    WP_GARAND = 25
    WP_LANDMINE = 26
    WP_SATCHEL = 27
    WP_SATCHEL_DET = 28
    WP_TRIPMINE = 29
    WP_SMOKE_BOMB = 30
    WP_MOBILE_MG42 = 31
    WP_K43 = 32
    WP_FG42 = 33
    WP_DUMMY_MG42 = 34
    WP_MORTAR = 35
    WP_LOCKPICK = 36
    WP_AKIMBO_COLT = 37
    WP_AKIMBO_LUGER = 38
    WP_GPG40 = 39
    WP_M7 = 40
    WP_SILENCED_COLT = 41
    WP_GARAND_SCOPE = 42
    WP_K43_SCOPE = 43
    WP_FG42SCOPE = 44
    WP_MORTAR_SET = 45
    WP_MEDIC_ADRENALINE = 46
    WP_AKIMBO_SILENCEDCOLT = 47
    WP_AKIMBO_SILENCEDLUGER = 48
    WP_MOBILE_MG42_SET = 49

    @staticmethod
    def to_string(weapon_number):
        return 'not yet'

    @staticmethod
    def type(weapon_number):
        switcher = {
            Weapon.WP_NONE.value: '',
            Weapon.WP_KNIFE.value: 'knife',
            Weapon.WP_LUGER.value: 'pistol',
            Weapon.WP_MP40.value: 'smg',
            Weapon.WP_GRENADE_LAUNCHER.value: 'nade',
            Weapon.WP_PANZERFAUST.value: 'panzer',
            Weapon.WP_FLAMETHROWER.value: 'flame',
            Weapon.WP_COLT.value: 'pistol',
            Weapon.WP_THOMPSON.value: 'smg',
            Weapon.WP_GRENADE_PINEAPPLE.value: 'nade',
            Weapon.WP_STEN.value: 'sten',
            Weapon.WP_MEDIC_SYRINGE.value: 'syringe',
            Weapon.WP_AMMO.value: 'ammo',
            Weapon.WP_ARTY.value: 'arty',
            Weapon.WP_SILENCER.value: 'pistol',
            Weapon.WP_DYNAMITE.value: 'dyna',
            Weapon.WP_SMOKETRAIL.value: 'smoke',
            Weapon.WP_MAPMORTAR.value: 'map',
            Weapon.VERYBIGEXPLOSION.value: 'map',
            Weapon.WP_MEDKIT.value: '',
            Weapon.WP_BINOCULARS.value: 'bino',
            Weapon.WP_PLIERS.value: 'pliers',
            Weapon.WP_SMOKE_MARKER.value: 'strike',
            Weapon.WP_KAR98.value: 'rifle',
            Weapon.WP_CARBINE.value: 'rifle',
            Weapon.WP_GARAND.value: 's rifle',
            Weapon.WP_LANDMINE.value: 'mine',
            Weapon.WP_SATCHEL.value: 'satchel',
            Weapon.WP_SATCHEL_DET.value: 'satchel',
            Weapon.WP_TRIPMINE.value: 'mine',
            Weapon.WP_SMOKE_BOMB.value: 'smoke',
            Weapon.WP_MOBILE_MG42.value: 'mg42',
            Weapon.WP_K43.value: 's rifle',
            Weapon.WP_FG42.value: 'fg42',
            Weapon.WP_DUMMY_MG42.value: 'dummy mg42',
            Weapon.WP_MORTAR.value: 'mortar',
            Weapon.WP_LOCKPICK.value: '',
            Weapon.WP_AKIMBO_COLT.value: 'akimbo',
            Weapon.WP_AKIMBO_LUGER.value: 'akimbo',
            Weapon.WP_GPG40.value: 'riflenade',
            Weapon.WP_M7.value: 'riflenade',
            Weapon.WP_SILENCED_COLT.value: 'pistol',
            Weapon.WP_GARAND_SCOPE.value: 'sniper',
            Weapon.WP_K43_SCOPE.value: 'sniper',
            Weapon.WP_FG42SCOPE.value: 'scoped fg42',
            Weapon.WP_MORTAR_SET.value: 'mortar',
            Weapon.WP_MEDIC_ADRENALINE.value: 'adrenaline',
            Weapon.WP_AKIMBO_SILENCEDCOLT.value: 'akimbo',
            Weapon.WP_AKIMBO_SILENCEDLUGER.value: 'akimbo',
            Weapon.WP_MOBILE_MG42_SET.value: 'mg42',
        }

        return switcher.get(weapon_number, "Invalid")


class MethodOfDamage(Enum):
    MOD_UNKNOWN = 0
    MOD_MACHINEGUN = 1
    MOD_BROWNING = 2
    MOD_MG42 = 3
    MOD_GRENADE = 4
    MOD_ROCKET = 5
    MOD_KNIFE = 6
    MOD_LUGER = 7
    MOD_COLT = 8
    MOD_MP40 = 9
    MOD_THOMPSON = 10
    MOD_STEN = 11
    MOD_GARAND = 12
    MOD_SNOOPERSCOPE = 13
    MOD_SILENCER = 14
    MOD_FG42 = 15
    MOD_FG42SCOPE = 16
    MOD_PANZERFAUST = 17
    MOD_GRENADE_LAUNCHER = 18
    MOD_FLAMETHROWER = 19
    MOD_GRENADE_PINEAPPLE = 20
    MOD_CROSS = 21
    MOD_MAPMORTAR = 22
    MOD_MAPMORTAR_SPLASH = 23
    MOD_KICKED = 24
    MOD_GRABBER = 25
    MOD_DYNAMITE = 26
    MOD_AIRSTRIKE = 27
    MOD_SYRINGE = 28
    MOD_AMMO = 29
    MOD_ARTY = 30
    MOD_WATER = 31
    MOD_SLIME = 32
    MOD_LAVA = 33
    MOD_CRUSH = 34
    MOD_TELEFRAG = 35
    MOD_FALLING = 36
    MOD_SUICIDE = 37
    MOD_TARGET_LASER = 38
    MOD_TRIGGER_HURT = 39
    MOD_EXPLOSIVE = 40
    MOD_CARBINE = 41
    MOD_KAR98 = 42
    MOD_GPG40 = 43
    MOD_M7 = 44
    MOD_LANDMINE = 45
    MOD_SATCHEL = 46
    MOD_TRIPMINE = 47
    MOD_SMOKEBOMB = 48
    MOD_MOBILE_MG42 = 49
    MOD_SILENCED_COLT = 50
    MOD_GARAND_SCOPE = 51
    MOD_CRUSH_CONSTRUCTION = 52
    MOD_CRUSH_CONSTRUCTIONDEATH = 53
    MOD_CRUSH_CONSTRUCTIONDEATH_NOATTACKER = 54
    MOD_K43 = 55
    MOD_K43_SCOPE = 56
    MOD_MORTAR = 57
    MOD_AKIMBO_COLT = 58
    MOD_AKIMBO_LUGER = 59
    MOD_AKIMBO_SILENCEDCOLT = 60
    MOD_AKIMBO_SILENCEDLUGER = 61
    MOD_SMOKEGRENADE = 62
    MOD_SWAP_PLACES = 63
    MOD_SWITCHTEAM = 64

    @staticmethod
    def to_weapon(mod_number):
        switcher = {
            MethodOfDamage.MOD_UNKNOWN.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_MACHINEGUN.value: Weapon.WP_MOBILE_MG42,
            MethodOfDamage.MOD_BROWNING.value: Weapon.WP_MOBILE_MG42,
            MethodOfDamage.MOD_MG42.value: Weapon.WP_MOBILE_MG42_SET,
            MethodOfDamage.MOD_GRENADE.value: Weapon.WP_GRENADE_PINEAPPLE,
            MethodOfDamage.MOD_ROCKET.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_KNIFE.value: Weapon.WP_KNIFE,
            MethodOfDamage.MOD_LUGER.value: Weapon.WP_LUGER,
            MethodOfDamage.MOD_COLT.value: Weapon.WP_COLT,
            MethodOfDamage.MOD_MP40.value: Weapon.WP_MP40,
            MethodOfDamage.MOD_THOMPSON.value: Weapon.WP_THOMPSON,
            MethodOfDamage.MOD_STEN.value: Weapon.WP_STEN,
            MethodOfDamage.MOD_GARAND.value: Weapon.WP_GARAND,
            MethodOfDamage.MOD_SNOOPERSCOPE.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_SILENCER.value: Weapon.WP_LUGER,
            MethodOfDamage.MOD_FG42.value: Weapon.WP_FG42,
            MethodOfDamage.MOD_FG42SCOPE.value: Weapon.WP_FG42SCOPE,
            MethodOfDamage.MOD_PANZERFAUST.value: Weapon.WP_PANZERFAUST,
            MethodOfDamage.MOD_GRENADE_LAUNCHER.value: Weapon.WP_GRENADE_LAUNCHER,
            MethodOfDamage.MOD_FLAMETHROWER.value: Weapon.WP_FLAMETHROWER,
            MethodOfDamage.MOD_GRENADE_PINEAPPLE.value: Weapon.WP_GRENADE_PINEAPPLE,
            MethodOfDamage.MOD_CROSS.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_MAPMORTAR.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_MAPMORTAR_SPLASH.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_KICKED.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_GRABBER.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_DYNAMITE.value: Weapon.WP_DYNAMITE,
            MethodOfDamage.MOD_AIRSTRIKE.value: Weapon.WP_SMOKE_MARKER,
            MethodOfDamage.MOD_SYRINGE.value: Weapon.WP_MEDIC_SYRINGE,
            MethodOfDamage.MOD_AMMO.value: Weapon.WP_AMMO,
            MethodOfDamage.MOD_ARTY.value: Weapon.WP_ARTY,
            MethodOfDamage.MOD_WATER.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_SLIME.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_LAVA.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_CRUSH.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_TELEFRAG.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_FALLING.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_SUICIDE.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_TARGET_LASER.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_TRIGGER_HURT.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_EXPLOSIVE.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_CARBINE.value: Weapon.WP_CARBINE,
            MethodOfDamage.MOD_KAR98.value: Weapon.WP_KAR98,
            MethodOfDamage.MOD_GPG40.value: Weapon.WP_GPG40,
            MethodOfDamage.MOD_M7.value: Weapon.WP_M7,
            MethodOfDamage.MOD_LANDMINE.value: Weapon.WP_LANDMINE,
            MethodOfDamage.MOD_SATCHEL.value: Weapon.WP_SATCHEL,
            MethodOfDamage.MOD_TRIPMINE.value: Weapon.WP_TRIPMINE,
            MethodOfDamage.MOD_SMOKEBOMB.value: Weapon.WP_SMOKE_BOMB,
            MethodOfDamage.MOD_MOBILE_MG42.value: Weapon.WP_MOBILE_MG42,
            MethodOfDamage.MOD_SILENCED_COLT.value: Weapon.WP_SILENCED_COLT,
            MethodOfDamage.MOD_GARAND_SCOPE.value: Weapon.WP_GARAND_SCOPE,
            MethodOfDamage.MOD_CRUSH_CONSTRUCTION.value: Weapon.WP_PLIERS,
            MethodOfDamage.MOD_CRUSH_CONSTRUCTIONDEATH.value: Weapon.WP_PLIERS,
            MethodOfDamage.MOD_CRUSH_CONSTRUCTIONDEATH_NOATTACKER.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_K43.value: Weapon.WP_K43,
            MethodOfDamage.MOD_K43_SCOPE.value: Weapon.WP_K43_SCOPE,
            MethodOfDamage.MOD_MORTAR.value: Weapon.WP_MORTAR,
            MethodOfDamage.MOD_AKIMBO_COLT.value: Weapon.WP_AKIMBO_COLT,
            MethodOfDamage.MOD_AKIMBO_LUGER.value: Weapon.WP_AKIMBO_LUGER,
            MethodOfDamage.MOD_AKIMBO_SILENCEDCOLT.value: Weapon.WP_AKIMBO_SILENCEDCOLT,
            MethodOfDamage.MOD_AKIMBO_SILENCEDLUGER.value: Weapon.WP_AKIMBO_SILENCEDLUGER,
            MethodOfDamage.MOD_SMOKEGRENADE.value: Weapon.WP_SMOKE_MARKER,
            MethodOfDamage.MOD_SWAP_PLACES.value: Weapon.WP_NONE,
            MethodOfDamage.MOD_SWITCHTEAM.value: Weapon.WP_NONE,
        }
        return switcher.get(mod_number, Weapon.WP_NONE)


class RtcwWeapon(Enum):
    WP_UNKNOWN = -1
    WP_NONE = 0
    WP_KNIFE = 1
    WP_LUGER = 2
    WP_MP40 = 3
    WP_MAUSER = 4
    WP_FG42 = 5
    WP_GRENADE_LAUNCHER = 6
    WP_PANZERFAUST = 7
    WP_VENOM = 8
    WP_FLAMETHROWER = 9
    WP_TESLA = 10
    WP_SPEARGUN = 11
    WP_KNIFE2 = 12
    WP_COLT = 13
    WP_THOMPSON = 14
    WP_GARAND = 15
    WP_BAR = 16
    WP_GRENADE_PINEAPPLE = 17
    WP_ROCKET_LAUNCHER = 18
    WP_SNIPERRIFLE = 19
    WP_SNOOPERSCOPE = 20
    WP_VENOM_FULL = 21
    WP_SPEARGUN_CO2 = 22
    WP_FG42SCOPE = 23
    WP_BAR2 = 24
    WP_STEN = 25
    WP_MEDIC_SYRINGE = 26
    WP_AMMO = 27
    WP_ARTY = 28
    WP_SILENCER = 29
    WP_AKIMBO = 30
    WP_CROSS = 31
    WP_DYNAMITE = 32
    WP_DYNAMITE2 = 33
    WP_PROX = 34
    WP_MONSTER_ATTACK1 = 35
    WP_MONSTER_ATTACK2 = 36
    WP_MONSTER_ATTACK3 = 37
    WP_SMOKETRAIL = 38
    WP_GAUNTLET = 39
    WP_SNIPER = 40
    WP_MORTAR = 41
    VERYBIGEXPLOSION = 42
    WP_MEDKIT = 43
    WP_PLIERS = 44
    WP_SMOKE_GRENADE = 45
    WP_BINOCULARS = 46
    WP_NUM_WEAPONS = 47
