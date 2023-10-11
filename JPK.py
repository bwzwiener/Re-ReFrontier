import io

class IJPKDecode:
  def ReadByte(self, s):
    """Reads a byte from the given stream.

    Args:
      s: A stream.

    Returns:
      A byte.
    """
    return s.read(1)[0]

  def ProcessOnDecode(self, in_stream, out_buffer):
    """Processes the given input stream and writes the output to the given buffer.

    Args:
      in_stream: An input stream.
      out_buffer: An output buffer.
    """
    pass




class ShowProgress:
  def __call__(self, perc):
    print(f"Progress: {perc}%")

class IJPKEncode:
  def WriteByte(self, s, b):
    """Writes a byte to the given stream.

    Args:
      s: A stream.
      b: A byte.
    """
    s.write(b)

  def ProcessOnEncode(self, in_buffer, out_stream, level=16, progress=None):
    """Processes the given input buffer and writes the output to the given stream.

    Args:
      in_buffer: An input buffer.
      out_stream: An output stream.
      level: The compression level.
      progress: A callback function that is called to show the progress of the encoding.
    """
    pass




class JPKDecodeLz(IJPKDecode):
  """A class for decoding JPK files using the LZ algorithm.

  This class implements the `IJPKDecode` interface and provides the `ProcessOnDecode()` method
  for decoding JPK files.

  Attributes:
    m_shiftIndex: The current shift index.
    m_flag: The current flag byte.
  """

  def __init__(self):
    self.m_shiftIndex = 0
    self.m_flag = 0

  def jpkcpy_lz(self, outBuffer, offset, length, outIndex):
    """Copies a length of bytes from the output buffer to the offset position.

    Args:
      outBuffer: A bytearray representing the output buffer.
      offset: The offset position to copy the bytes to.
      length: The number of bytes to copy.
      outIndex: A reference to the current index in the output buffer.

    Returns:
      None.
    """

    for i in range(length):
            outBuffer[outIndex] = outBuffer[outIndex - offset - 1]
            outIndex += 1

  def jpkbit_lz(self, s):
    """Reads a bit from the input stream.

    Args:
      s: A stream representing the input stream.

    Returns:
      A byte representing the bit read.
    """

    self.m_shiftIndex -= 1
    if self.m_shiftIndex < 0:
        self.m_shiftIndex = 7
        self.m_flag = self.ReadByte(s)

    return (self.m_flag >> self.m_shiftIndex) & 1

  def ProcessOnDecode(self, inStream, outBuffer):
    """Decodes the input stream into the output buffer using the LZ algorithm.

    Args:
      inStream: A stream representing the input stream.
      outBuffer: A bytearray representing the output buffer.

    Returns:
      None.
    """

    outIndex = 0
    while inStream.Position < inStream.Length and outIndex < len(outBuffer):
        if self.jpkbit_lz(inStream) == 0:
            outBuffer[outIndex] = self.ReadByte(inStream)
            outIndex += 1
            continue

        else:
            if self.jpkbit_lz(inStream) == 0:
                len = (self.jpkbit_lz(inStream) << 1) | self.jpkbit_lz(inStream)
                off = self.ReadByte(inStream)
                self.jpkcpy_lz(outBuffer, off, len + 3, outIndex)
                continue

            else:
                hi = self.ReadByte(inStream)
                lo = self.ReadByte(inStream)
                len = (hi & 0xE0) >> 5
                off = ((hi & 0x1F) << 8) | lo

                if len != 0:
                    self.jpkcpy_lz(outBuffer, off, len + 2, outIndex)
                    continue

                else:
                    if self.jpkbit_lz(inStream) == 0:
                        len = (self.jpkbit_lz(inStream) << 3) | (self.jpkbit_lz(inStream) << 2) | (self.jpkbit_lz(inStream) << 1) | self.jpkbit_lz(inStream)
                        self.jpkcpy_lz(outBuffer, off, len + 2 + 8, outIndex)
                        continue

                    else:
                        temp = self.ReadByte(inStream)
                        if temp == 0xFF:
                            for i in range(off + 0x1B):
                                outBuffer[outIndex] = self.ReadByte(inStream)
                                outIndex += 1
                            continue

                        else:
                            self.jpkcpy_lz(outBuffer, off, temp + 0x1A, outIndex)
                            continue
    
  def ReadByte(self, s):
    """Reads a byte from the input stream.

    Args:
      s: A stream representing the input stream.

    Returns:
      A byte representing the byte read.
    """

    value = s.ReadByte()
    if value < 0:
      raise Exception()
    return 0xff & value



