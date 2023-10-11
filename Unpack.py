import io
import os
from Libraries import *
from JPK import *

import io
import os

def UnpackSimpleArchive(input, brInput, magicSize, createLog=True, cleanUp=True, autoStage=True):
  """Unpacks a simple archive.

  Args:
    input: The path to the simple archive to unpack.
    brInput: A binary reader to read the simple archive from.
    magicSize: The size of the magic number at the beginning of the simple archive.
    createLog: Whether to create a log file.
    cleanUp: Whether to clean up the input file and output directory after unpacking.
    autoStage: Whether to automatically unpack the simple archive as a stage container if it is detected as one.

  Returns:
    None.
  """

  fileInfo = os.path.FileInfo(input)
  outputDir = f"{fileInfo.directory_path}\\{fileInfo.stem}"

  # Abort if too small
  if fileInfo.length < 12:
    print("File is too small. Skipping.")
    return

  count = brInput.read_uint32()

  # Calculate complete size of extracted data to avoid extracting plausible files that aren't archives
  completeSize = magicSize
  try:
    for i in range(count):
      brInput.seek(magicSize, io.SEEK_CUR)
      entrySize = brInput.read_int32()
      completeSize += entrySize
  except:
    print("Caught file-based error during simple container check.")

  # Very fragile check for stage container
  brInput.seek(4, io.SEEK_SET)
  checkUnk = brInput.read_int32()
  checkZero = brInput.read_int64()
  if checkUnk < 9999 and checkZero == 0:
    if autoStage:
      brInput.seek(0, io.SEEK_SET)
      UnpackStageContainer(input, brInput, createLog, cleanUp)
      return

    print(f"Skipping. Not a valid simple container, but could be stage-specific. Try:\nReFrontier.exe {fileInfo.full_path} -stageContainer")
    return

  if completeSize > fileInfo.length or count == 0 or count > 9999:
    print("Skipping. Not a valid simple container.")
    return

  print("Trying to unpack as generic simple container.")
  brInput.seek(magicSize, io.SEEK_SET)

  # Write to log file if desired; needs some other solution because it creates useless logs even if !createLog
  os.makedirs(outputDir, exist_ok=True)
  logOutput = open(f"{outputDir}\\{fileInfo.stem}.log", "w")
  if createLog:
    logOutput.write("SimpleArchive\n")
    logOutput.write(input[input.rfind("\\") + 1:] + "\n")
    logOutput.write(str(count) + "\n")

  for i in range(count):
    entryOffset = brInput.read_int32()
    entrySize = brInput.read_int32()

    # Skip if size is zero
    if entrySize == 0:
      print(f"Offset: 0x{entryOffset:08X}, Size: 0x{entrySize:08X} (SKIPPED)")
      if createLog:
        logOutput.write("null,{entryOffset},{entrySize},0\n")
      continue

    # Read file to array
    brInput.seek(entryOffset, io.SEEK_SET)
    entryData = brInput.read(entrySize)

    # Check file header and get extension
    header = bytes([entryData[0], entryData[1], entryData[2], entryData[3]])
    headerInt = int.from_bytes(header, 'big')
    extension = Enum.GetName(Extensions, headerInt)
    if extension is None:
      extension = CheckForMagic(headerInt, entryData)
    if extension is None:
      extension = "bin"

    # Print info
    print(f"Offset: 0x{entryOffset:08X}, Size: 0x{entrySize:08X} ({extension})")
    if createLog:
      logOutput.write(f'{(i + 1).ToString("D4")}_{entryOffset.ToString("X8")}.{extension},{entryOffset},{entrySize},{headerInt}\n')

    # Extract file
    with open(f'{outputDir}\\{(i + 1).ToString("D4")}_{entryOffset.ToString("X8")}.{extension}', "wb") as f:
      f.write(entryData)

    # Move to next entry block
    brInput.seek(magicSize + (i + 1) * 0x08, io.SEEK_SET)

    # Cut off after 1000 entries
    if i == 999:
      print("Cutting off after 1000 entries")
      break

  # Clean up
  logOutput.close()
  if not createLog:
    os.remove(f"{outputDir}\\{fileInfo.stem}.log")
  if cleanUp:
    os.remove(input)
    #if (Directory.GetFiles(outputDir) == null) Directory.Delete(outputDir);

