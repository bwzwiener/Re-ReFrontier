import os
import datetime
import hashlib
import binascii
import struct
from enum import Enum

class Extensions(Enum):
    DDS = 542327876
    FTXT = 0x000B0000
    GFX2 = 846751303
    JKR = 0x1A524B4A
    OGG = 0x5367674F
    PMO = 7302512
    PNG = 0x474E5089
    TMH = 1213027374

def ReadNullTerminatedString(br_input, encoding="utf-8"):
  """Reads a null-terminated string from a BinaryReader object.

  Args:
    br_input: A BinaryReader object.
    encoding: The encoding of the string.

  Returns:
    A string.
  """

  char_byte_list = []
  while True:
    b = br_input.read(1)
    if b == b"\x00":
      break
    char_byte_list.append(b)

  char_bytes = b"".join(char_byte_list)
  return char_bytes.decode(encoding)


def print_message(input, print_before=False):
    """Prints a message to the console.

    Args:
        input: The message to print.
        print_before: Whether to print the message before or after the separator line.
    """

    if not print_before:
        print(input)
        print("==============================")
    else:
        print("\n==============================")
        print(input)

def GetCrc32(array):
  """Calculates the CRC32 checksum of a byte array.

  Args:
    array: A byte array.

  Returns:
    A uint representing the CRC32 checksum.
  """

  crc32 = binascii.crc32(array)
  return crc32 & 0xFFFFFFFF

def GetUpdateEntry(input_file):
  """Generates an update entry for the given file.

  Args:
    input_file: The path to the input file.

  Returns:
    A string containing the update entry.
  """

  # Get the last write time of the file.
  date = datetime.datetime.fromtimestamp(os.path.getmtime(input_file))

  # Convert the date to a hexadecimal string.
  date_hex1 = date.strftime("%X").split(".")[0]
  date_hex2 = date.strftime("%X").split(".")[1]

  # Read the file contents.
  repack_data = open(input_file, "rb").read()

  # Calculate the CRC32 of the file contents.
  crc32 = hashlib.crc32(repack_data).hexdigest()

  # Generate the update entry.
  update_entry = f"{crc32},{date_hex1},{date_hex2},{input_file},{len(repack_data)},0"

  return update_entry

def GetOffsetOfArray(haystack, needle):
  """Returns the offset of the needle in the haystack, or -1 if not found.

  Args:
    haystack: A byte array.
    needle: A byte array.

  Returns:
    An int representing the offset of the needle in the haystack, or -1 if not found.
  """

  for i in range(len(haystack) - len(needle) + 1):
    if MatchArrays(haystack, needle, i):
      return i
  return -1

def MatchArrays(haystack, needle, start):
  """Returns True if the needle matches the haystack at the given start offset, False otherwise.

  Args:
    haystack: A byte array.
    needle: A byte array.
    start: The offset in the haystack to start matching at.

  Returns:
    A bool representing whether the needle matches the haystack at the given start offset.
  """

  if start + len(needle) > len(haystack):
    return False
  else:
    for i in range(len(needle)):
      if needle[i] != haystack[i + start]:
        return False
    return True
  
def CheckForMagic(header_int, data):
  """Returns the file extension for files without a unique 4-byte magic, or None if not found.

  Args:
    header_int: The first 4 bytes of the file, as a Python integer.
    data: The entire file contents, as a Python byte array.

  Returns:
    A string representing the file extension, or None if not found.
  """

  header = data[:12]

  if header_int == 1:
    extension = "fmod" if struct.unpack("<L", header[8:])[0] == len(data) else None
  elif header_int == 0xC0000000:
    extension = "fskl" if struct.unpack("<L", header[8:])[0] == len(data) else None

  return extension
