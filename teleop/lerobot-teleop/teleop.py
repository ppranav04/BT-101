from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig
from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig

robot_config = SO101FollowerConfig(
    port="/dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE6081270-if00",
    id="BT101_follower",
)

teleop_config = SO101LeaderConfig(
    port="/dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE6082952-if00",
    id="BT101_leader",
)

robot = SO101Follower(robot_config)
teleop_device = SO101Leader(teleop_config)
robot.connect()
teleop_device.connect()

while True:
    action = teleop_device.get_action()
    robot.send_action(action)