def UnpackMHA(input, brInput, createLog=True):
  """Unpacks an MHA archive.

  Args:
    input: The path to the MHA archive to unpack.
    brInput: A binary reader to read the MHA archive from.
    createLog: Whether to create a log file.

  Returns:
    None.
  """

  fileInfo = os.path.FileInfo(input)
  outputDir = f"{fileInfo.directory_path}\\{fileInfo.stem}"
  os.makedirs(outputDir, exist_ok=True)

  logOutput = open(f"{outputDir}\\{fileInfo.stem}.log", "w")
  if createLog:
    logOutput.write("MHA\n")
    logOutput.write(input[input.rfind("\\") + 1:] + "\n")

  # Read header
  pointerEntryMetaBlock = brInput.read_int32()
  count = brInput.read_int32()
  pointerEntryNamesBlock = brInput.read_int32()
  entryNamesBlockLength = brInput.read_int32()
  unk1 = brInput.read_int16()
  unk2 = brInput.read_int16()
  if createLog:
    logOutput.write(str(count) + "\n")
    logOutput.write(str(unk1) + "\n")
    logOutput.write(str(unk2) + "\n")

  # File Data
  for i in range(count):
    # Get meta
    brInput.seek(pointerEntryMetaBlock + i * 0x14)
    stringOffset = brInput.read_int32()
    entryOffset = brInput.read_int32()
    entrySize = brInput.read_int32()
    pSize = brInput.read_int32()  # Padded size
    fileId = brInput.read_int32()

    # Get name
    brInput.seek(pointerEntryNamesBlock + stringOffset)
    entryName = ReadNullTerminatedString(brInput, "utf-8")
    if createLog:
      logOutput.write(entryName + "," + str(fileId) + "\n")

    # Extract file
    brInput.seek(entryOffset)
    entryData = brInput.read(entrySize)
    with open(f"{outputDir}\\{entryName}", "wb") as f:
      f.write(entryData)

    print(f"{entryName}, String Offset: 0x{stringOffset:08X}, Offset: 0x{entryOffset:08X}, Size: 0x{entrySize:08X}, pSize: 0x{pSize:08X}, File ID: 0x{fileId:08X}")

  logOutput.close()
  if not createLog:
    os.remove(f"{outputDir}\\{fileInfo.stem}.log")



def UnpackJPK(input_file):
  """Unpacks a JPK file.

  Args:
    input_file: The path to the input JPK file.
  """

  buffer = open(input_file, "rb").read()
  ms = io.BytesIO(buffer)
  br = io.BufferedReader(ms)

  # Check the magic number.
  if br.readuint32() != 0x1A524B4A:
    return

  # Read the JPK type.
  ms.seek(0x2, io.SEEK_CUR)
  type = br.readuint16()
  print(f"JPK Type: {type}")

  # Select the appropriate decoder based on the JPK type.
  decoder = None
  if type == 0:
    decoder = JPKDecodeRW()
  elif type == 2:
    decoder = JPKDecodeHFIRW()
  elif type == 3:
    decoder = JPKDecodeLz()
  elif type == 4:
    decoder = JPKDecodeHFI()

  # If a decoder was selected, decompress the file.
  if decoder is not None:
    # Read the start offset and output size.
    start_offset = br.readint32()
    out_size = br.readint32()

    # Create a buffer to store the decompressed data.
    out_buffer = bytearray(out_size)

    # Seek to the start of the compressed data.
    ms.seek(start_offset, io.SEEK_SET)

    # Decompress the data.
    decoder.ProcessOnDecode(ms, out_buffer)

    # Get the extension of the decompressed file.
    extension = None
    header = out_buffer[:4]
    header_int = int.from_bytes(header, byteorder="big")
    if header_int in Extensions:
      extension = Extensions(header_int)
    elif CheckForMagic(header_int, out_buffer) is not None:
      extension = CheckForMagic(header_int, out_buffer)
    else:
      extension = "bin"

    # Get the output path for the decompressed file.
    file_info = os.path.splitext(input_file)
    directory = file_info[0]
    filename = file_info[1]
    output_path = f"{directory}/{filename}.{extension}"

    # Delete the input file.
    os.remove(input_file)

    # Write the decompressed data to the output file.
    open(output_path, "wb").write(out_buffer)

  # Close the BinaryReader and MemoryStream objects.
  br.close()
  ms.close()