class JPKEncodeLz(IJPKEncode):
  """A class for encoding JPK files using the LZ algorithm.

  This class implements the `IJPKEncode` interface and provides the `ProcessOnEncode()` method
  for encoding JPK files.

  Attributes:
    m_flag: The current flag byte.
    m_shiftIndex: The current shift index.
    m_ind: The current index in the input buffer.
    m_inp: The input buffer.
    m_level: The compression level.
    m_maxdist: The maximum distance.
    m_outstream: The output stream.
    m_towrite: A bytearray to store the bytes to be written to the output stream.
    m_itowrite: The number of bytes in the `m_towrite` bytearray.
  """

  def __init__(self):
    self.m_flag = 0
    self.m_shiftIndex = 8
    self.m_ind = 0
    self.m_inp = None
    self.m_level = 1000
    self.m_maxdist = 0x1fff
    self.m_outstream = None
    self.m_towrite = bytearray(1000)
    self.m_itowrite = 0

  def FindRep(self, ind, ofs):
    """Finds a repeating pattern in the input buffer.

    Args:
      ind: The current index in the input buffer.
      ofs: A reference to the output offset.

    Returns:
      The length of the repeating pattern, or 0 if no repeating pattern is found.
    """

    nlen = min(self.m_level, len(self.m_inp) - ind)
    ofs.value = 0

    if ind == 0 or nlen < 3:
      return 0

    ista = ind if ind < self.m_maxdist else ind - self.m_maxdist

    with io.BytesIO(self.m_inp) as inp:
      psta = inp.read(ista)
      pcur = inp.read(ind)
      len = 0

      while psta < pcur:
        lenw = 0
        pfin = psta + nlen

        for i in range(len(psta)):
          pb = psta[i]
          pb2 = pcur[i]
          if pb != pb2:
            break
          lenw += 1

        if lenw > len and lenw >= 3:
          len = lenw
          ofs.value = pcur - psta - 1

          if len >= nlen:
            break

        psta = inp.read(1)

    return len

  def flushflag(self, final):
    """Flushes the current flag to the output stream.

    Args:
      final: Whether this is the final flush.
    """

    if not final or self.m_itowrite > 0:
      self.WriteByte(self.m_outstream, self.m_flag)

    self.m_flag = 0

    for i in range(self.m_itowrite):
      self.WriteByte(self.m_outstream, self.m_towrite[i])

    self.m_itowrite = 0

  def SetFlag(self, b):
    """Sets a bit in the current flag.

    Args:
      b: The bit to set.
    """

    self.m_shiftIndex -= 1

    if self.m_shiftIndex < 0:
      self.m_shiftIndex = 7
      self.flushflag(False)

    self.m_flag |= b << self.m_shiftIndex

  def SetFlagsL(self, b, cnt):
    """Sets multiple bits in the current flag.

    Args:
      b: The byte containing the bits to set.
      cnt: The number of bits to set.
    """

    for i in range(cnt - 1, -1, -1):
      self.SetFlag((b >> i) & 1)
    
  def ProcessOnEncode(self, inBuffer, outStream, level=1000, showProgress=None):
    """Encodes the input buffer to the output stream using the LZ algorithm.

    Args:
        inBuffer: A bytearray containing the input data.
        outStream: A stream to write the encoded data to.
        level: The compression level.
        showProgress: A callback function to show the progress of the encoding.

    Returns:
        None.
    """

    self.m_inp = inBuffer
    self.m_outstream = outStream
    self.m_level = level

    perc = 0
    perc0 = 0
    percbord = 0

    if showProgress:
        showProgress(perc)

    while self.m_ind < len(inBuffer):
        perc = percbord + (100 - percbord) * self.m_ind / len(inBuffer)

        if perc > perc0:
            perc0 = perc
            if showProgress:
                showProgress(perc)

        ofs = io.BytesIO()
        len = self.FindRep(self.m_ind, ofs)

        if len == 0:
            self.SetFlag(0)
            self.m_towrite[self.m_itowrite] = inBuffer[self.m_ind]
            self.m_itowrite += 1
            self.m_ind += 1

        else:
            self.SetFlag(1)

            if len <= 6 and ofs.value <= 0xff:
                self.SetFlag(0)
                self.SetFlagsL((len - 3), 2)
                self.m_towrite[self.m_itowrite] = ofs.value
                self.m_itowrite += 1
                self.m_ind += len

            else:
                self.SetFlag(1)
                u16 = ofs.value
                hi = (u16 >> 8) & 0xff
                lo = u16 & 0xff

                if len <= 9:
                    u16 |= (len - 2) << 13

                self.m_towrite[self.m_itowrite] = hi
                self.m_itowrite += 1
                self.m_towrite[self.m_itowrite] = lo
                self.m_itowrite += 1
                self.m_ind += len

                if len > 9:
                    if len <= 25:
                        self.SetFlag(0)
                        self.SetFlagsL((len - 10), 4)

                    else:
                        self.SetFlag(1)
                        self.m_towrite[self.m_itowrite] = len - 0x1a
                        self.m_itowrite += 1

    self.flushflag(True)

    if showProgress:
        showProgress(100)

  def WriteByte(self, s, b):
    """Writes a byte to the stream.

    Args:
        s: The stream to write to.
        b: The byte to write.

    Returns:
        None.
    """

    s.write(bytes([b]))



