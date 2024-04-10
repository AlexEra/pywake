from pywake import *
from time import sleep


TEST_BYTES = list()


if __name__ == '__main__':
    ww = SerialWakeProtocol('COM3')

    ''' Input test '''
    if ww.send_data(address=-1, command=12, data_lst=[100, 192, 66]):
        print(ww.catch_input_data(ignore_address=True))
        print(ww.check_crc())
    else:
        print('Error')
