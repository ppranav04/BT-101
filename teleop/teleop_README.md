# Teleop

Two from scratch teleop modes (my code) and a LeRobot API test.
Linux only.
Ports are hardcoded:  
`/dev/ttyACM1 - Leader`  
`/dev/ttyACM0 - Follower`  
Check ports using `lerobot-find-ports`

## To run joystick teleop and leader follower (Self-coded)

```bash
pip install ftservo-python-sdk pygame pyserial
```

> Do not install this into the `lerobot` env.

| Mode | Run (from repo root) | Stop |
|---|---|---|
| Joystick | `python teleop/joystick/joystick_teleop.py` | START button |
| Leader-follower | `python teleop/leader_follower_teleop.py` | Spacebar (homes, then shuts down) |


## To run LeRobot API Test

``` bash
conda activate lerobot
python3 teleop/lerobot-teleop/teleop.py
```