class JPKDecodeHFI(JPKDecodeLz):
  """A class for decoding JPK files using the LZ algorithm with Huffman coding.

  This class inherits from the `JPKDecodeLz` class and overrides the `ProcessOnDecode()` and `ReadByte()` methods
  to support Huffman coding.

  Attributes:
    m_flagHF: The current flag byte for Huffman coding.
    m_flagShift: The current flag shift for Huffman coding.
    m_hfTableOffset: The offset of the Huffman table in the stream.
    m_hfDataOffset: The offset of the Huffman data in the stream.
    m_hfTableLen: The length of the Huffman table.
  """

  def __init__(self):
    super().__init__()

    self.m_flagHF = 0
    self.m_flagShift = 0
    self.m_hfTableOffset = 0
    self.m_hfDataOffset = 0
    self.m_hfTableLen = 0

  def ProcessOnDecode(self, inStream, outBuffer):
    """Decodes the input stream to the output buffer using the LZ algorithm with Huffman coding.

    Args:
      inStream: A stream containing the input data.
      outBuffer: A bytearray to write the decoded data to.

    Returns:
      None.
    """

    br = io.BinaryReader(inStream)
    self.m_hfTableLen = br.read_int16()
    self.m_hfTableOffset = inStream.tell()
    self.m_hfDataOffset = self.m_hfTableOffset + self.m_hfTableLen * 4 - 0x3fc

    super().ProcessOnDecode(inStream, outBuffer)

  def ReadByte(self, s):
    """Reads a byte from the stream using Huffman coding.

    Args:
      s: A stream containing the input data.

    Returns:
      A byte representing the byte read.
    """

    data = self.m_hfTableLen
    br = io.BinaryReader(s)

    while data >= 0x100:
      self.m_flagShift -= 1
      if self.m_flagShift < 0:
        self.m_flagShift = 7
        s.seek(self.m_hfDataOffset)
        self.m_flagHF = br.read_byte()

      bit = (self.m_flagHF >> self.m_flagShift) & 0x1
      s.seek((data * 2 - 0x200 + bit) * 2 + self.m_hfTableOffset)
      data = br.read_int16()

    return 0xff & data
  


