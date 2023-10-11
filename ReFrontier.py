import sys, os, io, re, threading
from Libraries import *
from Pack import *
from Unpack import *
from Crypto import *

recursive = True
create_log, repack, decrypt_only, no_decryption, encrypt, auto_close, clean_up, compress, ignore_jpk, stage_container, auto_stage, mhfup = False

def main():
    
    # Print the opening message.
    print_message("ReReFrontier by Brian_Z")

    # If the user has not provided any arguments, print the usage message and exit.
    if len(sys.argv) < 1:
        print_message("Usage: ReFrontier <file> (options)\n" +
                       "\nUnpacking Options:\n" +
                       "-log: Write log file (required for repacking)\n" +
                       "-cleanUp: Delete simple archives after unpacking\n" +
                       "-stageContainer: Unpack file as stage-specific container\n" +
                       "-autoStage: Automatically attempt to unpack containers that might be stage-specific\n" +
                       "-nonRecursive: Do not unpack recursively\n" +
                       "-decryptOnly: Decrypt ecd files without unpacking\n" +
                       "-noDecryption: Don't decrypt ecd files, no unpacking\n" +
                       "-ignoreJPK: Do not decompress JPK files\n" +
                       "\nPacking Options:\n" +
                       "-pack: Repack directory (requires log file)\n" +
                       "-compress [type],[level]: Pack file with jpk [type] at compression [level]\n" +
                       "-encrypt: Encrypt input file with ecd algorithm\n" +
                       "\nGeneral Options:\n" +
                       "-close: Close window after finishing process")
        sys.exit()

    input_file = sys.argv[1]
    create_log = sys.argv.count("-log") > 0
    recursive = sys.argv.count("-nonRecursive") == 0
    repack = sys.argv.count("-pack") > 0
    decrypt_only = sys.argv.count("-decryptOnly") > 0
    no_decryption = sys.argv.count("-noDecryption") > 0
    encrypt = sys.argv.count("-encrypt") > 0
    auto_close = sys.argv.count("-close") > 0
    clean_up = sys.argv.count("-cleanUp") > 0
    compress = sys.argv.count("-compress") > 0
    ignore_jpk = sys.argv.count("-ignoreJPK") > 0
    stage_container = sys.argv.count("-stageContainer") > 0
    auto_stage = sys.argv.count("-autoStage") > 0
    mhfup = sys.argv.count("-mhfup") > 0

    ## Check if the input file exists
    if not os.path.exists(input_file):
        print("ERROR: Input file does not exist.")
        sys.exit()

    ## If the input is a directory
    if os.path.isdir(input_file):

        ## If repacking or encrypting is not specified
        if not repack and not encrypt:

            ## Get a list of all the files in the input directory and its subdirectories
            input_files = os.listdir(input_file, recursive=True)

            ## If the `-mhfup` command-line argument is specified
            if mhfup:

                ## Create object to write to the mhfup.csv file
                text_output = open("mhfup.csv", "a", encoding="shift-jis", newline='\n')
                text_output.write("crc32,date1,date2,filename,lenght,0")

                ## Iterate over the input files and write their update entries to the mhfup.csv file
                for input_file in input_files:
                    text_output.write(GetUpdateEntry(input_file))

                ## Close the writing object
                text_output.close()

            ## Otherwise
            else:

                ## Process the input files
                ProcessMultipleLevels(input_files)

        ## If repacking is specified
        elif repack:

            ## Pack the input directory
            process_pack_input(input_file)

        ## If encrypting is specified
        elif compress:

            print("A directory was specified while in compression mode. Stopping.")
            sys.exit()

        ## If encrypting is specified
        elif encrypt:

            print("A directory was specified while in encryption mode. Stopping.")
            sys.exit()

    ## Otherwise, the input is a file
    else:

        ## If repacking or encrypting is not specified
        if not repack and not encrypt and not compress:

            ## Process the input file
            ProcessMultipleLevels([input_file])

        ## If repacking is specified
        elif repack:

            ## Print an error message and exit
            print("A single file was specified while in repacking mode. Stopping.")
            sys.exit()

        elif compress:
            try:
                ## Get the compress type and level from the command-line arguments
                pattern = r"-compress (\d+),(\d+)"
                match = re.match(pattern, " ".join(sys.argv[1:]))
                type = int(match.group(1))
                level = int(match.group(2)) * 100

                ## Compress the input file
                jpk_encode(type, input_file, os.path.basename(input_file), level)

            ## Otherwise, print an error message and exit
            except:
                print("ERROR: Check compress input. Example: -compress 3,50")
                sys.exit()

        ## If encrypting is specified
        elif encrypt:

            ## Open the input file and metadata file in binary mode
            with open(input_file, "rb") as f:
                buffer = f.read()

            with open(f"{input_file}.meta", "rb") as f:
                buffer_meta = f.read()

            ## Encrypt the input file
            buffer = encEcd(buffer, buffer_meta)

            ## Open the input file in binary mode and write the encrypted file back to it
            with open(input_file, "wb") as f:
                f.write(buffer)

            ## Print a message indicating that the file has been encrypted
            print_message("File encrypted.", False)

            ## Get the update entry for the encrypted file
            GetUpdateEntry(input_file)


