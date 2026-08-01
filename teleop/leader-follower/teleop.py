import serial.tools.list_ports
import servo_control

# List all available serial ports
ports = serial.tools.list_ports.comports()

print("Available serial ports:")
for port in ports:
    print(f"  {port.device}")
    print(f"    Description: {port.description}")
    print(f"    Manufacturer: {port.manufacturer}")
    print()


leader_port = ""
follower_port = ""

print(f"Using leader port: {leader_port}")
print(f"Using follower port: {follower_port}")