class JPKEncodeHFI(JPKEncodeLz):
  """A class for encoding JPK files using the LZ algorithm with Huffman coding.

  This class inherits from the `JPKEncodeLz` class and overrides the `ProcessOnEncode()`, `WriteByte()`, and `WriteBit()` methods
  to support Huffman coding.

  Attributes:
    m_bits: The current bit buffer.
    m_bitcount: The number of bits in the current bit buffer.
  """

  def __init__(self):
    super().__init__()

    self.m_bits = 0
    self.m_bitcount = 0

  def ProcessOnEncode(self, inBuffer, outStream, level=16, showProgress=None):
    """Encodes the input buffer to the output stream using the LZ algorithm with Huffman coding.

    Args:
      inBuffer: A bytearray containing the input data.
      outStream: A stream to write the encoded data to.
      level: The compression level.
      showProgress: A callback function to show the progress of the encoding.

    Returns:
      None.
    """

    self.FillTable()
    br = io.BufferedWriter(outStream)
    br.write(self.m_hfTableLen.to_bytes(2, 'big'))
    for i in range(self.m_hfTableLen):
      br.write(self.m_hfTable[i].to_bytes(1, 'big'))

    super().ProcessOnEncode(inBuffer, outStream, level, showProgress)
    self.FlushWrite(outStream)
    br.flush()

  def WriteBit(self, s, b):
    """Writes a bit to the stream.

    Args:
      s: A stream to write to.
      b: The bit to write.

    Returns:
      None.
    """

    if self.m_bitcount == 8:
      s.write(self.m_bits.to_bytes(1, 'big'))
      self.m_bits = 0
      self.m_bitcount = 0

    self.m_bits <<= 1
    self.m_bits |= b
    self.m_bitcount += 1

  def WriteBits(self, s, bits, len):
    """Writes multiple bits to the stream.

    Args:
      s: A stream to write to.
      bits: The bits to write.
      len: The number of bits to write.

    Returns:
      None.
    """

    while len > 0:
      len -= 1
      self.WriteBit(s, (bits >> len) & 1)

  def FlushWrite(self, s):
    """Flushes the current bit buffer to the stream.

    Args:
      s: A stream to write to.

    Returns:
      None.
    """

    if self.m_bitcount > 0:
      self.m_bits <<= (8 - self.m_bitcount)
      s.write(self.m_bits.to_bytes(1, 'big'))

  def WriteByte(self, s, b):
    """Writes a byte to the stream using Huffman coding.

    Args:
      s: A stream to write to.
      b: The byte to write.

    Returns:
      None.
    """

    bits = self.m_Paths[b]
    len = self.m_Lengths[b]
    self.WriteBits(s, bits, len)




class JPKDecodeHFIRW(JPKDecodeHFI):
  """A class for decoding JPK files using the LZ algorithm with Huffman coding, using a read-write stream."""

  def ProcessOnDecode(self, inStream, outBuffer):
    """Decodes the input stream to the output buffer using the LZ algorithm with Huffman coding.

    Args:
      inStream: A stream containing the input data.
      outBuffer: A bytearray to write the decoded data to.

    Returns:
      None.
    """

    index = 0
    while index < len(outBuffer):
      outBuffer[index] = super().ReadByte(inStream)
      index += 1



class JPKEncodeHFIRW(JPKEncodeHFI):
  """A class for encoding JPK files using the LZ algorithm with Huffman coding, using a read-write stream."""

  def ProcessOnEncode(self, inBuffer, outStream, level=16, showProgress=None):
    """Encodes the input buffer to the output stream using the LZ algorithm with Huffman coding.

    Args:
      inBuffer: A bytearray containing the input data.
      outStream: A stream to write the encoded data to.
      level: The compression level.
      showProgress: A callback function to show the progress of the encoding.

    Returns:
      None.
    """

    pass



class JPKDecodeRW(IJPKDecode):
  """A class for decoding JPK files, using a read-write stream."""

  def ProcessOnDecode(self, inStream, outBuffer):
    """Decodes the input stream to the output buffer.

    Args:
      inStream: A stream containing the input data.
      outBuffer: A bytearray to write the decoded data to.

    Returns:
      None.
    """

    index = 0
    while inStream.tell() < inStream.length and index < len(outBuffer):
      outBuffer[index] = self.ReadByte(inStream)
      index += 1

  def ReadByte(self, s):
    """Reads a byte from the stream.

    Args:
      s: A stream to read from.

    Returns:
      A byte representing the byte read.
    """

    value = s.read(1)
    if value is None:
      raise NotImplementedError()

    return value[0]



class JPKEncodeRW(IJPKEncode):
  """A class for encoding JPK files, using a read-write stream."""

  def ProcessOnEncode(self, inBuffer, outStream, level=16, showProgress=None):
    """Encodes the input buffer to the output stream.

    Args:
      inBuffer: A bytearray containing the input data.
      outStream: A stream to write the encoded data to.
      level: The compression level.
      showProgress: A callback function to show the progress of the encoding.

    Returns:
      None.
    """

    perc, perc0 = 0, 0
    if showProgress is not None:
      showProgress(perc)

    for iin in range(len(inBuffer)):
      perc = int(100 * iin / len(inBuffer))
      if perc > perc0:
        perc0 = perc
        if showProgress is not None:
          showProgress(perc)

      self.WriteByte(outStream, inBuffer[iin])

    if showProgress is not None:
      showProgress(100)

  def WriteByte(self, s, b):
    """Writes a byte to the stream.

    Args:
      s: A stream to write to.
      b: The byte to write.

    Returns:
      None.
    """

    s.write(bytes([b]))