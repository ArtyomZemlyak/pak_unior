# Unior.py
"""CLass Unior(), use for chating with PAK UNIOR module"""

import serial
import serial.tools.list_ports
from time import process_time
from struct import unpack
import keyboard

from ComConnect import ComConnect

STD_SPEED = 57600  # Скорость COM порта
COM_PORT = 'COM6'


class Unior(ComConnect):
    """Create connection with PAK UNIOR"""

    def __init__(self, channel, com_port=COM_PORT, std_speed=STD_SPEED):
        print('... | Unior | ...', end='')
        self.channel = channel
        super().__init__(com_port, std_speed)

    def begin(self, com_port=COM_PORT):
        """Setup COM-port and connect to PAK UNIOR"""
        self.com_port = com_port
        if keyboard.is_pressed('q'):
            self.piSerial.close()
            print('CLOSING... | EXIT')
        try:
            if self.status == 2:
                print(f'INITIALIZE... | unior_begin {self.channel}', end='')
                self.begin_initialization()
            if self.status == 0:
                self.begin_connection(self.channel)
        except (OSError, serial.SerialException,
                serial.serialutil.SerialException):
            try:
                self.piSerial.close()
            except (OSError, serial.SerialException):
                self.status = 2
                return "NO CONN"
            self.status = 2
            return "NO CONN"
        return self.status

    def read(self):
        """Read data from PAK UNIOR"""
        try:
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
        except (OSError, serial.SerialException,
                serial.serialutil.SerialException):
            try:
                self.piSerial.close()
            except (OSError, serial.SerialException):
                self.status = 2
                return "NO CONN"
            self.status = 2
            return "NO CONN"

    def set_status(self, sts):
        """Set status for reconnection or read data"""
        self.status = sts
        if self.status == 2:
            self.__init__(self.channel, self.com_port, self. std_speed)
