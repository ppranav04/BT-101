import serial.tools.list_ports
from scservo_sdk import sms_sts, PortHandler



def check_ports(): # List all available serial ports
    ports = serial.tools.list_ports.comports()
    
    print("Available serial ports:")
    for port in ports:
        print(f"  {port.device}")
        print(f"    Description: {port.description}")
        print(f"    Manufacturer: {port.manufacturer}")
        print()

# Register addresses
ADDR_PRESENT_POSITION = 56
ADDR_PRESENT_VOLTAGE = 62
ADDR_PRESENT_TEMPERATURE = 63
ADDR_MOVING = 66

# Motor Control
# Register addresses
ADDR_TORQUE_ENABLE = 40
ADDR_GOAL_POSITION = 42

SERVO_LIMITS = {1: (730, 3440), 2: (740, 3340), 3: (750, 3040), 4: (900, 3270), 5: (10, 4095), 6: (2020,3520)}

class Servo():
    def __init__(self, serial_port, baudrate):
        self.port_handler = PortHandler(serial_port)
        self.sms_servo = sms_sts(self.port_handler)
        self.baudrate = baudrate
    
    
    def init_servo(self):
        # Open the serial port
        if self.port_handler.openPort():
            print("✓ Port opened successfully")
            # Set the baud rate
            if self.port_handler.setBaudRate(self.baudrate):
                print(f"✓ Baud rate set to {self.baudrate}")
                for i in SERVO_LIMITS.keys():
                    model_number, comm_result, error = self.sms_servo.ping(i)
                    if comm_result == 0:
                        comm_result, _ = self.sms_servo.write1ByteTxRx(i, ADDR_TORQUE_ENABLE, 1)
                        if comm_result != 0:
                            print ("Torque enable failed")
                            return False
                    else:
                        print(f"✗ Failed to ping servo")
                        break
                print("✓ Torque enabled - servo is now holding position")
                return True
            else:
                print("✗ Failed to set baud rate")
        else:
            print("✗ Failed to open port")


    def move(self, SERVO_ID, dir):
        move_limits = SERVO_LIMITS[SERVO_ID]
        if (1 <= SERVO_ID <=4):
            if (-1638 <= dir <= 1638):
                #Read current position:
                position, comm_result, error = self.sms_servo.read2ByteTxRx(SERVO_ID, ADDR_PRESENT_POSITION)
                if comm_result == 0:
                    self.sms_servo.WritePosEx(SERVO_ID, position, 1000, 50)

            else:
                if (dir < 0):
                    move_to = move_limits[0]
                    self.sms_servo.WritePosEx(SERVO_ID, move_to, 1000, 50)
                else:
                    move_to = move_limits[1]
                    self.sms_servo.WritePosEx(SERVO_ID, move_to, 1000, 50)
        elif (SERVO_ID == 5):
            if (dir == -1):
                move_to = move_limits[0]
                self.sms_servo.WritePosEx(SERVO_ID, move_to, 1000, 50)              
            elif (dir == 1):
                move_to = move_limits[1]
                self.sms_servo.WritePosEx(SERVO_ID, move_to, 1000, 50)
            else:
                #Read current position:
                position, comm_result, error = self.sms_servo.read2ByteTxRx(SERVO_ID, ADDR_PRESENT_POSITION)
                if comm_result == 0:
                    self.sms_servo.WritePosEx(SERVO_ID, position, 1000, 50)
        else:
            if (dir == -1):
                move_to = move_limits[0]
                self.sms_servo.WritePosEx(SERVO_ID, move_to, 1000, 50)              
            elif (dir == 1):
                move_to = move_limits[1]
                self.sms_servo.WritePosEx(SERVO_ID, move_to, 1000, 50)
            else:
                #Read current position:
                position, comm_result, error = self.sms_servo.read2ByteTxRx(SERVO_ID, ADDR_PRESENT_POSITION)
                if comm_result == 0:
                    self.sms_servo.WritePosEx(SERVO_ID, position, 1000, 50)

    def shutdown(self):
        # Disable torque and close port
        for i in SERVO_LIMITS.keys():
            self.sms_servo.write1ByteTxRx(i, ADDR_TORQUE_ENABLE, 0)
        print("✓ Torque disabled")

        self.port_handler.closePort()
        print("✓ Port closed")       