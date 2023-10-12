import sys
import io
import csv
import struct
from Structs import *

# Define offset pointers

# --- mhfdat.bin ---
# Strings
SO_STRING_HEAD = 0x64
SO_STRING_BODY = 0x68
SO_STRING_ARM = 0x6C
SO_STRING_WAIST = 0x70
SO_STRING_LEG = 0x74
EO_STRING_HEAD = 0x60
EO_STRING_BODY = 0x64
EO_STRING_ARM = 0x68
EO_STRING_WAIST = 0x6C
EO_STRING_LEG = 0x70
SO_STRING_RANGED = 0x84
SO_STRING_MELEE = 0x88
EO_STRING_RANGED = 0x88
EO_STRING_MELEE = 0x174
SO_STRING_ITEM = 0x100
SO_STRING_ITEM_DESC = 0x12C
EO_STRING_ITEM = 0xFC
EO_STRING_ITEM_DESC = 0x100

# Armor
SO_HEAD = 0x50
SO_BODY = 0x54
SO_ARM = 0x58
SO_WAIST = 0x5C
SO_LEG = 0x60
EO_HEAD = 0xE8
EO_BODY = 0x50
EO_ARM = 0x54
EO_WAIST = 0x58
EO_LEG = 0x5C

# Weapons
SO_RANGED = 0x80
SO_MELEE = 0x7C
EO_RANGED = 0x7C
EO_MELEE = 0x90

# --- mhfpac.bin ---
# Strings
SO_STRING_SKILL_PT = 0xA20
SO_STRING_SKILL_ACTIVATE = 0xA1C
SO_STRING_ZSKILL = 0xFBC
SO_STRING_SKILL_DESC = 0xb8
EO_STRING_SKILL_PT = 0xA1C
EO_STRING_SKILL_ACTIVATE = 0xBC0
EO_STRING_ZSKILL = 0xFB0
EO_STRING_SKILL_DESC = 0xc0

# --- mhfinf.pac ---
OFFSET_INF_QUEST_DATA = [
    (0x6bd60, 95),
    (0x74100, 62),
    (0x797e0, 99),
    (0x821a0, 98),
    (0x8aa00, 99),
    (0x933c0, 99),
    (0x9bd80, 99),
    (0xa4740, 99),
    (0xad100, 99),
    (0xb5b40, 36),
    (0xb8e60, 96),
    (0xc1400, 91),
    (0x161220, 20) # This entry is incorrect
]

# Define offset pointers

# Armor
DATA_POINTERS_ARMOR = [
    (SO_HEAD, EO_HEAD),
    (SO_BODY, EO_BODY),
    (SO_ARM, EO_ARM),
    (SO_WAIST, EO_WAIST),
    (SO_LEG, EO_LEG)
]

STRING_POINTERS_ARMOR = [
    (SO_STRING_HEAD, EO_STRING_HEAD),
    (SO_STRING_BODY, EO_STRING_BODY),
    (SO_STRING_ARM, EO_STRING_ARM),
    (SO_STRING_WAIST, EO_STRING_WAIST),
    (SO_STRING_LEG, EO_STRING_LEG)
]

# Define classes

ELEMENT_IDS = ["なし", "火", "水", "雷", "龍", "氷", "炎", "光", "雷極", "天翔", "熾凍", "黒焔", "奏", "闇", "紅魔", "風", "響", "灼零", "皇鳴"]
AILMENT_IDS = ["なし", "毒", "麻痺", "睡眠", "爆破"]
WEAPON_CLASS_IDS = ["大剣", "ヘビィボウガン", "ハンマー", "ランス", "片手剣", "ライトボウガン", "双剣", "太刀", "狩猟笛", "ガンランス", "弓", "穿龍棍", "スラッシュアックスＦ", "マグネットスパイク"]
ARMOR_CLASS_IDS = ["頭", "胴", "腕", "腰", "脚"]
EQ_TYPE = {
    "通常": 0,
    "SP": 1,
    "剛種": 2,
    "進化": 4,
    "HC": 8
}

# Define class StringDatabase

