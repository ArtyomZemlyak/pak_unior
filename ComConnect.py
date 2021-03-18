# ComConnect.py
"""CLass ComConnect(), use for chating with Arduino or another COM PORT"""

import serial
import serial.tools.list_ports
import keyboard

CMD = 0xff
STD_SPEED = 9600  # Скорость COM порта
COM_PORT = 'COM3'


class ComConnect:
    """Create connection with Arduino or another COM PORT"""

    def __init__(self, com_port=COM_PORT, std_speed=STD_SPEED):
        print('INITIALIZE... | ConConnect...', end='')
        self.com_port = com_port
        self. std_speed = std_speed
        self.status = 2
        self.piSerial = serial.Serial()
        self.piSerial.close()
        print(' DONE |')

    def begin_initialization(self, cmd=CMD):
        """Initialization parameters for COM port"""
        print(f'INITIALIZE... | COM {self.com_port}', end='')
        self.piSerial.baudrate = self.std_speed
        self.piSerial.port = self.com_port
        self.piSerial.timeout = 0.1
        self.piSerial.write_timeout = 0.1
        print(' DONE |')
        self.piSerial.open()
        print(f'|PORT:{self.com_port}| OPENED')
        self.piSerial.write(cmd)
        print(f'|WRITE| {cmd}')
        print('|WHAITING...', end='')
        self.status = 0

    def begin_connection(self, wr_line=0):
        """Use if we need response for coonecting"""
        s = self.piSerial.readline()
        if s == b'OK\n':
            print('CONNECTED')
            # send channels mask
            self.write(wr_line)
            print('|WHAITING DATA...')
            self.status = 1

    def begin(self, com_port=COM_PORT):
        """Setup COM-port and connect"""
        self.com_port = com_port
        if keyboard.is_pressed('q'):
            self.piSerial.close()
            print('CLOSING... | EXIT')
        try:
            if self.status == 2:
                self.begin_initialization()
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

    def write(self, wr_line):
        """Write line data"""
        try:
            self.piSerial.write((str(wr_line) + '\r\n\0').encode())
        except (OSError, serial.SerialException):
            self.status = 2
            return "NO CONN"
        return 1

    def read(self):
        """Read data from COM Port"""
        try:
            if self.piSerial.inWaiting() > 0:
                try:
                    tmp = self.piSerial.read(self.piSerial.inWaiting())
                    if tmp != tmp:
                        return 0
                    else:
                        return tmp
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

    @staticmethod
    def serial_ports():
        """ Lists serial port names"""
        print(f'LISTENNING PORTS...')
        print(f'CHECKING PORTS...', end='')
        ports = serial.tools.list_ports.comports()
        print(f'DONE |')
        print(f'PORTS| {ports} |')
        a = []
        for i in ports:
            s = ''
            for j in str(i):
                if j != ' ':
                    s += j
                else:
                    a.append(s)
                    break
        print(f'PORTS str| {a} |')

        return a

    def set_status(self, sts):
        """Set status for reconnection or read data"""
        self.status = sts
        if self.status == 2:
            self.__init__(self.com_port, self. std_speed)

    def close(self):
        """Close COM port"""
        try:
            self.piSerial.close()
        except (OSError, serial.SerialException):
            self.status = 2
            return "NO CONN"
        self.status = 2
        return "NO CONN"
