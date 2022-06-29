"""High level Object-Oriented interface methods for the pyccsds package."""

__author__ = "Joey Mukherjee <joey@swri.org>"

import numpy as np

from .decode import _decode_packet


class PacketField(object):
    """
    A class used to represent a field contained in a packet.

    Attributes
    ----------
    _name : str
        An identifier for the field
    _data_type : str
        The data type of the field
    _bit_length : int
        The number of bits contained in the field
    _bit_offset : int
        The bit offset into the packet, including the primary header
    _byte_order : str
        The byte order of the field
    """

    def __init__(self, name, data_type, bit_length, bit_offset=None, byte_order="big"):
        """
        Definition of a field contained in a packet.

        Parameters
        ----------
        name : str
            The string identifier for the field. The name specifies how you may
            call upon this data later.
        data_type : str
            The data type of the field.
            Valid values - {'uint', 'int', 'float', 'str', 'fill'}.
        bit_length : int
            The number of bits contained in the field.
        bit_offset : int, optional
            The bit offset into the packet, including the primary header.
            If this is not specified, then the bit offset will be calculated
            automatically from its position inside the packet definition
            (default is None).
        byte_order : str, optional
            The byte order of the field (default is 'big').
            Valid values - {'big', 'little'}.

        Raises
        ------
        TypeError
            If one of the arguments is not of the correct type.
        ValueError
            If the data_type or byte_order argument is invalid.
        """

        if not isinstance(name, str):
            raise TypeError("name parameter must be a str")
        if not isinstance(data_type, str):
            raise TypeError("data_type parameter must be a str")
        if not isinstance(bit_length, (int, np.integer)):
            raise TypeError("bit_length parameter must be an int")
        if not (bit_offset is None or isinstance(bit_offset, (int, np.integer))):
            raise TypeError("bit_offset parameter must be an int")
        if not isinstance(byte_order, str):
            raise TypeError("byte_order parameter must be a str")

        valid_data_types = ("uint", "int", "float", "str", "fill")
        if data_type not in valid_data_types:
            raise ValueError(
                "data_type set to {0} - must be one of {valids}".format(
                    data_type, valids=repr(valid_data_types)
                )
            )

        valid_byte_orders = ("big", "little")
        if byte_order not in valid_byte_orders:
            raise ValueError(
                "byte_order set to {0} - must be one of {valids}".format(
                    byte_order, valids=repr(valid_byte_orders)
                )
            )

        self._name = name
        self._data_type = data_type
        self._bit_length = bit_length
        self._bit_offset = bit_offset
        self._byte_order = byte_order

    def __repr__(self):
        """Define the string representation of the PacketField class object.

        Parameters
        ----------
        No parameters defined.

        Returns
        -------
        str
            The string representation of the key-value pairs of the PacketField
            attributes.
        """

        values = {k: repr(v) for (k, v) in self.__dict__.items()}

        return (
            "PacketField(name={_name}, data_type={_data_type}, "
            "bit_length={_bit_length}, bit_offset={_bit_offset}, "
            "byte_order={_byte_order})".format(**values)
        )

    def __iter__(self):
        """Define the iterator for the PacketField class object.

        Parameters
        ----------
        No parameters defined.

        Returns
        -------
        iterator
            The PacketField custom iterator object
        """

        return iter(
            [
                ("name", self._name),
                ("dataType", self._data_type),
                ("bitLength", self._bit_length),
                ("bitOffset", self._bit_offset),
                ("byteOrder", self._byte_order),
            ]
        )


class Packet(object):
    """
    A class used to collect single packets.

    Attributes
    ----------
    _packets : dictionary list of `ccsdspy.PacketField`
        The packets being collected and ordered by name.
    """

    def __init__(self, packets):
        """
        Defines a list of packets.

        Parameters
        ----------
        packets : dictionary list of `ccsdspy.PacketField`
            A list of packet fields included in the definition ordered by name.
        """

        self._packets = packets[:]

    def read_one(self, file_bytes):
        """
        Decodes an array of bytes containing a sequence of packets.

        Parameters
        ----------
        file_bytes: str
            An array of bytes read from a file or a file-like object.

        Returns
        -------
        data: `OrderedDict`
            A dictionary mapping field names to NumPy arrays.
        """

        field_arrays = _decode_packet(file_bytes, self._packets)

        return field_arrays


