import argparse
import datetime
import struct
import csv
import os
import hashlib
import io
from Libraries import *

verbose = False
auto_close = False
true_offsets = False
null_strings = False

class StringDatabase:
  def __init__(self, offset, hash, j_string, e_string):
    self.offset = offset
    self.hash = hash
    self.j_string = j_string
    self.e_string = e_string

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-verbose", action="store_true", help="Enable verbose output.")
  parser.add_argument("-close", action="store_true", help="Automatically close the program after finishing.")
  parser.add_argument("-trueoffsets", action="store_true", help="Use true offsets instead of relative offsets.")
  parser.add_argument("-nullstrings", action="store_true", help="Use null strings instead of empty strings.")
  parser.add_argument("command", help="The command to execute.")
  parser.add_argument("args", nargs="*", help="The arguments to pass to the command.")
  args = parser.parse_args()

  global verbose, auto_close, true_offsets, null_strings
  verbose = args.verbose
  auto_close = args.close
  true_offsets = args.trueoffsets
  null_strings = args.nullstrings

  if args.command == "fulldump":
    dump_and_hash(args.args[0], 0, 0)
  elif args.command == "dump":
    dump_and_hash(args.args[0], int(args.args[1]), int(args.args[2]))
  elif args.command == "insert":
    insert_strings(args.args[0], args.args[1])
  elif args.command == "merge":
    merge(args.args[0], args.args[1])
  elif args.command == "cleanTrados":
    clean_trados(args.args[0])
  elif args.command == "insertCAT":
    insert_cat_file(args.args[0], args.args[1])
  else:
    print("Unknown command: {}".format(args.command))
    return

  if not auto_close:
    print("Done")
    input()

def insert_cat_file(cat_file, csv_file):
  """Inserts the strings from the CSV file into the CAT file.

  Args:
    cat_file: The path to the CAT file.
    csv_file: The path to the CSV file.
  """

  # Clean the Trados markers from the CAT file.
  clean_trados(cat_file)

  # Read the CAT file into a list of strings.
  cat_strings = []
  with open(cat_file, "r", encoding="utf-8") as f:
    for line in f:
      cat_strings.append(line.strip())

  # Read the CSV file into a list of StringDatabase objects.
  string_db = []
  with open(csv_file, "r", encoding="shift-jis") as f:
    reader = csv.reader(f, delimiter="\t", ignore_quotes=True, lineterminator="\n")
    reader.read()  # Skip the header row.

    for row in reader:
      record = StringDatabase(
          int(row[0]),
          int(row[1]),
          row[2],
          row[3],
      )
      string_db.append(record)

  # Copy the catStrings to the new database.
  for i in range(len(string_db)):
    # Update the entry if the Japanese string is different.
    if string_db[i].j_string != cat_strings[i]:
      string_db[i].e_string = cat_strings[i]

    # Allow for deletions.
    elif string_db[i].j_string == cat_strings[i] and string_db[i].e_string != "":
      string_db[i].e_string = ""

  # Write the new database to a CSV file.
  output_file_name = os.path.join("csv", os.path.basename(csv_file))
  if os.path.exists(output_file_name):
    os.remove(output_file_name)

  with open(output_file_name, "w", encoding="shift-jis") as f:
    f.write("Offset\tHash\tjString\teString\n")
    for record in string_db:
      f.write(f"{record.offset}\t{record.hash}\t{record.j_string}\t{record.e_string}\n")

  # Move the old CAT file to a backup directory.
  backup_dir = "backup"
  if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

  backup_file_name = os.path.join(backup_dir, f"{os.path.splitext(os.path.basename(cat_file))[0]}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt")
  os.rename(cat_file, backup_file_name)

def clean_trados(file):
  """Cleans up Trados markers from a file.

  Args:
    file: The path to the file to clean.
  """

  with open(file, "r", encoding="utf-8") as f:
    text = f.read()

  text = text.replace(": ~", ":~")
  text = text.replace("。 ", "。")
  text = text.replace("！ ", "！")
  text = text.replace("？ ", "？")
  text = text.replace("： ", "：")
  text = text.replace("． ", "．")
  text = text.replace("． ", "．")
  text = text.replace("」 ", "」")
  text = text.replace("「 ", "「")
  text = text.replace("） ", "）")
  text = text.replace("（ ", "（")

  with open(file, "w", encoding="utf-8") as f:
    f.write(text)

  print("Cleaned up")


class StringDatabase:
  def __init__(self, offset, hash, e_string):
    self.offset = offset
    self.hash = hash
    self.e_string = e_string

