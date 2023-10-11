import io
import os
import struct
import datetime
from JPK import *

def process_pack_input(input_path):
  """Processes the input for a packed file.

  Args:
    input_path: The path to the input file.
  """

  # Get the log file path.
  log_file_path = os.path.join(input_path, os.path.basename(input_path) + ".log")
  if not os.path.exists(log_file_path):
    # If the log file does not exist, try using the input file name as the log file name.
    log_file_path = os.path.join(input_path, os.path.basename(input_path))
    if not os.path.exists(log_file_path):
      print("ERROR: Log file does not exist.")
      return

  # Read the log file content.
  with open(log_file_path, "r") as f:
    log_content = f.readlines()

  # Determine the archive type.
  archive_type = log_content[0].strip()

  # Process the archive based on the type.
  if archive_type == "SimpleArchive":
    process_simple_archive(input_path, log_content)
  elif archive_type == "MHA":
    process_mha_archive(input_path, log_content)
  elif archive_type == "StageContainer":
    process_stage_container_archive(input_path, log_content)
  else:
    print("ERROR: Unsupported archive type.")
    return

def process_simple_archive(input_path, log_content):
  """Processes a simple archive.

  Args:
    input_path: The path to the input file.
    log_content: The content of the log file.
  """

  # Get the output file name.
  output_file_name = log_content[1].strip()

  # Create the output directory if it does not exist.
  output_dir_path = os.path.join("output", output_file_name)
  if not os.path.exists(output_dir_path):
    os.makedirs(output_dir_path)

  # Open the output file.
  with open(os.path.join(output_dir_path, output_file_name), "wb") as f:
    # Write the number of entries.
    f.write(struct.pack("<I", int(log_content[2].strip())))

    # Write the file data for each entry.
    for i in range(3, len(log_content)):
      entry_name = log_content[i].strip()
      if entry_name != "null":
        entry_data = open(os.path.join(input_path, entry_name), "rb").read()
        f.write(entry_data)

def process_mha_archive(input_path, log_content):
  """Processes an MHA archive.

  Args:
    input_path: The path to the input file.
    log_content: The content of the log file.
  """

  # Get the output file name.
  output_file_name = log_content[1].strip()

  # Create the output directory if it does not exist.
  output_dir_path = os.path.join("output", output_file_name)
  if not os.path.exists(output_dir_path):
    os.makedirs(output_dir_path)

  # Open the output file.
  with open(os.path.join(output_dir_path, output_file_name), "wb") as f:
    # Write the MHA header.
    f.write(struct.pack("<I", 23160941))  # MHA magic
    f.write(struct.pack("<I", 0))  # pointerEntryMetaBlock
    f.write(struct.pack("<I", int(log_content[2].strip())))  # count
    f.write(struct.pack("<I", 0))  # pointerEntryNamesBlock
    f.write(struct.pack("<I", 0))  # entryNamesBlockLength
    f.write(struct.pack("<H", int(log_content[3].strip())))  # unk1
    f.write(struct.pack("<H", int(log_content[4].strip())))  # unk2

    # Write the entry names block.
    entry_names_block = io.BytesIO()
    for i in range(5, len(log_content)):
      entry_name = log_content[i].strip()
      entry_names_block.write(entry_name.encode("utf-8"))
      entry_names_block.write(b"\0")

    # Write the entry meta block.
    entry_meta_block = io.BytesIO()
    for i in range(5, len(log_content)):
      entry_name = log_content[i].strip()
      entry_data = open(os.path.join(input_path, entry_name), "rb").read()

      entry_meta_block.write(struct.pack("<I", entry_names_block.tell()))
      entry_meta_block.write(struct.pack("<I", len(entry_data)))
      entry_meta_block.write(struct.pack("<I", len(entry_data)))
      entry_meta_block.write(struct.pack("<I", 0))  # write psize if necessary
      entry_meta_block.write(struct.pack("<I", 0))  # file id

    # Write the entry data.
    f.write(entry_names_block.getvalue())
    f.write(entry_meta_block.getvalue())

    # Update the offsets.
    f.seek(4, io.SEEK_SET)
    f.write(struct.pack("<I", 0x18 + len(entry_names_block.getvalue())))
    f.write(struct.pack("<I", int(log_content[2].strip())))
    f.write(struct.pack("<I", 0x18))
    f.write(struct.pack("<I", len(entry_names_block.getvalue())))

