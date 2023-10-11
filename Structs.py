from enum import Enum

class QuestData:

  def __init__(self, **kwargs):
    for key, value in kwargs.items():
      setattr(self, key, value)

class QuestTypes(Enum):

    NONE = 0
    HUNT = 0x00000001
    CAPTURE = 0x00000101
    KILL = 0x00000201
    DELIVERY = 0x00000002
    GUILD_FLAG = 0x00001002
    DAMAGING = 0x00008004

class ArmorDataEntry:

  def __init__(self, **kwargs):
    for key, value in kwargs.items():
      setattr(self, key, value)

class MeleeWeaponEntry:

  def __init__(self, **kwargs):
    for key, value in kwargs.items():
      setattr(self, key, value)

class RangedWeaponEntry:

  def __init__(self, **kwargs):
    for key, value in kwargs.items():
      setattr(self, key, value)