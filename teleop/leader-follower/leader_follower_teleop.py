import serial.tools.list_ports
import servo_control
import sys, termios, select, tty

leader_port = "/dev/ttyACM1"
follower_port = "/dev/ttyACM0"
baudrate = 1000000


class teleop():
    def __init__(self, leader_port, follower_port):
        self.lead_port = leader_port
        self.follower_port = follower_port

def is_space_pressed():
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1) == ' '
    return False

print(f"Using leader port: {leader_port}")
print(f"Using follower port: {follower_port}")

fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)

if __name__ == "__main__":
    servo = servo_control.Servo(leader_port, follower_port, baudrate)
    if servo.init_servos():
        try:
            tty.setcbreak(fd)
            while not is_space_pressed():
                for i in servo_control.leader_limits.keys():
                    result, pos = servo.read(i)
                    if result:
                        servo.move(i, pos)
                    else:
                        continue
            
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            servo.shutdown()
                    
'''
# List all available serial ports
ports = serial.tools.list_ports.comports()

print("Available serial ports:")
for port in ports:
    print(f"  {port.device}")
    print(f"    Description: {port.description}")
    print(f"    Manufacturer: {port.manufacturer}")
    print()

'''




