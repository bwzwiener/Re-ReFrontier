import binascii

def LoadUInt32BE(buffer, offset):
  """Loads a 32-bit unsigned integer from a buffer in big-endian format.

  Args:
    buffer: A byte buffer.
    offset: The offset in the buffer to start loading from.

  Returns:
    A 32-bit unsigned integer.
  """

  value = (buffer[offset] << 24) | (buffer[offset + 1] << 16) | (buffer[offset + 2] << 8) | buffer[offset + 3]
  return value

# From addr 0x10292DCC
rndBufEcd = bytearray([0x4A, 0x4B, 0x52, 0x2E, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x0D,
                       0xCD, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x0D, 0xCD, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x0D, 0xCD,
                       0x00, 0x00, 0x00, 0x01, 0x00, 0x19, 0x66, 0x0D, 0x00, 0x00, 0x00, 0x03, 0x7D, 0x2B, 0x89, 0xDD, 0x00,
                       0x00, 0x00, 0x01])

# From addr 0x1025F4E0
rndBufExf = bytearray([0x4A, 0x4B, 0x52, 0x2E, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x0D,
                       0xCD, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x0D, 0xCD, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x0D, 0xCD,
                       0x00, 0x00, 0x00, 0x01, 0x02, 0xE9, 0x0E, 0xDD, 0x00, 0x00, 0x00, 0x03])

def getRndEcd(index, rnd):
    """Generates a random number using the ECD random number generator.

    Args:
        index: The index of the random number to generate.
        rnd: The current seed value.

    Returns:
        A 32-bit unsigned integer.
    """

    rnd = rnd * LoadUInt32BE(rndBufEcd, 8 * index) + LoadUInt32BE(rndBufEcd, 8 * index + 4)
    return rnd


def CreateXorkeyExf(header):
  """Creates an XOR key for the ECD decryptor.

  Args:
    header: The header of the encrypted file.

  Returns:
    A 16-byte byte array.
  """

  keyBuffer = bytearray(16)
  index = int.from_bytes(header[4:6], "big")
  tempVal = int.from_bytes(header[12:16], "big")
  value = int.from_bytes(header[12:16], "big")

  for i in range(4):
    tempVal = tempVal * LoadUInt32BE(rndBufExf, index * 8) + LoadUInt32BE(rndBufExf, index * 8 + 4)
    key = tempVal ^ value
    tempKey = key.to_bytes(4, "big")
    keyBuffer.extend(tempKey)

  return keyBuffer

def decEcd(buffer):
  """Decrypts a file encrypted using the ECD algorithm.

  Args:
    buffer: A byte buffer containing the encrypted file.
  """

  fsize = int.from_bytes(buffer[8:12], "big")
  crc32 = int.from_bytes(buffer[12:16], "big")
  index = int.from_bytes(buffer[4:6], "big")
  rnd = (crc32 << 16) | (crc32 >> 16) | 1

  xorpad = getRndEcd(index, rnd)
  r8 = xorpad

  for i in range(fsize):
    xorpad = getRndEcd(index, rnd)

    data = buffer[0x10 + i]
    r11 = data ^ r8
    r12 = (r11 >> 4) & 0xFF

    for j in range(8):
      r10 = xorpad ^ r11
      r11 = r12
      r12 = (r12 ^ r10) & 0xFF
      xorpad >>= 4

    r8 = (r12 & 0xF) | ((r11 & 0xF) << 4)
    buffer[0x10 + i] = r8

def encEcd(buffer, bufferMeta):
  """Encrypts a file using the ECD algorithm.

  Args:
    buffer: A byte buffer containing the file to be encrypted.
    bufferMeta: A byte buffer containing the metadata for the encrypted file.

  Returns:
    A byte buffer containing the encrypted file.
  """

  # Update meta data
  fsize = len(buffer)
  crc32w = binascii.crc32(buffer)
  index = int.from_bytes(bufferMeta[4:6], "big")

  # Write meta data
  buf = bytearray(16 + fsize)
  buf.extend(bufferMeta)
  buf.extend(fsize.to_bytes(4, "big"))
  buf.extend(crc32w.to_bytes(4, "big"))

  # Fill data with nullspace
  for i in range(16 + fsize, len(buf)):
    buf[i] = 0

  # Encrypt data
  rnd = (crc32w << 16) | (crc32w >> 16) | 1
  xorpad = getRndEcd(index, rnd)
  r8 = xorpad

  for i in range(fsize):
    xorpad = getRndEcd(index, rnd)
    data = buffer[i]
    r11 = 0
    r12 = 0

    for j in range(8):
      r10 = xorpad ^ r11
      r11 = r12
      r12 ^= r10
      r12 &= 0xFF
      xorpad >>= 4

    dig2 = data
    dig1 = (dig2 >> 4) & 0xFF
    dig1 ^= r11
    dig2 ^= r12
    dig1 ^= dig2

    rr = (dig2 & 0xF) | ((dig1 & 0xF) << 4)
    rr ^= r8
    buf[16 + i] = rr
    r8 = data

  return buf

def decExf(buffer):
  """Decrypts a file encrypted using the EXF algorithm.

  Args:
    buffer: A byte buffer containing the encrypted file.
  """

  header = buffer[:16]
  if int.from_bytes(header[:4], "big") == 0x1a667865:
    keybuf = CreateXorkeyExf(header)
    for i in range(16, len(buffer) - len(header)):
      r28 = i - 0x10
      r8 = buffer[i]
      index = r28 & 0xf
      r4 = r8 ^ r28
      r12 = keybuf[index]
      r0 = (r4 & 0xf0) >> 4
      r7 = keybuf[r0]
      r9 = r4 >> 4
      r5 = r7 >> 4
      r9 ^= r12
      r26 = r5 ^ r4
      r26 = (r26 & ~0xf0) | ((r9 & 0xf) << 4)
      buffer[i] = r26