class StringDatabase:
    def __init__(self, offset: int, hash: int, j_string: str, e_string: str):
        self.offset = offset
        self.hash = hash
        self.j_string = j_string
        self.e_string = e_string


def main():
  """The main function."""

  if len(sys.argv) < 2:
    print("Too few arguments.")
    return

  if sys.argv[1] == "dump":
    dump_data(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
  elif sys.argv[1] == "modshop":
    mod_shop(sys.argv[2])
  else:
    print("Unknown command.")

  print("Done")

def dump_data(suffix: str, mhfpac: str, mhfdat: str, mhfinf: str):
  """Dumps the skill system dictionary to a text file.

  Args:
    suffix: The suffix to use for the output file name.
    mhfpac: The path to the MHFPAC file.
    mhfdat: The path to the MHFDAT file.
    mhfinf: The path to the MHFINF file.
  """

  # Get and dump skill system dictionary
  print("Dumping skill tree names.")
  with open(mhfpac, "rb") as f:
    ms_input = io.BytesIO(f.read())
    br_input = io.BinaryReader(ms_input)
    br_input.seek(SO_STRING_SKILL_PT)
    s_offset = br_input.read_int32()
    br_input.seek(EO_STRING_SKILL_PT)
    e_offset = br_input.read_int32()

    br_input.seek(s_offset)
    skill_id = []
    id = 0
    while br_input.tell() < e_offset:
      name = string_from_pointer(br_input)
      skill_id.append((id, name))
      id += 1

  text_name = f"mhsx_SkillSys_{suffix}.txt"
  with open(text_name, "w", encoding="utf-8") as f:
    for id, name in skill_id:
      f.write(f"{name}\n")

  # Dump active skill names
  print("Dumping active skill names.")
  br_input.seek(SO_STRING_SKILL_ACTIVATE)
  s_offset = br_input.read_int32()
  br_input.seek(EO_STRING_SKILL_ACTIVATE)
  e_offset = br_input.read_int32()
  br_input.seek(s_offset)
  active_skill = []
  while br_input.tell() < e_offset:
    name = string_from_pointer(br_input)
    active_skill.append(name)
  
  text_name = f"mhsx_SkillActivate_{suffix}.txt"
  with open(text_name, "w", encoding="utf-8") as f:
    for name in active_skill:
      f.write(f"{name}\n")
  
  # Dump active skill descriptions
  print("Dumping active skill descriptions.")
  br_input.seek(SO_STRING_SKILL_DESC)
  s_offset = br_input.read_int32()
  br_input.seek(EO_STRING_SKILL_DESC)
  e_offset = br_input.read_int32()
  br_input.seek(s_offset)
  skill_desc = []
  while br_input.tell() < e_offset:
    name = string_from_pointer(br_input)
    skill_desc.append(name)
  
  text_name = f"mhsx_SkillDesc_{suffix}.txt"
  with open(text_name, "w", encoding="utf-8") as f:
    for name in skill_desc:
      f.write(f"{name}\n")

  # Dump Z skill names
  print("Dumping Z skill names.")
  br_input.seek(SO_STRING_ZSKILL)
  s_offset = br_input.read_int32()
  br_input.seek(EO_STRING_ZSKILL)
  e_offset = br_input.read_int32()
  br_input.seek(s_offset)
  z_skill = []
  while br_input.tell() < e_offset:
    name = string_from_pointer(br_input)
    z_skill.append(name)
  
  text_name = f"mhsx_SkillZ_{suffix}.txt"
  with open(text_name, "w", encoding="utf-8") as f:
    for name in z_skill:
      f.write(f"{name}\n")

  # Dump item names
  print("Dumping item names.")
  with open(mhfdat, "rb") as f:
      ms_input = io.BytesIO(f.read())
      br_input = io.BinaryReader(ms_input)
      br_input.seek(SO_STRING_ITEM)
      s_offset = br_input.read_int32()
      br_input.seek(EO_STRING_ITEM)
      e_offset = br_input.read_int32()
      br_input.seek(s_offset)
      items = []
      while br_input.tell() < e_offset:
          name = string_from_pointer(br_input)
          items.append(name)
  
  text_name = f"mhsx_Items_{suffix}.txt"
  with open(text_name, "w", encoding="utf-8") as f:
      for name in items:
          f.write(f"{name}\n")
  
  # Dump item descriptions
  print("Dumping item descriptions.")
  br_input.seek(SO_STRING_ITEM_DESC)
  s_offset = br_input.read_int32()
  br_input.seek(EO_STRING_ITEM_DESC)
  e_offset = br_input.read_int32()
  br_input.seek(s_offset)
  items_desc = []
  while br_input.tell() < e_offset:
      name = string_from_pointer(br_input)
      items_desc.append(name)
  
  text_name = f"Items_Desc_{suffix}.txt"
  with open(text_name, "w", encoding="utf-8") as f:
      for name in items_desc:
          f.write(f"{name}\n")





  # Dump armor data
  total_count = 0
  for i in range(5):
    # Get raw data
    br_input.seek(DATA_POINTERS_ARMOR[i][0])
    s_offset = br_input.read_int32()
    br_input.seek(DATA_POINTERS_ARMOR[i][1])
    e_offset = br_input.read_int32()
    entry_count = (e_offset - s_offset) // 0x48
    total_count += entry_count

  print(f"Total armor count: {total_count}")

  armor_entries = []
  current_count = 0
  for i in range(5):
    # Get raw data
    br_input.seek(DATA_POINTERS_ARMOR[i][0])
    s_offset = br_input.read_int32()
    br_input.seek(DATA_POINTERS_ARMOR[i][1])
    e_offset = br_input.read_int32()
    entry_count = (e_offset - s_offset) // 0x48
    br_input.seek(s_offset)
    print(f"{ARMOR_CLASS_IDS[i]} count: {entry_count}")

    for j in range(entry_count):
      entry = ArmorDataEntry()
      entry.equip_class = ARMOR_CLASS_IDS[i]
      entry.model_id_male = br_input.read_int16()
      entry.model_id_female = br_input.read_int16()
      bitfield = br_input.read_byte()
      entry.is_male_equip = (bitfield & (1 << 1 - 1)) != 0
      entry.is_female_equip = (bitfield & (1 << 2 - 1)) != 0
      entry.is_blade_equip = (bitfield & (1 << 3 - 1)) != 0
      entry.is_gunner_equip = (bitfield & (1 << 4 - 1)) != 0
      entry.bool1 = (bitfield & (1 << 5 - 1)) != 0
      entry.is_sp_equip = (bitfield & (1 << 6 - 1)) != 0
      entry.bool3 = (bitfield & (1 << 7 - 1)) != 0
      entry.bool4 = (bitfield & (1 << 8 - 1)) != 0
      entry.rarity = br_input.read_byte()
      entry.max_level = br_input.read_byte()
      entry.unk1_1 = br_input.read_byte()
      entry.unk1_2 = br_input.read_byte()
      entry.unk1_3 = br_input.read_byte()
      entry.unk1_4 = br_input.read_byte()
      entry.unk2 = br_input.read_byte()
      entry.zenny_cost = br_input.read_int32()
      entry.unk3 = br_input.read_int16()
      entry.base_defense = br_input.read_int16()
      entry.fire_res = br_input.read_byte()
      entry.water_res = br_input.read_byte()
      entry.thunder_res = br_input.read_byte()
      entry.dragon_res = br_input.read_byte()
      entry.ice_res = br_input.read_byte()
      entry.unk3_1 = br_input.read_int16()
      entry.base_slots = br_input.read_byte()
      entry.max_slots = br_input.read_byte()
      entry.sth_event_crown = br_input.read_byte()
      entry.unk5 = br_input.read_byte()
      entry.unk6 = br_input.read_byte()
      entry.unk7_1 = br_input.read_byte()
      entry.unk7_2 = br_input.read_byte()
      entry.unk7_3 = br_input.read_byte()
      entry.unk7_4 = br_input.read_byte()
      entry.unk8_1 = br_input.read_byte()
      entry.unk8_2 = br_input.read_byte()
      entry.unk8_3 = br_input.read_byte()
      entry.unk8_4 = br_input.read_byte()
      entry.unk10 = br_input.read_int16()
      entry.skill_id_1 = skill_id[br_input.read_byte()].value
      entry.skill_pts_1 = br_input.read_sbyte()
      entry.skill_id_2 = skill_id[br_input.read_byte()].value
      entry.skill_pts_2 = br_input.read_sbyte()
      entry.skill_id_3 = skill_id[br_input.read_byte()].value
      entry.skill_pts_3 = br_input.read_sbyte()
      entry.skill_id_4 = skill_id[br_input.read_byte()].value
      entry.skill_pts_4 = br_input.read_sbyte()
      entry.skill_id_5 = skill_id[br_input.read_byte()].value
      entry.skill_pts_5 = br_input.read_sbyte()
      entry.sth_hiden = br_input.read_int32()
      entry.unk12 = br_input.read_int32()
      entry.unk13 = br_input.read_byte()
      entry.unk14 = br_input.read_byte()
      entry.unk15 = br_input.read_byte()
      entry.unk16 = br_input.read_byte()
      entry.unk17 = br_input.read_int32()
      entry.unk18 = br_input.read_int16()
      entry.unk19 = br_input.read_int16()

      armor_entries[j + current_count] = entry

    # Get strings
    br_input.seek(STRING_POINTERS_ARMOR[i][0], io.SEEK_SET)
    s_offset = br_input.read_int32()
    br_input.seek(s_offset, io.SEEK_SET)

    for j in range(entry_count - 1):
      name = string_from_pointer(br_input)
      armor_entries[j + current_count].name = name

    current_count += entry_count

  # Write armor csv
  with open("Armor.csv", "w", encoding="shift-jis") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerows(armor_entries)

  # Write armor txt
  text_name = f"mhsx_Armor_{suffix}.txt"
  with open(text_name, "w", encoding="utf-8") as f:
    for entry in armor_entries:
      f.write(entry.name)




  # Dump melee weapon data
  br_input.seek(DATA_POINTERS_ARMOR[5][0])
  s_offset = br_input.read_int32()
  br_input.seek(DATA_POINTERS_ARMOR[5][1])
  e_offset = br_input.read_int32()
  entry_count_melee = (e_offset - s_offset) // 0x34
  br_input.seek(s_offset)
  print(f"Melee count: {entry_count_melee}")

  melee_entries = []
  for i in range(entry_count_melee):
    entry = MeleeWeaponEntry()
    entry.model_id = br_input.read_int16()
    entry.model_id_data = get_model_id_data(entry.model_id)
    entry.rarity = br_input.read_byte()
    entry.class_id = WEAPON_CLASS_IDS[br_input.read_byte()]
    entry.zenny_cost = br_input.read_int32()
    entry.sharpness_id = br_input.read_int16()
    entry.raw_damage = br_input.read_int16()
    entry.defense = br_input.read_int16()
    entry.affinity = br_input.read_sbyte()
    entry.element_id = ELEMENT_IDS[br_input.read_byte()]
    entry.ele_damage = br_input.read_byte() * 10
    entry.ailment_id = AILMENT_IDS[br_input.read_byte()]
    entry.ail_damage = br_input.read_byte() * 10
    entry.slots = br_input.read_byte()
    entry.unk3 = br_input.read_byte()
    entry.unk4 = br_input.read_byte()
    entry.unk5 = br_input.read_int16()
    entry.unk6 = br_input.read_int16()
    entry.unk7 = br_input.read_int16()
    entry.unk8 = br_input.read_int32()
    entry.unk9 = br_input.read_int32()
    entry.unk10 = br_input.read_int16()
    entry.unk11 = br_input.read_int16()
    entry.unk12 = br_input.read_byte()
    entry.unk13 = br_input.read_byte()
    entry.unk14 = br_input.read_byte()
    entry.unk15 = br_input.read_byte()
    entry.unk16 = br_input.read_int32()
    entry.unk17 = br_input.read_int32()

    melee_entries.append(entry)

  # Get strings
  br_input.seek(STRING_POINTERS_ARMOR[5][0])
  s_offset = br_input.read_int32()
  br_input.seek(s_offset)
  for j in range(entry_count_melee - 1):
    name = string_from_pointer(br_input)
    melee_entries[j].name = name

  # Write csv
  with open("Melee.csv", "w", encoding="shift-jis") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerows(melee_entries)

  # Dump ranged weapon data
  br_input.seek(DATA_POINTERS_ARMOR[6][0])
  s_offset = br_input.read_int32()
  br_input.seek(DATA_POINTERS_ARMOR[6][1])
  e_offset = br_input.read_int32()
  entry_count_ranged = (e_offset - s_offset) // 0x3C
  br_input.seek(s_offset)
  print(f"Ranged count: {entry_count_ranged}")

  ranged_entries = []
  for i in range(entry_count_ranged):
    entry = RangedWeaponEntry()
    entry.model_id = br_input.read_int16()
    entry.model_id_data = get_model_id_data(entry.model_id)
    entry.rarity = br_input.read_byte()
    entry.max_slots_maybe = br_input.read_byte()
    entry.class_id = WEAPON_CLASS_IDS[br_input.read_byte()]
    entry.unk2_1 = br_input.read_byte()
    entry.eq_type = str(br_input.read_byte())  # Enum.GetName(typeof(eqType), brInput.ReadByte());
    entry.unk2_3 = br_input.read_byte()
    entry.unk3_1 = br_input.read_byte()
    entry.unk3_2 = br_input.read_byte()
    entry.unk3_3 = br_input.read_byte()
    entry.unk3_4 = br_input.read_byte()
    entry.unk4_1 = br_input.read_byte()
    entry.unk4_2 = br_input.read_byte()
    entry.unk4_3 = br_input.read_byte()
    entry.unk4_4 = br_input.read_byte()
    entry.unk5_1 = br_input.read_byte()
    entry.unk5_2 = br_input.read_byte()
    entry.unk5_3 = br_input.read_byte()
    entry.unk5_4 = br_input.read_byte()
    entry.zenny_cost = br_input.read_int32()
    entry.raw_damage = br_input.read_int16()
    entry.defense = br_input.read_int16()
    entry.recoil_maybe = br_input.read_byte()
    entry.slots = br_input.read_byte()
    entry.affinity = br_input.read_sbyte()
    entry.sort_order_maybe = br_input.read_byte()
    entry.unk6_1 = br_input.read_byte()
    entry.element_id = ELEMENT_IDS[br_input.read_byte()]
    entry.ele_damage = br_input.read_byte() * 10
    entry.unk6_4 = br_input.read_byte()
    entry.unk7_1 = br_input.read_byte()
    entry.unk7_2 = br_input.read_byte()
    entry.unk7_3 = br_input.read_byte()
    entry.unk7_4 = br_input.read_byte()
    entry.unk8_1 = br_input.read_byte()
    entry.unk8_2 = br_input.read_byte()
    entry.unk8_3 = br_input.read_byte()
    entry.unk8_4 = br_input.read_byte()
    entry.unk9_1 = br_input.read_byte()
    entry.unk9_2 = br_input.read_byte()
    entry.unk9_3 = br_input.read_byte()
    entry.unk9_4 = br_input.read_byte()
    entry.unk10_1 = br_input.read_byte()
    entry.unk10_2 = br_input.read_byte()
    entry.unk10_3 = br_input.read_byte()
    entry.unk10_4 = br_input.read_byte()
    entry.unk11_1 = br_input.read_byte()
    entry.unk11_2 = br_input.read_byte()
    entry.unk11_3 = br_input.read_byte()
    entry.unk11_4 = br_input.read_byte()
    entry.unk12_1 = br_input.read_byte()
    entry.unk12_2 = br_input.read_byte()
    entry.unk12_3 = br_input.read_byte()
    entry.unk12_4 = br_input.read_byte()
    
    ranged_entries.append(entry)
    
  # Get strings
  br_input.seek(STRING_POINTERS_ARMOR[6][0])
  s_offset = br_input.read_int32()
  br_input.seek(s_offset)
  for j in range(entry_count_ranged - 1):
      name = string_from_pointer(br_input)
      ranged_entries[j].name = name
  
  # Write csv
  with open("Ranged.csv", "w", encoding="shift-jis") as f:
      writer = csv.writer(f, delimiter="\t")
      writer.writerows(ranged_entries)





  # Dump inf quest data
  total_count = 0
  for j in OFFSET_INF_QUEST_DATA:
    total_count += OFFSET_INF_QUEST_DATA[j]

  quests = []
  current_count = 0
  for j in OFFSET_INF_QUEST_DATA:
    br_input.seek(OFFSET_INF_QUEST_DATA[j])
    for i in range(OFFSET_INF_QUEST_DATA[j]):
      quest = QuestData()

      # Read the quest data
      quest.unk1 = br_input.read_byte()
      quest.unk2 = br_input.read_byte()
      quest.unk3 = br_input.read_byte()
      quest.unk4 = br_input.read_byte()
      quest.level = br_input.read_byte()
      quest.unk5 = br_input.read_byte()
      quest.course_type = br_input.read_byte()
      quest.unk7 = br_input.read_byte()
      quest.unk8 = br_input.read_byte()
      quest.unk9 = br_input.read_byte()
      quest.unk10 = br_input.read_byte()
      quest.unk11 = br_input.read_byte()
      quest.fee = br_input.read_int32()
      quest.zenny_main = br_input.read_int32()
      quest.zenny_ko = br_input.read_int32()
      quest.zenny_sub_a = br_input.read_int32()
      quest.zenny_sub_b = br_input.read_int32()
      quest.time = br_input.read_int32()
      quest.unk12 = br_input.read_int32()
      quest.unk13 = br_input.read_byte()
      quest.unk14 = br_input.read_byte()
      quest.unk15 = br_input.read_byte()
      quest.unk16 = br_input.read_byte()
      quest.unk17 = br_input.read_byte()
      quest.unk18 = br_input.read_byte()
      quest.unk19 = br_input.read_byte()
      quest.unk20 = br_input.read_byte()

      # Read the quest type
      quest_type = br_input.read_int32()
      quest.main_goal_type = QuestTypes(quest_type).name
      quest.main_goal_target = br_input.read_int16()
      quest.main_goal_count = br_input.read_int16()

      # Read the subquest type A
      quest_type = br_input.read_int32()
      quest.sub_a_goal_type = QuestTypes(quest_type).name
      quest.sub_a_goal_target = br_input.read_int16()
      quest.sub_a_goal_count = br_input.read_int16()

      # Read the subquest type B
      quest_type = br_input.read_int32()
      quest.sub_b_goal_type = QuestTypes(quest_type).name
      quest.sub_b_goal_target = br_input.read_int16()
      quest.sub_b_goal_count = br_input.read_int16()

      # Skip some unknown data
      br_input.seek(0x5C, io.SEEK_CUR)

      # Read the GRP values
      quest.main_grp = br_input.read_int32()
      quest.sub_a_grp = br_input.read_int32()
      quest.sub_b_grp = br_input.read_int32()

      # Skip some more unknown data
      br_input.seek(0x90, io.SEEK_CUR)
    
      # Read the quest strings
      quest.title = string_from_pointer(br_input)
      quest.text_main = string_from_pointer(br_input)
      quest.text_sub_a = string_from_pointer(br_input)
      quest.text_sub_b = string_from_pointer(br_input)
    
      # Skip some more unknown data
      br_input.seek(0x10, io.SEEK_CUR)
      print(f"Position: {br_input.tell().to_hex()}")
    
      # Add the quest to the list
      quests.append(quest)
    
      # Increment the current count
      current_count += OFFSET_INF_QUEST_DATA[j]
    
    # Write the quests to a CSV file
    with open("InfQuests.csv", "w", encoding="shift-jis") as f:
      writer = csv.writer(f, delimiter="\t")
      writer.writerows(quests)




def mod_shop(file):
  """Modifies the shop data in the given file.

  Args:
    file: The path to the file to modify.
  """

  # Read the file into memory
  with open(file, "rb") as f:
    input_array = f.read()

  # Create a binary writer to write to the file
  with open(file, "wb") as f:
    output_array = bytearray()

    # Patch item prices
    offset_data = input_array.find(b"\x0F\x01\x01\x00\x00\x00\x00\x00\x03\x01\x01\x00\x00\x00\x00\x00")
    if offset_data != -1:
      offset_pointer = input_array.find(b"\x0F\x01\x01\x00\x00\x00\x00\x00")
      if offset_pointer != -1:
        # Patch the shop pointer
        output_array += input_array[:offset_pointer]
        output_array += struct.pack("<I", len(input_array))
        output_array += input_array[offset_pointer + 4:]

      else:
        print("Could not find shop pointer, please check manually and correct code.")
    else:
      print("Could not find shop needle, please check manually and correct code.")

    # Patch equip prices
    for i in range(5):
      s_offset = struct.unpack("<I", input_array[DATA_POINTERS_ARMOR[i][0]:DATA_POINTERS_ARMOR[i][1]])[0]
      e_offset = struct.unpack("<I", input_array[DATA_POINTERS_ARMOR[i][0] + 4:DATA_POINTERS_ARMOR[i][1]])[0]
      count = (e_offset - s_offset) // 0x48

      for j in range(count):
        # Patch the buy price
        output_array += input_array[:s_offset + (j * 0x48) + 12]
        output_array += struct.pack("<I", 50)
        output_array += input_array[s_offset + (j * 0x48) + 16:]

    # Generate the shop array
    count = 16700
    shop_array = bytearray((count * 8) + 5 * 32)
    block_size = (count / 5) * 8

    for i in range(count):
      item_id = struct.pack("<H", i + 1)
      item = bytearray(8)
      item[0:2] = item_id
      shop_array[i * 8:i * 8 + 8] = item

    # Append the modshop data to the file
    output_array += input_array
    output_array += shop_array

    # Patch the hunter pearl skill unlocks
    offset_data = input_array.find(b"\x01\x00\x01\x00\x00\x00\x00\x00\x25\x00\x25\x00\x25\x00\x25\x00\x25\x00\x25\x00\x25\x00")
    if offset_data != -1:
      pearl_patch = b"\x02\x00\x02\x00\x02\x00\x02\x00\x02\x00\x02\x00\x02\x00"
      for i in range(108):
        output_array[offset_data + (i * 0x30) + 8:offset_data + (i * 0x30) + 8 + len(pearl_patch)] = pearl_patch

    else:
      print("Could not find pearl skill needle, please check manually and correct code.")

    # Write the output array to the file
    f.write(output_array)



def string_from_pointer(br_input: io.BinaryReader) -> str:
  """Reads a null-terminated string from a binary reader.

  Args:
    br_input: The binary reader to read from.

  Returns:
    The string that was read.
  """

  offset = br_input.read_int32()
  current_position = br_input.tell()
  br_input.seek(offset, io.SEEK_SET)
  string_data = br_input.read_until(b"\x00").decode("shift-jis")
  string_data = string_data.replace("\n", "<NL>")
  br_input.seek(current_position, io.SEEK_SET)
  return string_data


def get_model_id_data(id: int) -> str:
  """Returns the model ID data for the given ID.

  Args:
    id: The model ID.

  Returns:
    The model ID data, or "Unmapped" if the ID is not mapped.
  """

  if id < 0 or id >= 1000:
    return "Unmapped"

  if id < 1000:
    return f"we{id:03d}"
  elif id < 2000:
    return f"wf{(id - 1000):03d}"
  elif id < 3000:
    return f"wg{(id - 2000):03d}"
  elif id < 4000:
    return f"wh{(id - 3000):03d}"
  elif id < 5000:
    return f"wi{(id - 4000):03d}"
  elif id < 7000:
    return f"wk{(id - 6000):03d}"
  elif id < 8000:
    return f"wl{(id - 7000):03d}"
  elif id < 9000:
    return f"wm{(id - 8000):03d}"
  elif id < 10000:
    return f"wg{(id - 9000):03d}"
  else:
    return "Unmapped"

if __name__ == "__main__":
  main()