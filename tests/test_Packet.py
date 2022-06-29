from src.pyccsds.interface import Packet, PacketField
import numpy as np

def test_Packet():

    my_fields = []
    my_fields.append (PacketField(name='HDR_VER', data_type='uint', bit_offset=0, bit_length=3))
    my_fields.append (PacketField(name='HDR_TYPE', data_type='uint', bit_offset=3, bit_length=1))

    new_packet = Packet (my_fields)

    # Since pytest captures the stdout from individual tests and displays them 
    # only on certain conditions, this output will only show up IF we call pytest 
    # with the -rP option since output is not displayed for tests that pass.

    print_fields = new_packet._packets
    for fields in print_fields:
        print (repr(fields))
