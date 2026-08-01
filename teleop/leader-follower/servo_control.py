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
        else:
            print("Failed to open leader port")

        if self.leader_port.setBaudRate(self.baudrate):
            if self.follower_port.setBaudRate(self.baudrate):
                print("Both baudrates set")
            else:
                print("Failed to set follower baud rate")
        else:
            print("Failed to set leader baud rate")

        for i in leader_limits.keys():
            model_number, comm_result, error = self.leader_servo.ping(i)
            if comm_result == 0:
                continue
            else:
                print(f"Failed to ping leader servo {i} ")

        print("All leader servos pinged")

        for i in follower_limits.keys():
            model_number, comm_result, error = self.follower_servo.ping(i)
            if comm_result == 0:
                continue
            else:
                print(f"Failed to ping follower servo {i} ")   

        print("All follower servos pinged")

        # Torque enable for both leader and follower
        for i in leader_limits.keys():
            self.leader_servo.write1ByteTxRx(i, ADDR_TORQUE_ENABLE, 1)
            self.follower_servo.write1ByteTxRx(i, ADDR_TORQUE_ENABLE, 1)

        print("Torque enabled for leader and follower servos - holding positions now")

        


        

