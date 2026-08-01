# BT-101

A voice-commanded physical AI robot built on the SO-101 platform - moving from teleoperation, through imitation learning, to autonomous manipulation, capped by a voice-responsive expressive assistant.

BT nods to BT-7274 (Titanfall 2): the tight-loop trust between a pilot and a machine acting as an extension of intent.

101 is double meaning: the SO-101 arm hardware, and an honest marker that this is a foundational, first-principles pass at the discipline.

This project is deliberately built **from scratch** where it matters: leader-follower and joystick teleop were first validated using LeRobot's own built-in examples, then reimplemented from the ground up (raw serial protocol, servo register maps, control loop) to build real understanding of the control loop rather than treating the library as a black box.

## Project Arc

- [x] **Phase 1 - Teleoperation**
  - [x] Joystick teleop (Xbox controller -> Feetech servos), from scratch
  - [ ] Leader-follower teleop, from scratch *(in progress)*
- [ ] **Phase 2 - Imitation Learning** - record demonstrations, train ACT and Diffusion Policy models
- [ ] **Phase 3 - Autonomous Manipulation** - validate trained policies on real pick-and-place tasks
- [ ] **Phase 4 - Expressive Embodied Assistant** *(capstone)* - voice-responsive companion: listens via STT, generates expressive motion while talking

## Demo

**Joystick teleop:** Xbox controller driving the SO-101 follower arm in real time:

![Joystick teleop demo](docs/media/joystick/Joystick_Servo.gif)

*(Leader-follower demo to be added once that phase is complete.)*

## Hardware

- **Manipulator:** SO-101 leader-follower arm pair: open-source design by [TheRobotStudio](https://github.com/TheRobotStudio/SO-ARM100), in collaboration with Hugging Face.
- **Servos:** Feetech STS3215 serial bus servos, driven over USB (CDC-ACM serial) via two Feetech/Waveshare driver boards.

## Repository Structure

```
BT-101/
├── teleop/
│   ├── joystick/          - Xbox controller → servo teleop (from scratch, hardware-validated)
│   └── leader-follower/   - leader-follower teleop (from scratch, in progress)
└── docs/media/            - demo gifs and photos of the physical rig
```

## Setup
- Run the joystick demo:
  ```
  cd teleop/joystick
  python controller.py
  ```

## Acknowledgments

- [TheRobotStudio](https://github.com/TheRobotStudio/SO-ARM100) - SO-101 / SO-ARM100 hardware design (Apache 2.0)
- [Hugging Face LeRobot](https://github.com/huggingface/lerobot) - robot learning framework (Apache 2.0), used to validate hardware before from-scratch reimplementation
- 3D-printed parts sourced from TheRobotStudio's SO-ARM100 repo and/or community remixes - check individual file licenses (some are CC-BY-SA and require attribution)

## License

MIT — see [LICENSE](LICENSE).