def ProcessFile(input_file, create_log=False, clean_up=False, auto_stage=False, decrypt_only=False, ignore_jpk=False):
  """Processes a single file.

  Args:
    input_file: The path to the input file.
    create_log: Whether to create a log file for the processed file.
    clean_up: Whether to clean up the processed file.
    auto_stage: Whether to automatically stage the processed file.
    decrypt_only: Whether to only decrypt the file.
    ignore_jpk: Whether to ignore JKR files.
  """

  print(f"Processing {input_file}")

  # Read the file to memory.
  with open(input_file, "rb") as f:
    ms_input = io.BytesIO(f.read())
    br_input = io.BufferedReader(ms_input)

  # If the file is empty, skip it.
  if ms_input.length == 0:
    print("File is empty. Skipping.")
    return

  # Get the file magic number.
  file_magic = br_input.readint32()

  # If the file is a stage container, unpack it.
  if stage_container:
    br_input.seek(0, io.SEEK_SET)
    try:
      UnpackStageContainer(input_file, br_input, create_log, clean_up)
    except:
      pass

  # If the file has a MOMO header, unpack it as a simple archive.
  elif file_magic == 0x4F4D4F4D:
    print("MOMO Header detected.")
    UnpackSimpleArchive(input_file, br_input, 8, create_log, clean_up, auto_stage)

  # If the file has an ECD header, unpack it and decrypt it.
  elif file_magic == 0x1A646365:
    print("ECD Header detected.")

    # Decrypt the file.
    if not decrypt_only:
      buffer = os.path.getsize(input_file)
      data = br_input.read(buffer)
      decEcd(data)

      # Strip the ECD header from the file.
      ecd_header = data[:0x10]
      data_stripped = data[0x10:]

      # Write the stripped file back to disk.
      with open(input_file, "wb") as f:
        f.write(data_stripped)

      # Create a log file for the processed file.
      if create_log:
        with open(f"{input_file}.meta", "wb") as f:
          f.write(ecd_header)

      print("File decrypted.")

  # If the file has an EXF header, decrypt it.
  elif file_magic == 0x1A667865:
    print("EXF Header detected.")

    # Decrypt the file.
    buffer = os.path.getsize(input_file)
    data = br_input.read(buffer)
    decExf(data)

    # Write the decrypted file back to disk.
    with open(input_file, "wb") as f:
      f.write(data)

    print("File decrypted.")

  # If the file has a JKR header, unpack it.
  elif file_magic == 0x1A524B4A:
    print("JKR Header detected.")

    # Decompress the file.
    if not ignore_jpk:
      UnpackJPK(input_file)
      print("File decompressed.")

  # If the file has a MHA header, unpack it.
  elif file_magic == 0x0161686D:
    print("MHA Header detected.")
    UnpackMHA(input_file, br_input, create_log)

  # If the file is a MHF text file, print it out.
  elif file_magic == 0x000B0000:
    print("MHF Text file detected.")
    PrintFTXT(input_file, br_input)

# Otherwise, try to unpack the file as a simple archive.
  else:
    print("Trying to unpack as simple container...")

    br_input.seek(0, io.SEEK_SET)

    try:
        UnpackSimpleArchive(input_file, br_input, 4, create_log, clean_up, auto_stage)
    except:
        pass

    # If the file has an ECD header and we are not only decrypting,
    # recursively process the file again.
  if file_magic == 0x1A646365 and not decrypt_only:
    print("==============================")
    ProcessFile(input_file, create_log, clean_up, auto_stage, decrypt_only, ignore_jpk)
    return

  # Otherwise, print a separator line.
  else:
    print("==============================")

def ProcessMultipleLevels(input_files, patterns=["*.bin", "*.jkr", "*.ftxt", "*.snd"], recursive=True):
  """Processes a set of files and all subdirectories.

  Args:
    input_files: A list of file paths.
    patterns: A list of file patterns to match.
    recursive: Whether to process subdirectories.
  """

  # Current level
  for input_file in input_files:
    ProcessFile(input_file)

    # Disable stage processing files unpacked from parent
    stage_container = False

    # Process all successive levels
    if os.path.isdir(input_file) and recursive:
      directory = os.path.join(os.path.dirname(input_file), os.path.basename(input_file))
      subdirectory_files = []
      for pattern in patterns:
        for subdirectory_file in os.listdir(directory):
          if pattern.endswith(os.path.splitext(subdirectory_file)[1]):
            subdirectory_files.append(os.path.join(directory, subdirectory_file))
      ProcessMultipleLevels(subdirectory_files, patterns, recursive)

if __name__ == "__main__":
    main()