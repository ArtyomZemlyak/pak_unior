# Unior.py
"""CLass Unior(), use for chating this PAK UNIOR module"""

from time import process_time
import serial.tools.list_ports
from struct import unpack
import keyboard

CMD = 0xff


class Unior:
    """Create connection with PAK UNIOR"""

    def __init__(self, channel, com_port, std_speed):
        print('INITIALIZE... | Unior...', end='')
        self.channel = channel
        self.com_port = com_port
        self. std_speed = std_speed
        self.status = 2
        self.piSerial = serial.Serial()
        self.piSerial.close()
        print(' DONE |')

    def begin(self):
        """Setup COM-port and connect to PAK UNIOR"""
        if keyboard.is_pressed('q'):
            self.piSerial.close()
            print('CLOSING... | EXIT')

        if self.status == 2:
            print(f'INITIALIZE... | unior_begin {self.channel}', end='')
            self.piSerial.baudrate = self.std_speed
            self.piSerial.port = self.com_port
            self.piSerial.timeout = 0.1
            self.piSerial.write_timeout = 0.1
            print(' DONE |')
            self.piSerial.open()
            print(f'|PORT:{self.com_port}| OPENED')
            self.piSerial.write(CMD)
            print(f'|WRITE| {CMD}')
            print('|WHAITING...', end='')
            self.status = 0

        if self.status == 0:
            s = self.piSerial.readline()
            # print(end='.')

            if s == b'OK\n':
                print('CONNECTED')
                # send channels mask
                self.piSerial.write((str(self.channel) + '\r\n\0').encode())
                print('|WHAITING DATA...')
                self.status = 1

        return self.status

    def read(self):
        """Read data from PAK UNIOR"""
        if self.piSerial.inWaiting() > 0:
            self.piSerial.flushInput()
        self.piSerial.write((str(self.channel) + '\r\n\0').encode())
        beg_time = process_time()
        while self.piSerial.inWaiting() < 4:
            if process_time() - beg_time > 1:
                return 0
        try:
            tmp = unpack('<f', self.piSerial.read(4))[0]
            if tmp != tmp:
                return 0
            else:
                return float("%.2f" % tmp)
        except ValueError:
            return 0

    def set_status(self, sts):
        """Set status for reconnection or read data"""
        self.status = sts
        if self.status == 2:
            self.__init__(self.channel, self.com_port, self. std_speed)

    def close(self):
        """Close COM port"""
        self.piSerial.close()
