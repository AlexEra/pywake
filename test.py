from pywake import *
from time import sleep


TEST_BYTES = list()


if __name__ == '__main__':
    ww = SerialWakeProtocol('COM3')
    a = -1
    c = 12
    d = [12, 192]

    if ww.send_data(address=a, command=c, data_s=d):
        if a > 0:
            print(ww.catch_input_data())
        else:
            print(ww.catch_input_data(ignore_address=True))
        print(ww.check_crc())
    else:
        print('Error')