class ParseMultiplePackets(object):
    """
    A class used to parse multiple packet types and lengths given an array of
    packets organized by an ID.

    In the context of engineering and science, variable length packets
    correspond to data that is of a variable layout every time, but has
    a length. Examples of this include sensor time series.

    Attributes
    ----------
    _packets : dictionary list of `ccsdspy.PacketField`
        The list of packets associated with the given ID.
    _apid_lookup : str
        The ID that is associated with the packets.
    _ccsds_header : Packet class
        The packet definition of the CCSDS header.
    _file_bytes : str
        An array of bytes read from a file or a string.
    _offset : int
        The offset into the array of bytes read from a file or a string.
    """

    def __init__(self, packets, apid_lookup):
        """
        Parameters
        ----------
        packets : dictionary list of `ccsdspy.PacketField`
            List of packet fields contained in the definition ordered by name.
        apid_lookup : str
            The ID for which the packets are to be associated.
        """

        self._packets = packets
        self._apid_lookup = apid_lookup

        self._ccsds_header = Packet(
            [
                PacketField(
                    name="HDR_VER", data_type="uint", bit_offset=0, bit_length=3
                ),
                PacketField(
                    name="HDR_TYPE", data_type="uint", bit_offset=3, bit_length=1
                ),
                PacketField(
                    name="HDR_SHDR", data_type="uint", bit_offset=4, bit_length=1
                ),
                PacketField(
                    name="HDR_APID", data_type="uint", bit_offset=5, bit_length=11
                ),
                PacketField(
                    name="HDR_GRP", data_type="uint", bit_offset=0, bit_length=2
                ),
                PacketField(
                    name="HDR_SEQ", data_type="uint", bit_offset=2, bit_length=14
                ),
                PacketField(
                    name="HDR_LEN", data_type="uint", bit_offset=0, bit_length=16
                ),
                PacketField(
                    name="HDR_SPARE", data_type="fill", bit_offset=0, bit_length=1
                ),
                PacketField(
                    name="HDR_RT_PB", data_type="fill", bit_offset=1, bit_length=1
                ),
                PacketField(
                    name="HDR_FLASH_PAGE", data_type="uint", bit_offset=2, bit_length=6
                ),
                PacketField(
                    name="HDR_FLASH_BLOCK",
                    data_type="uint",
                    bit_offset=0,
                    bit_length=14,
                ),
                PacketField(
                    name="HDR_TIME_VALID", data_type="uint", bit_offset=6, bit_length=1
                ),
                PacketField(
                    name="HDR_YEAR", data_type="uint", bit_offset=7, bit_length=11
                ),
                PacketField(
                    name="HDR_DAY", data_type="uint", bit_offset=2, bit_length=9
                ),
                PacketField(
                    name="HDR_HOUR", data_type="uint", bit_offset=3, bit_length=5
                ),
                PacketField(
                    name="HDR_MIN", data_type="uint", bit_offset=0, bit_length=6
                ),
                PacketField(
                    name="HDR_SEC", data_type="uint", bit_offset=6, bit_length=6
                ),
                PacketField(
                    name="HDR_USEC", data_type="uint", bit_offset=4, bit_length=20
                ),
            ]
        )

    def start_over(self):
        """Reset the system and start anew.

        Parameters
        ----------
        No parameters defined.
        """

        self._offset = 0
        self._file_bytes = None

    def read_one(self, file):
        """Decode a file-like object containing a sequence of these packets.

        Call continuously to get all packets.

        Parameters
        ----------
        file: str
            Path to a file on the local file system or a file-like object.

        Returns
        -------
        type : str
            The name of the packet based on the APIDs/lookup table passed in.
        data : `OrderedDict`
            A dictionary mapping field names to NumPy arrays.

        Raises
        ------
        TypeError
            If one of the APIDs being processed is unknown.
        """

        # First time parsing the input file / string?
        # If so, get all the packets.

        if self._file_bytes is None:
            if isinstance(file, str):
                self._file_bytes = np.fromstring(file.read(), "u1")
            else:
                self._file_bytes = np.fromfile(file, "u1")

        field_arrays = None

        # Haven't finished parsing the whole array of bytes?

        if self._offset < self._file_bytes.size:

            # Read one header packet.

            header_field_arrays = self._ccsds_header.read_one(
                self._file_bytes[self._offset :]
            )
            try:
                which_packet = self._apid_lookup[header_field_arrays["HDR_APID"]]
            except IndexError:
                # if we got a HDR_APID we don't understand, code will simply raise an
                # Exception for the caller to catch.  Initial comments said the code
                # should error out gracefully by returning None but that is not what
                # the code actually does.

                raise TypeError(
                    "ERROR - unknown APID {apid}!".format(
                        apid=header_field_arrays["HDR_APID"]
                    )
                )

            field_arrays = self._packets[which_packet].read_one(
                self._file_bytes[self._offset :]
            )

            # can't remember where 7 comes from
            self._offset = self._offset + header_field_arrays["HDR_LEN"] + 7
            return {"type": which_packet, "data": field_arrays}
        else:
            return None
