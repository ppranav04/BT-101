import pygame as pg
import pygame._sdl2.controller as sdl2_controller
import servo_control

SERIAL_PORT = '/dev/ttyACM0'
BAUDRATE = 1000000
'''
axis_constants = [pg.CONTROLLER_AXIS_LEFTX, pg.CONTROLLER_AXIS_LEFTY,
pg.CONTROLLER_AXIS_RIGHTX, pg.CONTROLLER_AXIS_RIGHTY,
pg.CONTROLLER_AXIS_TRIGGERLEFT, pg.CONTROLLER_AXIS_TRIGGERRIGHT]

button_constants = [pg.CONTROLLER_BUTTON_A, pg.CONTROLLER_BUTTON_B,
pg.CONTROLLER_BUTTON_X, pg.CONTROLLER_BUTTON_Y,pg.CONTROLLER_BUTTON_DPAD_UP, pg.CONTROLLER_BUTTON_DPAD_DOWN,
pg.CONTROLLER_BUTTON_DPAD_LEFT, pg.CONTROLLER_BUTTON_DPAD_RIGHT,
pg.CONTROLLER_BUTTON_LEFTSHOULDER, pg.CONTROLLER_BUTTON_RIGHTSHOULDER,
pg.CONTROLLER_BUTTON_LEFTSTICK, pg.CONTROLLER_BUTTON_RIGHTSTICK,
pg.CONTROLLER_BUTTON_BACK, pg.CONTROLLER_BUTTON_GUIDE,
pg.CONTROLLER_BUTTON_START]
'''

mapping  = {1:pg.CONTROLLER_AXIS_LEFTX, 2:pg.CONTROLLER_AXIS_LEFTY, 3:pg.CONTROLLER_AXIS_RIGHTX,
             4:pg.CONTROLLER_AXIS_RIGHTY, 5:[pg.CONTROLLER_BUTTON_LEFTSHOULDER,pg.CONTROLLER_BUTTON_RIGHTSHOULDER],
             6:[pg.CONTROLLER_AXIS_TRIGGERLEFT, pg.CONTROLLER_AXIS_TRIGGERRIGHT]}

CONTROL_HELP = {
    1: "Left Stick X  -> shoulder_pan",
    2: "Left Stick Y  -> shoulder_lift",
    3: "Right Stick X -> elbow_flex",
    4: "Right Stick Y -> wrist_flex",
    5: "LB / RB       -> wrist_roll",
    6: "LT / RT       -> gripper (open/close)",
}

def print_controls():
    print("Controls:")
    for servo_id, desc in CONTROL_HELP.items():
        print(f"  {desc}")

def init_controllers():
    pg.init()
    sdl2_controller.init()
    count = sdl2_controller.get_count()
    return count


class XboxCtrl:
    def __init__(self, index: int = 0):
        self.controller = sdl2_controller.Controller(index)
        self.name = self.controller.name

    def get_axis(self, axis_constant) -> float:
        raw = self.controller.get_axis(axis_constant)
        return raw

    def get_button(self, button_constant) -> bool:
        c = self.controller.get_button(button_constant)
        return bool(c)

if __name__ == "__main__":
    count = init_controllers()
    print(f"Using serial port: {SERIAL_PORT}")
    if count == 0:
        print("No controller found.")
    else:
        # Configuration        
        xbox  = XboxCtrl()
        print(f"Connected: {xbox.name}")
        print_controls()
        servo = servo_control.Servo(SERIAL_PORT, BAUDRATE)

        
        if (servo.init_servo()):
            print("Connected to servos")
            while xbox.get_button(pg.CONTROLLER_BUTTON_START) != True:
                pg.event.pump()
                for i in mapping.keys():
                    if 1 <= i <= 4:
                        dir = xbox.get_axis(mapping[i])
                        SERVO_ID = i
                    elif i==5:
                        choice = mapping[i]
                        if xbox.get_button(choice[0]):
                            dir = -1
                        elif xbox.get_button(choice[1]):
                            dir = 1
                        else:
                            dir = 0
                        SERVO_ID = i
                    else:
                        choice = mapping[i]
                        if xbox.get_axis(choice[0]) > 1638:
                            dir = -1
                        elif xbox.get_axis(choice[1]) > 1638:
                            dir = 1                        
                        else:
                            dir = 0
                        SERVO_ID = i
                    servo.move(SERVO_ID, dir)
            servo.shutdown()
        else:
            print("Servo initialisaiton failed")
