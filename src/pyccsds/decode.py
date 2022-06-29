"""Internal decoding routines."""
from __future__ import division
from collections import namedtuple, OrderedDict
import numpy as np

__author__ = 'Joey Mukherjee <joey@swri.org>'

# lots of this is based on ccsdspy from Daniel DaSilva but the bugs are mine!

def _create_field_meta(packet_nbytes, fields):
    body_nbytes = sum(field._bit_length for field in fields) // 8
    counter = (packet_nbytes - body_nbytes) * 8
    bit_offset = {}

    for i, field in enumerate(fields):
        if i == 0 and field._bit_offset is not None:
            # case: using bit_offset to fix the start position
            bit_offset[field._name] = field._bit_offset
            counter = field._bit_offset + field._bit_length
        elif field._bit_offset is None:
            # case: floating start position such that packet def fills to
            # to end of packet. What's missing is assumed to be header at the beginning.
            bit_offset[field._name] = counter
            counter += field._bit_length
        elif field._bit_offset < counter:
            # case: bit_offset specifying to backtrack. This condition
            # seems odd and unlikely. Eg. one or more bits of a packet overlap?
            bit_offset[field._name] = field._bit_offset
            # don't update counter unless the the overlap goes past counter
            counter = max(field._bit_offset + field._bit_length, counter)
        elif field._bit_offset >= counter:
            # case: otherwise, bit_offset is ahead of counter and we're skipping 
            # definition of 0 or more bits.
            bit_offset[field._name] = field._bit_offset
            counter = field._bit_offset + field._bit_length
        else:
            raise RuntimeError(("Unexpected case: could not compare"
                                " bit_offset {} with counter {} for field {}"
                                ).format(field._bit_offset, counter, field._name))

    if all(field._bit_offset is None for field in fields):
        assert counter == packet_nbytes * 8, \
            'Field definition != packet length'.format(n=counter-packet_nbytes*8)
    elif counter > packet_nbytes * 8:
        raise RuntimeError(("Packet definition larger than packet length"
                            " by {} bits").format(counter-(packet_nbytes*8)))
        
    # Setup metadata for each field, consiting of where to look for the field in
    # the file and how to parse it.
    FieldMeta = namedtuple('Meta', ['nbytes_file', 'start_byte_file',
                                    'nbytes_final', 'np_dtype'])
    field_meta = {}
    offset = 0
    for field in fields:
        nbytes_file = np.ceil(field._bit_length/8.).astype(int)  # the number of bytes the field takes up in the file

# add a byte from the file if we go over to the next character
        if (bit_offset[field._name] % 8 and bit_offset[field._name] % 8 + field._bit_length > 8):
            nbytes_file += 1

        nbytes_final = {3: 4, 5: 8, 6: 8, 7: 8}.get(nbytes_file, nbytes_file) # JM - the number of actual bytes in memory the variable takes up after all the masking is done

# JM - this calculation is wrong!  Or I don't know what he meant.
# changing this to the start byte of the file assuming we started at 0

        start_byte_file = offset // 8
        offset += field._bit_length

        # byte_order_symbol is only used to control float types here.
        #  - uint and int byte order are handled with byteswap later
        #  - fill is independent of byte order (all 1's)
        #  - byte order is not applicable to str types
        byte_order_symbol = "<" if field._byte_order == "little" else ">"
        np_dtype = {
            'uint': '>u%d' % nbytes_final,
            'int':  '>i%d' % nbytes_final,
            'fill': '>u%d' % nbytes_final,
            'float': '%sf%d' % (byte_order_symbol, nbytes_final),
            'str':   'S%d' % nbytes_final,
        }[field._data_type]
        
#        print ("Adding", field._name, nbytes_file, start_byte_file, nbytes_final, np_dtype)
        field_meta[field] = FieldMeta(
            nbytes_file, start_byte_file, nbytes_final, np_dtype)

    return bit_offset, field_meta

def _create_byte_arrays (file_bytes, packet_nbytes, field_meta, fields):

    # Create byte arrays for each field. At the end of this method they are left
    # as the numpy uint8 type.
    field_bytes = {}

    # Note: if only values of field._byte_order are big and little, then dont have to assign, just use the value as-is.
    #      Also, this could be moved into the 'for field in fields' loop but would they
    #      really change the byte order of a single field ?
    #      This flag just swaps byte order (not bit order). Perhaps can
    #       use: pwnlib.util.fiddling.bitswap(s)
    #            Reverses the bits in every byte of a given string.
    #            or a shift_rotate function.
    # big or little endian
    if fields[0]._byte_order == 'little':
       assert ("Can't handle that!")       # arr.byteswap(inplace=True)
       bigOrLittle = 'little'
    else:
       bigOrLittle = 'big'

    for field in fields:
        meta = field_meta[field]

        # Convert list of bytes into int: list[Nbytes_file bytes] -> python byte format -> int
        field_bytes[field._name] = int.from_bytes (bytes (file_bytes [meta.start_byte_file : meta.start_byte_file + meta.nbytes_file]), bigOrLittle)

    return field_bytes

def getSignedNumber(number, bitLength):
    mask = (2 ** bitLength) - 1
    if number & (1 << (bitLength - 1)):
        return number | ~mask
    else:
        return number & mask

def _process_byte_arrays (field_bytes, bit_offset, field_meta, fields):

    # Switch dtype of byte arrays to the final dtype, and apply masks and shifts
    # to interpret the correct bits.
    field_arrays = OrderedDict()

    for field in fields:
        meta = field_meta[field]
#        arr = field_bytes[field]
#        arr.dtype = meta.np_dtype

        if field._data_type in ('int', 'uint'):

           nbits_file = meta.nbytes_file * 8
           bit_end1   = bit_offset[field._name] + field._bit_length
           bit_power  = nbits_file - bit_offset[field._name]
           bit_shift  = nbits_file - bit_end1

# Use mask on number then shift right.
# This should work on any number of bits (as long as ones_bits long enough).
# actual_value = bytes-together & ( true mask of bits: bit_offset to bit_offset+bit_length-1 )

           actual_value  = field_bytes [field._name] & ( 2**bit_power-1 &  (0xffffffff << bit_shift) )

# Shift to the right to get just the masked number (was masked in place and may have trailing 0's)

           actual_value = actual_value >> bit_shift
           if field._data_type == 'int':
              actual_value = getSignedNumber (actual_value, field._bit_length)

        elif field._data_type == 'float':
           actual_value = float (field_bytes [field._name])
        else:
           actual_value = field_bytes [field._name]
        field_arrays[field._name] = actual_value

    return field_arrays

def _decode_packet(file_bytes, fields):
    """Decode a variable length APID.
    
    Parameters
    ----------
    file_bytes : array 
       A NumPy array of uint8 type, holding the bytes of the file to decode.
    fields : list of ccsdspy.interface.PacketField
       A list of fields, including the secondary header but excluding the
       primary header.

    Returns
    -------
    data: `OrderedDict`
       A dictionary mapping field names to NumPy arrays.
    """

    # Setup a dictionary mapping a bit offset to each field. It is assumed
    # that the `fields` array contains entries for the secondary header.
    packet_nbytes = file_bytes[4] * 256 + file_bytes[5] + 7
    
    bit_offset, field_meta = _create_field_meta (packet_nbytes, fields)
    field_bytes = _create_byte_arrays (file_bytes, packet_nbytes, field_meta, fields)
    field_arrays = _process_byte_arrays (field_bytes, bit_offset, field_meta, fields)

    return field_arrays
