from pyccsds.interface import PacketField

def test_PacketField():

    new_obj = PacketField(name='HDR_VER', data_type='uint', bit_offset=0, bit_length=3)
    assert new_obj._name == "HDR_VER"

def test_PacketFieldBadTypeNameArgument():

    new_obj1 = PacketField(name=25, data_type='uint', bit_offset=0, bit_length=3)

def test_PacketFieldBadTypeDataTypeArgument():

    new_obj = PacketField(name='HDR_VER', data_type=25, bit_offset=0, bit_length=3)

def test_PacketFieldBadTypeBitOffsetArgument():

    new_obj = PacketField(name='HDR_VER', data_type='uint', bit_offset="0", bit_length=3)

def test_PacketFieldBadTypeBitLengthArgument():

    new_obj = PacketField(name='HDR_VER', data_type='uint', bit_offset=0, bit_length="3")

def test_PacketFieldBadTypeByteOrderArgument():

    new_obj = PacketField(name='HDR_VER', data_type='uint', bit_offset=0, bit_length=3, byte_order = 0)

def test_PacketFieldBadValueDataTypeArgument():

    new_obj = PacketField(name='HDR_VER', data_type='double', bit_offset=0, bit_length=3)

def test_PacketFieldBadValueByteOrderArgumentCaseSensitive():

    new_obj = PacketField(name='HDR_VER', data_type='uint', bit_offset=0, bit_length=3, byte_order = 'BIG')
