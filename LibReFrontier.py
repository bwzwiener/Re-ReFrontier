import os
import datetime
import hashlib

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