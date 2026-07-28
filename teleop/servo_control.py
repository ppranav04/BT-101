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
                return True
            else:
                print("✗ Failed to set baud rate")
        else:
            print("✗ Failed to open port")

    def move(self, SERVO_ID, dir):
        model_number, comm_result, error = self.sms_servo.ping(SERVO_ID)
        if comm_result == 0:
            self.sms_servo.write1ByteTxRx(SERVO_ID, ADDR_TORQUE_ENABLE, 1)
            print("✓ Torque enabled - servo is now holding position")
            move_limits = SERVO_LIMITS[SERVO_ID]
            if (-1638 <= dir <= 1638):
                    #Read current position
                    position, comm_result, error = self.sms_servo.read2ByteTxRx(SERVO_ID, ADDR_PRESENT_POSITION)
                    if comm_result == 0:
                        self.sms_servo.WritePosEx(SERVO_ID, position, 1000, 50)
            else:
                if dir < 0:
                    move_to = move_limits[0]
                    self.sms_servo.WritePosEx(SERVO_ID, move_to, 1000, 50)
                else:
                    move_to = move_limits[1]
                    self.sms_servo.WritePosEx(SERVO_ID, move_to, 1000, 50)                     
        else:
            print(f"✗ Failed to ping servo")



    


# I am planning on using cases where if left jostick + or - then use servo with ID one goes + or negative and move it if 
'''
SERIAL_PORT = '/dev/ttyACM0'  # Replace with your actual port
print(f"Using serial port: {SERIAL_PORT}")





# Initialize the port handler and servo handler
port_handler = PortHandler(SERIAL_PORT)
servo = sms_sts(port_handler)






# Ping the servo to check communication and motor status
for i in SERVO_ID:
    model_number, comm_result, error = servo.ping(i)

    if comm_result == 0:  # COMM_SUCCESS
        print(f"✓ Servo ID {i} found!")
        print(f"  Model number: {model_number}")
    else:
        print(f"✗ Failed to ping servo")

    # Read current position (2 bytes)
    position, comm_result, error = servo.read2ByteTxRx(i, ADDR_PRESENT_POSITION)
    if comm_result == 0:
        degrees = position * 360 / 4096  # Convert to degrees
        print(f"Current Position: {position} (raw) = {degrees:.1f}°")
    else:
        print(f"Failed to read position")

    #Read voltage (1 byte)
    voltage_raw, comm_result, error = servo.read1ByteTxRx(i, ADDR_PRESENT_VOLTAGE)
    if comm_result == 0:
        voltage = voltage_raw * 0.1  # Convert to volts
        print(f"Voltage: {voltage:.1f}V")
    else:
        print(f"Failed to read voltage")

    # Read temperature (1 byte)
    temp, comm_result, error = servo.read1ByteTxRx(i, ADDR_PRESENT_TEMPERATURE)
    if comm_result == 0:
        print(f"Temperature: {temp}°C")
    else:
        print(f"Failed to read temperature")

    # Read torque enable status (1 byte)
    torque_enabled, comm_result, error = servo.read1ByteTxRx(i, ADDR_TORQUE_ENABLE)
    if comm_result == 0:
        print(f"Torque Enabled: {'Yes' if torque_enabled else 'No'}")
    else:
        print(f"Failed to read torque status")

    # Read moving status (1 byte)
    moving, comm_result, error = servo.read1ByteTxRx(i, ADDR_MOVING)
    if comm_result == 0:
        print(f"Moving: {'Yes' if moving else 'No'}")
    else:
        print(f"Failed to read moving status")



# Motor Control

# Register addresses
ADDR_TORQUE_ENABLE = 40
ADDR_GOAL_POSITION = 42

# Enable torque
servo.write1ByteTxRx(SERVO_ID, ADDR_TORQUE_ENABLE, 1)
print("✓ Torque enabled - servo is now holding position")

# Move to position (2048 = 180°)
move_to = 2048
degrees = move_to * 360 / 4096  # Convert to degrees
# WritePosEx(ID, Position, Speed, Acceleration)
servo.WritePosEx(SERVO_ID, move_to, 1000, 50)
print(f"✓ Moving to position ({move_to} = {degrees}°)")




'''