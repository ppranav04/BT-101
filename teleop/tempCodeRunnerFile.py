import serial.tools.list_ports
from scservo_sdk import sms_sts, PortHandler

ports = serial.tools.list_ports.comports()

print("Available serial ports:")
for port in ports:
    print(f"  {port.device}")
    print(f"    Description: {port.description}")
    print(f"    Manufacturer: {port.manufacturer}")
    print()

SERIAL_PORT = '/dev/ttyACM0'  # Replace with your actual port
print(f"Using serial port: {SERIAL_PORT}")

# Configuration
BAUDRATE = 1000000
SERVO_ID = 1

# Initialize the port handler and servo handler
port_handler = PortHandler(SERIAL_PORT)
servo = sms_sts(port_handler)

# Open the serial port
if port_handler.openPort():
    print("✓ Port opened successfully")
else:
    print("✗ Failed to open port")
    
# Set the baud rate
if port_handler.setBaudRate(BAUDRATE):
    print(f"✓ Baud rate set to {BAUDRATE}")
else:
    print("✗ Failed to set baud rate")

# Ping the servo to check communication
model_number, comm_result, error = servo.ping(SERVO_ID)

if comm_result == 0:  # COMM_SUCCESS
    print(f"✓ Servo ID {SERVO_ID} found!")
    print(f"  Model number: {model_number}")
else:
    print(f"✗ Failed to ping servo")