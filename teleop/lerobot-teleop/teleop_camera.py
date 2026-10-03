import signal
import time

from lerobot.cameras.opencv import OpenCVCameraConfig
from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig
from lerobot.utils.robot_utils import precise_sleep
from lerobot.utils.visualization_utils import (
    init_visualization,
    log_visualization_data,
    shutdown_visualization,
)

FOLLOWER_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE6081270-if00"
LEADER_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE6082952-if00"
LG_CAM = "/dev/v4l/by-id/usb-EBP641570013AD08VH_LG_Smart_Cam_01.00.00-video-index0"

DISPLAY = "rerun"
TARGET_HZ = 30
TIME_PER_FRAME = 1.0 / TARGET_HZ

robot_config = SO101FollowerConfig(
    port=FOLLOWER_PORT,
    id="BT101_follower",
    cameras={
        # TODO: add fourcc=... from your format decision; rename "top" if the mount isn't top-down
        "front": OpenCVCameraConfig(index_or_path=LG_CAM, width=640, height=480, fps=TARGET_HZ),
    },
)
teleop_config = SO101LeaderConfig(port=LEADER_PORT, id="BT101_leader")

robot = SO101Follower(robot_config)
teleop_device = SO101Leader(teleop_config)


def safe_cleanup():
    # Ignore a second Ctrl+C so cleanup can't be interrupted halfway
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    print("\nShutting down...")

    # Each step is independent: one failure must not skip the others
    for name, device in (("follower", robot), ("leader", teleop_device)):
        try:
            if device.is_connected:
                device.disconnect()
        except Exception as e:
            print(f"Failed to disconnect {name}: {e}")

    try:
        shutdown_visualization(DISPLAY)
    except Exception as e:
        print(f"Failed to shut down visualization: {e}")

    print("Done.")


try:
    init_visualization(DISPLAY, session_name="teleoperation")
    robot.connect()
    teleop_device.connect()
    print("Teleop running. Put the LEADER in rest pose, then press Ctrl+C to exit.")

    while True:
        start_time = time.perf_counter()

        observation = robot.get_observation()
        action = teleop_device.get_action()
        robot.send_action(action)
        log_visualization_data(DISPLAY, observation=observation, action=action)

        precise_sleep(max(TIME_PER_FRAME - (time.perf_counter() - start_time), 0.0))

except KeyboardInterrupt:
    pass
finally:
    safe_cleanup()