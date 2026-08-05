from scservo_sdk import sms_sts, PortHandler
import time

follower_limits = {1: (761, 3410), 2: (686, 3308), 3: (807, 3106), 4: (858, 3187), 5: (0, 4095), 6: (2046,3472)}
follower_home =  {1: 1984, 2: 833, 3: 3100, 4: 2886, 5: 2002, 6: 2067}
leader_limits = {1: (832, 3498), 2: (787, 3185), 3: (932, 3141), 4: (37, 2344), 5: (0, 4095), 6: (2046, 3300)}

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
        f_pos, comm_result, error = self.follower_servo.read2ByteTxRx(ID, ADDR_PRESENT_POSITION)
        if comm_result == 0:
            l_pos, comm_result, error = self.leader_servo.read2ByteTxRx(ID, ADDR_PRESENT_POSITION)        
            if comm_result == 0:
                follower_maxmin = follower_limits[ID]
                leader_maxmin = leader_limits[ID]
                fraction = (l_pos - leader_maxmin[0])/(leader_maxmin[1]-leader_maxmin[0])
                follower_goal = follower_maxmin[0] + fraction * (follower_maxmin[1]-follower_maxmin[0])
     
                if follower_goal != f_pos:

                    return True, int(follower_goal)
                else:
                    return False, f_pos
            else:
                print(f"Leader servo {ID} read failed")
                return False, f_pos
        else:
            print(f"Follower servo {ID} read failed")
            return False, f_pos

    def move(self, follower_ID, val):
        position, comm_result, error = self.follower_servo.read2ByteTxRx(follower_ID, ADDR_PRESENT_POSITION)
        if comm_result == 0:
            limits = follower_limits[follower_ID]
            if limits[0] <= val <= limits[1]:
                self.follower_servo.WritePosEx(follower_ID, val, 1000, 50)
            else:
                if follower_ID != 6:
                    print(f"Leader out of follower {follower_ID} safe range")
                else:
                    print(f"Leader gripper closed more than required")
        else:
            print(f"Follower servo {follower_ID} read failed")

    def shutdown(self):
            #Home pos
            for i in follower_home.keys():
                self.follower_servo.WritePosEx(i, follower_home[i], 1000, 50)
            time.sleep(3)
            # Disable torque and close port
            for i in follower_home.keys():
                self.follower_servo.write1ByteTxRx(i, ADDR_TORQUE_ENABLE, 0)
            print("✓ Torque disabled")
            self.leader_port.closePort()
            self.follower_port.closePort()
            print("✓ Port closed") 
        


        

