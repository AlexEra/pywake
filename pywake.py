import serial
from constants import *


def calculate_crc(buf: list) -> int:
    crc = 0xDE

    for elem in buf:
        crc = crc_table[crc ^ elem]

    return crc


class SerialWakeProtocol:
    def __init__(self, prt: str):
        self._addr = list()
        self._cmd = 0
        self._n = list()
        self._data = list()
        self._crc = list()
        self._in_package = list()
        self._connected = False

        try:
            self.serial_conn = serial.Serial(prt, baudrate=115200)
            self._connected = True
        except serial.SerialException as e:
            print(e)

    def __del__(self):
        if self._connected:
            self.serial_conn.close()

    def catch_input_data(self) -> list:
        self._in_package = list()

        if not self._connected:
            return list()
        else:
            byte = int.from_bytes(self.serial_conn.read(), byteorder='big')
            if byte == FEND:
                return self._looping_for_package(byte)
            else:
                return list()

    def send_data(self, address: int, command: int, data_lst: list) -> bool:
        if address > 0x80 or command > 0x7F or not self._connected:
            return False

        in_data = data_lst.copy()

        n = len(in_data)
        in_data.append(calculate_crc([FEND, address, command, n, *in_data]))
        address |= 0x80
        data_to_send = [FEND, *self._stuffing(address), command, *self._stuffing(n)]        

        for i in range(n + 1):  # inlcuding crc byte
            tmp = self._stuffing(in_data[i])
            if len(tmp) == 1:
                data_to_send.append(*tmp)
            elif len(tmp) > 1:
                data_to_send.append(tmp[0])
                data_to_send.append(tmp[1])

        data_to_send = bytearray(data_to_send)
        self.serial_conn.write(data_to_send)
        return True

    def check_crc(self) -> bool:
        if self._in_package == []:
            return False
        elif calculate_crc(self._in_package[:-1]) == self._in_package[-1]:
            return True 
        else:
            return False

    def _looping_for_package(self, start_byte: int) -> list:
        bytes_count = 1  # start_byte is included
        max_bytes = 517  # overall bytes count in a package

        self._in_package.append(start_byte)

        while True:
            b = int.from_bytes(self.serial_conn.read(), byteorder='big')
            if b == FESC:
                self._in_package.append(self._unstuffing())
            else:
                self._in_package.append(b)

            bytes_count += 1

            if bytes_count > MAX_BYTES_COUNT:
                return list()
            elif bytes_count == 2:
                self._addr = b & 0x7F
                self._in_package[1] &= 0x7F  # excluding the bit at 7 position
            elif bytes_count == 3:
                self._cmd = b
            elif bytes_count == 4:
                if b < 256:
                    self._n = b
                    max_bytes = 5 + b  # including the crc byte
            elif bytes_count == max_bytes:
                return self._in_package

    def _stuffing(self, byte_to_check: int):        
        if byte_to_check == FEND:
            return [FESC, TFEND]
        elif byte_to_check == FESC:
            return [FESC, TFESC]
        else:
            return [byte_to_check]

    def _unstuffing(self) -> int:
        unst_byte = int.from_bytes(self.serial_conn.read(), byteorder='big')
        if unst_byte == TFEND:
            return FEND
        elif unst_byte == TFESC:
            return FESC
        else:
            return unst_byte
