import pygame as pg
import pygame._sdl2.controller as sdl2_controller
import servo_control

SERIAL_PORT = '/dev/ttyACM0'
BAUDRATE = 1000000

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
        # Returnns nomalized value from -1.0 to 1.0
        raw = self.controller.get_axis(axis_constant)
        return raw / 32768.0

    def get_button(self, button_constant) -> bool:
        c = self.controller.get_button(button_constant)
        return bool(c)

if __name__ == "__main__":
    count = init_controllers()
    print(f"Using serial port: {SERIAL_PORT}")
    if count == 0:
        print("No controller found.")
    else:
        xbox  = XboxCtrl(0)
        print(f"Connected: {xbox.name}")

        pg.event.pump()
        # Configuration
        
        SERVO_ID = (1,2,3,4,5,6)
        Servo_control = servo_control.Servo(SERIAL_PORT, BAUDRATE)
        if (Servo_control.init_servo()):
            print("Connected to servos")