def UnpackStageContainer(input_file, br_input, create_log=True, clean_up=True):
  """Unpacks a stage container file.

  Args:
    input_file: The path to the input stage container file.
    br_input: A BinaryReader object for the input file.
    create_log: Whether to create a log file for the unpacked files.
    clean_up: Whether to delete the input file after unpacking.
  """

  # Create a directory to store the unpacked files.
  file_info = os.path.splitext(input_file)
  output_dir = f"{file_info[0]}/{file_info[1][:-len('.stage')]}"
  os.makedirs(output_dir, exist_ok=True)

  # Create a log file if desired.
  if create_log:
    log_file = open(f"{output_dir}/{file_info[1][:-len('.stage')]}.log", "w")
    log_file.write("StageContainer\n")
    log_file.write(input_file.split("/")[-1] + "\n")

  # Unpack the first three segments.
  for i in range(3):
    offset = br_input.readint32()
    size = br_input.readint32()

    if size == 0:
      print(f"Offset: 0x{offset:08X}, Size: 0x{size:08X} (SKIPPED)")
      if create_log:
        log_file.write("null,{},0\n".format(offset))
      continue

    br_input.seek(offset, io.SEEK_SET)
    data = br_input.read(size)

    # Get the file extension.
    header = data[:4]
    header_int = int.from_bytes(header, "big")
    extension = Extensions(header_int) if header_int in Extensions else CheckForMagic(header_int, data) or "bin"

    # Print information about the file.
    print(f"Offset: 0x{offset:08X}, Size: 0x{size:08X} ({extension})")
    if create_log:
      log_file.write(f"{i + 1:04d}_{offset:08X}.{extension},{offset},{size},{header_int}\n")

    # Write the file to disk.
    with open(f"{output_dir}/{i + 1:04d}_{offset:08X}.{extension}", "wb") as f:
      f.write(data)

  # Unpack the remaining segments.
  rest_count = br_input.readint32()
  unk_header = br_input.readint32()
  if create_log:
    log_file.write(f"{rest_count},{unk_header}\n")

  for i in range(rest_count):
    offset = br_input.readint32()
    size = br_input.readint32()
    unk = br_input.readint32()

    if size == 0:
      print(f"Offset: 0x{offset:08X}, Size: 0x{size:08X}, Unk: 0x{unk:08X} (SKIPPED)")
      if create_log:
        log_file.write("null,{},0\n".format(offset))
      continue

    br_input.seek(offset, io.SEEK_SET)
    data = br_input.read(size)

    # Get the file extension.
    header = data[:4]
    header_int = int.from_bytes(header, "big")
    extension = Extensions(header_int) if header_int in Extensions else CheckForMagic(header_int, data) or "bin"

    # Print information about the file.
    print(f"Offset: 0x{offset:08X}, Size: 0x{size:08X}, Unk: 0x{unk:08X} ({extension})")
    if create_log:
      log_file.write(f"{i + 4:04d}_{offset:08X}.{extension},{offset},{size},{unk},{header_int}")

    # Write the file to disk.
    with open(f"{output_dir}/{i + 4:04d}_{offset:08X}.{extension}", "wb") as f:
      f.write(data)

  # Clean up.
  log_file.close()
  if not create_log:
    os.remove(f"{output_dir}/{file_info[1][:-len('.stage')]}.log")
  if clean_up:
    os.remove(input_file)



def PrintFTXT(input_file, br_input):
  """Prints an FTXT file to the console.

  Args:
    input_file: The path to the input file.
    br_input: A BinaryReader object for the input file.
  """

  # Get the directory and filename of the input file.
  file_info = os.path.splitext(input_file)
  directory = file_info[0]
  filename = file_info[1]

  # Get the output path for the text file.
  output_path = f"{directory}/{filename}.txt"

  # If the output file already exists, delete it.
  if os.path.exists(output_path):
    os.remove(output_path)

  # Create a StreamWriter object for the output file.
  txt_output = io.TextIOWrapper(open(output_path, "w", encoding="shift-jis"))

  # Read the header of the FTXT file.
  br_input.read(10)
  string_count = br_input.readint16()
  text_block_size = br_input.readint32()

  # For each string in the FTXT file, read it and write it to the output file.
  for i in range(string_count):
    string = ReadNullTerminatedString(br_input)
    txt_output.write(string.replace("\n", "<NEWLINE>"))

  # Close the StreamWriter object.
  txt_output.close()