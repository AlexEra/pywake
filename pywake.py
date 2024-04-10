import serial
from constants import *


def calculate_crc(buf: list) -> int:
    crc = 0xDE
    for elem in buf:
        crc = crc_table[crc ^ elem]
    return crc


class SerialWakeProtocol:
    def __init__(self, prt: str):
        self.__addr = 0
        self.__cmd = 0
        self.__n = 0
        self.__data = list()
        self.__in_package = list()
        self.__connected = False
        self.__ignore_address_flag = False

        try:
            self.serial_conn = serial.Serial(prt, baudrate=115200)
            self.__connected = True
        except serial.SerialException as e:
            print(e)

    def __del__(self):
        if self.__connected:
            self.serial_conn.close()

    def catch_input_data(self, ignore_address=False) -> list:
        self.__in_package = list()
        self.__data = list()
        self.__ignore_address_flag = ignore_address

        if not self.__connected:
            return list()
        else:
            byte = int.from_bytes(self.serial_conn.read(), byteorder='big')
            if byte == FEND:
                return self.__looping_for_package(byte)
            else:
                return list()

    def send_data(self, address: int, command: int, data_lst: list) -> bool:
        if address > 0x80 or command > 0x7F or not self.__connected:
            return False

        in_data = data_lst.copy()
        data_to_send = list()
        n = n = len(in_data)

        if address == -1:
            in_data.append(calculate_crc([FEND, command, n, *in_data]))
            data_to_send = [FEND, command, *self.__stuffing(n)]   
        else:
            in_data.append(calculate_crc([FEND, address, command, n, *in_data]))
            address |= 0x80
            data_to_send = [FEND, *self.__stuffing(address), command, *self.__stuffing(n)]        

        for i in range(n + 1):  # including crc byte
            tmp = self.__stuffing(in_data[i])
            if len(tmp) == 1:
                data_to_send.append(*tmp)
            elif len(tmp) == 2:
                data_to_send.append(tmp[0])
                data_to_send.append(tmp[1])

        data_to_send = bytearray(data_to_send)
        self.serial_conn.write(data_to_send)
        print(data_to_send)  ##################
        return True

    def check_crc(self) -> bool:
        if self.__in_package == []:
            return False
        elif calculate_crc(self.__in_package[:-1]) == self.__in_package[-1]:
            return True 
        else:
            return False

    def read_last_address(self):
        return self.__addr

    def read_last_cmd(self):
        return self.__cmd

    def read_last_data_len(self):
        return self.__n

    def read_last_data(self) -> list:
        return self.__data

    def __looping_for_package(self, start_byte: int) -> list:
        bytes_count = 1  # start_byte is included
        max_bytes = 518  # overall bytes count in a package

        self.__in_package.append(start_byte)

        while True:
            b = int.from_bytes(self.serial_conn.read(), byteorder='big')
            if b == FESC:
                b = self.__unstuffing()
            self.__in_package.append(b)

            bytes_count += 1

            if self.__ignore_address_flag:
                if bytes_count > (MAX_BYTES_COUNT - 1):
                    return list()
                elif bytes_count == 2:
                    self.__cmd = b
                elif bytes_count == 3:
                    if b < 256:
                        self.__n = b
                        max_bytes = 4 + b  # including the crc byte
            else:
                if bytes_count > MAX_BYTES_COUNT:
                    return list()
                elif bytes_count == 2:
                    self.__addr = b & 0x7F
                    self.__in_package[1] &= 0x7F  # excluding the bit at 7 position
                elif bytes_count == 3:
                    self.__cmd = b
                elif bytes_count == 4:
                    if b < 256:
                        self.__n = b
                        max_bytes = 5 + b  # including the crc byte

            if bytes_count == max_bytes:
                return self.__in_package
            else:
                self.__data.append(b)

    def __stuffing(self, byte_to_check: int):        
        if byte_to_check == FEND:
            return [FESC, TFEND]
        elif byte_to_check == FESC:
            return [FESC, TFESC]
        else:
            return [byte_to_check]

    def __unstuffing(self) -> int:
        unst_byte = int.from_bytes(self.serial_conn.read(), byteorder='big')
        if unst_byte == TFEND:
            return FEND
        elif unst_byte == TFESC:
            return FESC
        else:
            return unst_byte