def insert_strings(input_file, input_csv):
  """Inserts the strings from the CSV file into the input file.

  Args:
    input_file: The path to the input file.
    input_csv: The path to the CSV file.
  """

  # Read the input file into a byte array.
  with open(input_file, "rb") as f:
    input_array = f.read()

  # Read the CSV file into a list of StringDatabase objects.
  string_database = []
  with open(input_csv, "r", encoding="shift-jis") as f:
    reader = csv.reader(f, delimiter="\t", ignore_quotes=True, lineterminator="\n")
    reader.read()  # Skip the header row.

    for row in reader:
      record = StringDatabase(
          int(row[0]),
          int(row[1]),
          row[2].replace("<TAB>", "\t").replace("<CLINE>", "\r\n").replace("<NLINE>", "\n"),
      )
      string_database.append(record)

  # Get the offsets and lengths of the strings that need to be remapped.
  e_strings_offsets = []
  e_string_lengths = []
  for record in string_database:
    if record.e_string != "":
      e_strings_offsets.append(record.offset)
      e_string_lengths.append(get_null_terminated_string_length(record.e_string))

  # Calculate the total length of the new strings.
  e_strings_length = sum(e_string_lengths)

  # Create a dictionary of offset replacements.
  offset_dict = {}
  for i in range(len(e_strings_offsets)):
    offset_dict[e_strings_offsets[i]] = input_array.length + sum(e_string_lengths[:i])

  # Create a new byte array for the strings.
  e_strings_array = bytearray(e_strings_length)

  # Copy the strings to the new byte array.
  for i in range(len(string_database)):
    if string_database[i].e_string != "":
      start_index = sum(e_string_lengths[:i])
      end_index = start_index + e_string_lengths[i] - 1
      e_strings_array[start_index:end_index] = string_database[i].e_string.encode("shift-jis")

  # Replace the offsets in the binary file.
  if true_offsets:
    for key, value in offset_dict.items():
      input_array[key:key + 4] = struct.pack("<I", value)
  else:
    for i in range(0, len(input_array), 4):
      if i + 4 > len(input_array):
        continue

      offset = struct.unpack("<I", input_array[i:i + 4])[0]
      if offset in offset_dict and i > 10000:
        input_array[i:i + 4] = struct.pack("<I", offset_dict[offset])

  # Combine the arrays.
  output_array = bytearray(input_array + e_strings_array)

  # Write the output file.
  output_dir = "output"
  os.makedirs(output_dir, exist_ok=True)
  output_file = f"{output_dir}/{os.path.basename(input_file)}"
  with open(output_file, "wb") as f:
    f.write(output_array)

def dump_and_hash(input_file, start_offset, end_offset):
  """Dumps and hashes the strings in the input file to a CSV file.

  Args:
    input_file: The path to the input file.
    start_offset: The offset at which to start dumping the strings.
    end_offset: The offset at which to stop dumping the strings.
  """

  with open(input_file, "rb") as f:
    buffer = f.read()

  ms_input = io.MemoryStream(buffer)
  br_input = io.BinaryReader(ms_input)

  end_offset = end_offset if end_offset != 0 else len(buffer)

  print(f"Strings at: 0x{start_offset:X8} - 0x{end_offset:X8}. Size 0x{(end_offset - start_offset):X8}")

  filename = os.path.splitext(os.path.basename(input_file))[0]
  csv_file = f"{filename}.csv"
  if os.path.exists(csv_file):
    os.remove(csv_file)

  with open(csv_file, "w", encoding="shift-jis") as f:
    writer = csv.writer(f)
    writer.writerow(["Offset", "Hash", "jString", "eString"])

  br_input.seek(start_offset, io.SEEK_SET)
  while br_input.tell() + 4 <= end_offset:
    offset = br_input.tell()
    tmp_pos = br_input.tell()

    if true_offsets:
      str_pos = br_input.readUInt32()
      if str_pos == 0 or str_pos > len(buffer):
        continue

      tmp_pos = br_input.tell()
      if null_strings:
        br_input.seek(str_pos - 1, io.SEEK_SET)
        if br_input.readByte() != 0:
          br_input.seek(tmp_pos, io.SEEK_SET)
          continue

      br_input.seek(str_pos, io.SEEK_SET)

    str = ReadNullTerminatedString(br_input, encoding="shift-jis").replace("\t", "<TAB>").replace("\r\n", "<CLINE>").replace("\n", "<NLINE>")

    if true_offsets:
      br_input.seek(tmp_pos, io.SEEK_SET)

    if str == "":
      continue

    writer.writerow([
        offset,
        hashlib.crc32(str.encode("shift-jis")),
        str,
        ""
    ])


def merge(old_csv, new_csv):
  """Merges the two CSV files into a new CSV file.

  Args:
    old_csv: The path to the old CSV file.
    new_csv: The path to the new CSV file.
  """

  # Read the old CSV file.
  string_db_old = []
  with open(old_csv, "r", encoding="shift-jis") as f:
    reader = csv.reader(f, delimiter="\t", ignore_quotes=True, lineterminator="\n")
    reader.read()  # Skip the header row.

    for row in reader:
      record = StringDatabase(
          None,
          int(row[0]),
          row[1],
          ""
      )
      string_db_old.append(record)

  # Read the new CSV file.
  string_db_new = []
  with open(new_csv, "r", encoding="shift-jis") as f:
    reader = csv.reader(f, delimiter="\t", ignore_quotes=True, lineterminator="\n")
    reader.read()  # Skip the header row.

    for row in reader:
      record = StringDatabase(
          int(row[0]),
          int(row[1]),
          row[2],
          row[3]
      )
      string_db_new.append(record)

  # Copy the eStrings from the old database to the new database.
  for i in range(len(string_db_old)):
    print(f"\rUpdating entry {i + 1}/{len(string_db_old)}", end="")

    if string_db_old[i].e_string != "":
      matched_new_objs = [obj for obj in string_db_new if obj.hash == string_db_old[i].hash]

      if matched_new_objs:
        for obj in matched_new_objs:
          obj.e_string = string_db_old[i].e_string

  print()

  # Write the new CSV file.
  output_file = f"csv/{os.path.basename(old_csv)}"
  if os.path.exists(output_file):
    os.remove(output_file)

  with open(output_file, "w", encoding="shift-jis") as f:
    writer = csv.writer(f)
    writer.writerow(["Offset", "Hash", "jString", "eString"])

    for obj in string_db_new:
      writer.writerow([
          obj.offset,
          obj.hash,
          obj.j_string,
          obj.e_string
      ])

  os.remove(new_csv)

def get_null_terminated_string_length(input_string):
  """Calculates the length of a null-terminated string.

  Args:
    input_string: The string to calculate the length of.

  Returns:
    The length of the string, including the null terminator.
  """

  return len(input_string.encode("shift-jis")) + 1

if __name__ == "__main__":
  main()