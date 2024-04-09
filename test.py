from pywake import *
from time import sleep


TEST_BYTES = list()


if __name__ == '__main__':
    ww = SerialWakeProtocol('COM3')

    ''' Input test '''
    while True:
        print(ww.catch_input_data())
        sleep(0.2)
        # try:
        #     print(ww.check_crc())
        # except Exception as e:
        #     print(e)
