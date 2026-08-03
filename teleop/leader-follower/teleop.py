import serial.tools.list_ports
import servo_control
import pygame as pg
import pygame._sdl2.controller as sdl2_controller 

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
baudrate = 1000000


class teleop():
    def __init__(self, leader_port, follower_port):
        self.lead_port = leader_port
        self.follower_port = follower_port




print(f"Using leader port: {leader_port}")
print(f"Using follower port: {follower_port}")

mapping  = {1:pg.CONTROLLER_AXIS_LEFTX, 2:pg.CONTROLLER_AXIS_LEFTY, 3:pg.CONTROLLER_AXIS_RIGHTX,
             4:pg.CONTROLLER_AXIS_RIGHTY, 5:[pg.CONTROLLER_BUTTON_LEFTSHOULDER,pg.CONTROLLER_BUTTON_RIGHTSHOULDER],
             6:[pg.CONTROLLER_AXIS_TRIGGERLEFT, pg.CONTROLLER_AXIS_TRIGGERRIGHT]}

if __name__ == "__main__":
    servo = servo_control.Servo(leader_port, follower_port, baudrate)
    if servo.init_servos():
        for i in mapping.keys():
            result, pos = servo.read(i)
            if result:
                servo.move(i, pos)
            else:
                continue
            