def process_stage_container_archive(input_path, log_content):
  """Processes a Stage Container archive.

  Args:
    input_path: The path to the input file.
    log_content: The content of the log file.
  """

  # Get the output file name.
  output_file_name = log_content[1].strip()

  # Create the output directory if it does not exist.
  output_dir_path = os.path.join("output", output_file_name)
  if not os.path.exists(output_dir_path):
    os.makedirs(output_dir_path)

  # Write the temp dir.
  with open(os.path.join(output_dir_path, output_file_name), "wb") as f:
    temp_dir = bytearray(0 for _ in range((3 * 8 + int(log_content[5].strip()) * 0x0C + 8) & ~15))
    f.write(temp_dir)

    # Write the first three segments.
    offset = len(temp_dir)
    for i in range(0, 3):
      if log_content[i + 2].strip() != "null":
        entry_data = open(os.path.join(input_path, log_content[i + 2].strip()), "rb").read()

        f.seek(i * 0x08, io.SEEK_SET)
        f.write(struct.pack("<I", offset))
        f.write(struct.pack("<I", len(entry_data)))

        f.seek(offset, io.SEEK_SET)
        f.write(entry_data)

        offset += len(entry_data)

    # Write the rest of the segments.
    f.seek(3 * 0x08, io.SEEK_SET)
    f.write(struct.pack("<I", int(log_content[5].strip())))
    f.write(struct.pack("<I", int(log_content[6].strip())))

    for i in range(3, len(log_content)):
      if log_content[i].strip() != "null":
        entry_data = open(os.path.join(input_path, log_content[i].strip()), "rb").read()

        f.seek(3 * 0x08 + (i - 3) * 0x0C + 8, io.SEEK_SET)
        f.write(struct.pack("<I", offset))
        f.write(struct.pack("<I", len(entry_data)))
        f.write(struct.pack("<I", int(log_content[i + 6].strip())))

        f.seek(offset, io.SEEK_SET)
        f.write(entry_data)

        offset += len(entry_data)

def jpk_encode(atype, in_path, out_path, level):
  """Encodes a file using the JPK format.

  Args:
    atype: The type of JPK compression to use.
    in_path: The path to the input file.
    out_path: The path to the output file.
    level: The compression level to use (0-9).
  """

  # Create the output directory if it does not exist.
  if not os.path.exists("output"):
    os.makedirs("output")

  type = atype
  buffer = open(in_path, "rb").read()
  in_size = len(buffer)

  # Delete the output file if it exists.
  if os.path.exists(out_path):
    os.remove(out_path)

  # Create a file stream to the output file.
  fsot = open(out_path, "wb")

  # Create a binary writer to the file stream.
  br = io.BufferedWriter(fsot)

  # Write the header to the output file.
  br.write(struct.pack("<I", 0x1A524B4A))
  br.write(struct.pack("<H", 0x108))
  br.write(struct.pack("<H", type))
  br.write(struct.pack("<I", 0x10))
  br.write(struct.pack("<I", in_size))

  # Get the appropriate JPK encoder based on the type.
  encoder = None
  if type == 0:
    encoder = JPKEncodeRW()
  elif type == 2:
    #encoder = new JPKEncodeHFIRW();
    pass
  elif type == 3:
    encoder = JPKEncodeLz()
  elif type == 4:
    encoder = JPKEncodeHFI()

  # If an encoder was found, encode the file.
  if encoder is not None:
    start_time = datetime.datetime.now()
    encoder.process_on_encode(buffer, fsot, level, None)
    end_time = datetime.datetime.now()

    # Print the compression statistics.
    print(f"File compressed using type {type} (level {level / 100}): {fsot.tell()} bytes ({1 - (fsot.tell() / in_size):P} saved) in {(end_time - start_time).total_seconds()} seconds")

    # Close the file stream.
    fsot.close()
  else:
    print(f"Unsupported/invalid type: {type}")

    # Close the file stream.
    fsot.close()

    # Delete the output file.
    os.remove(out_path)