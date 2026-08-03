from scservo_sdk import sms_sts, PortHandler

follower_limits = {1: (730, 3440), 2: (740, 3340), 3: (750, 3040), 4: (900, 3270), 5: (10, 4095), 6: (2020,3520)}

# Correct this
leader_limits = {1: (730, 3440), 2: (740, 3340), 3: (750, 3040), 4: (900, 3270), 5: (10, 4095), 6: (2020,3520)}

# Register addresses
ADDR_PRESENT_POSITION = 56
ADDR_PRESENT_VOLTAGE = 62
ADDR_PRESENT_TEMPERATURE = 63
ADDR_MOVING = 66
# Motor Control
ADDR_TORQUE_ENABLE = 40
ADDR_GOAL_POSITION = 42

class Servo:
    def __init__(self, lead_port, foll_port, baudrate):
        self.leader_port = PortHandler(lead_port)
        self.follower_port = PortHandler(foll_port)
        self.leader_servo = sms_sts(self.leader_port)
        self.follower_servo = sms_sts(self.follower_port)
        self.baudrate = baudrate

    def init_servos(self):
        if self.leader_port.openPort():
            if self.follower_port.openPort():
                print("Both ports opened")
            else:
                print("Failed to open follower port")
                return False
        else:
            print("Failed to open leader port")
            return False

        if self.leader_port.setBaudRate(self.baudrate):
            if self.follower_port.setBaudRate(self.baudrate):
                print("Both baudrates set")
            else:
                print("Failed to set follower baud rate")
                return False
        else:
            print("Failed to set leader baud rate")
            return False

        for i in leader_limits.keys():
            model_number, comm_result, error = self.leader_servo.ping(i)
            if comm_result == 0:
                continue
            else:
                print(f"Failed to ping leader servo {i} ")
                return False

        print("All leader servos pinged")

        for i in follower_limits.keys():
            model_number, comm_result, error = self.follower_servo.ping(i)
            if comm_result == 0:
                continue
            else:
                print(f"Failed to ping follower servo {i} ") 
                return False  

        print("All follower servos pinged")

        # Torque enable for follower
        for i in follower_limits.keys():
            self.follower_servo.write1ByteTxRx(i, ADDR_TORQUE_ENABLE, 1)

        print("Torque enabled for follower servos - holding positions now")

        return True

    def read(self, ID) -> int:
        l_pos, comm_result, error = self.leader_servo.read2ByteTxRx(ID, ADDR_PRESENT_POSITION)
        if comm_result == 0:
            f_pos, comm_result, error = self.follower_servo.read2ByteTxRx(ID, ADDR_PRESENT_POSITION)
            if comm_result == 0:
                if l_pos != f_pos:
                    return True, f_pos
                else:
                    return False
            else:
                print(f"Follower servo {ID} read failed")
        else:
            print(f"Leader servo {ID} read failed")

    def move(self, follower_ID, val):
        position, comm_result, error = self.follower_servo.read2ByteTxRx(follower_ID, ADDR_PRESENT_POSITION)
        if comm_result == 0:
            limits = follower_limits[follower_ID-1]
            if limits[0] < position < limits[1]:
                self.follower_servo.WritePosEx(follower_ID, val, 1000, 50)
            else:
                print("Leader out of follower safe range")
        else:
            print(f"Leader servo {follower_ID} read failed")


        

