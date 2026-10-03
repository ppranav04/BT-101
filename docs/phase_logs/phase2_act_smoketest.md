# Phase 2 — ACT Smoke Test (single camera)

Does the full imitation-learning pipeline work end to end on BT-101 (record → inspect → train → roll out), and what breaks first? This run uses a single fixed camera on purpose. The goal is to find pipeline problems that have nothing to do with camera count before the wrist camera arrives. Getting a good success rate is not the goal here.

## Camera setup

### Goal

Get the LG Smart Cam streaming at a fixed 30 fps into LeRobot, with a config that stays valid when the wrist camera is added later.

### Method

The LG Smart Cam enumerates as a standard UVC device. No driver is needed.

```bash
v4l2-ctl --list-devices                          # LG Smart Cam -> /dev/video2, /dev/video3
v4l2-ctl -d /dev/video2 --all | grep -A3 "Device Caps"   # Video Capture
v4l2-ctl -d /dev/video3 --all | grep -A3 "Device Caps"   # Metadata Capture only
v4l2-ctl -d /dev/video2 --list-formats-ext
lsusb -t                                         # LG cam on port 13 at 480M
```

`/dev/video2` is the capture node. `/dev/video3` carries metadata only.

### Results

The camera has a USB-C connector, but it negotiates **480M (USB 2.0)**.

| Format | 640×480 | 1280×720 | 1920×1080 |
|---|---|---|---|
| MJPG | 30 fps | 30 fps | 30 fps |
| YUYV | 30 fps | 10 fps | 5 fps |

The YUYV limits follow from raw bandwidth (YUYV = 2 bytes/pixel) against the ~24 MB/s practical ceiling for a single isochronous USB 2.0 stream:

| YUYV mode | Bandwidth | Fits under ~24 MB/s? |
|---|---|---|
| 640×480 @ 30 | 18.4 MB/s | yes |
| 1280×720 @ 30 | 55.3 MB/s | no, so the camera caps it at 10 fps (18.4 MB/s) |
| 1920×1080 @ 30 | 124.4 MB/s | no, so the camera caps it at 5 fps (20.7 MB/s) |

**Gotcha:** `lerobot-find-cameras` reported a different "default profile" on two runs: 1920×1080 @ 5 fps the first time, 640×480 @ 30 fps the second. V4L2 reopens a device in whatever format the last program set, so there is no stable default. The config therefore pins `fourcc`, width, height and fps explicitly. LeRobot raises an error if the camera refuses the requested format, so a wrong format fails loudly.

### Decision

- **MJPG, 640×480, 30 fps**, camera key **`front`**.
- **Why MJPG over YUYV:** at 640×480 both reach 30 fps, but two raw YUYV streams (~37 MB/s) won't fit on the shared USB 2.0 bus once the wrist cam is added. YUYV's "no compression artifacts" advantage mostly disappears anyway, because LeRobot re-encodes every frame to AV1 when it saves the dataset.
- **Why 640×480:** LeRobot's ACT has no resize/crop step, so the recorded resolution goes straight into the ResNet-18 backbone and sets VRAM per sample. The original ALOHA/ACT work used 480×640.
- **Placement:** fixed, raised oblique view from the front-left of the follower. A top-down view hides the ball behind the gripper exactly at the moment of grasp and makes height nearly invisible. The oblique view keeps the jaws and the object visible together. The trade-off is perspective: the far side of the table gets fewer pixels per cm.
- **Device paths:** `/dev/v4l/by-id/...-video-index0` for the camera and `/dev/serial/by-id/...` for both arm boards, so the paths survive replugging. `/dev/videoN` and `ttyACMn` numbering depends on plug-in order.

## Environment

The LeRobot clone was a dev snapshot (v0.5.1-155) with an unexplained local patch in `camera_opencv.py`, and the web docs (`/main/`) didn't match its API. I rebuilt it from scratch:

- `lerobot` conda env, Python 3.12, ffmpeg 9.0.2 (conda-forge, with libsvtav1)
- torch 2.11.0+cu130 installed **first** from the cu130 index, before LeRobot (RTX 5070 / sm_120, driver 595.91)
- LeRobot **v0.6.1** (tag), editable, extras `core_scripts,training,feetech`
- `[all]` failed to build `egl_probe`, a simulation dependency that needs cmake and isn't needed here

Teleop worked on the new env with the existing calibration files, without recalibrating.

## Task

**Pick up a crushed paper ball and put it in a fixed box.**

- I first planned a Hot Wheels car, but it rolls when the gripper bumps it and sits very low. The paper ball is easier to grasp, looks the same from every angle, and is light enough that a drop is harmless.
- The box position and the start region are taped on the table. The same ball is used for every demo and every rollout.
- **Success:** the ball is fully inside the box and released, and the gripper is out of the box.

## Dataset

`ppranav04/bt101_smoketest_20261003_214244` (private, LeRobot dataset v3.0)

| | |
|---|---|
| Episodes | 15 |
| Frames | 11,071 (~6.2 min at 30 fps) |
| Episode length | 19.5–31.4 s (`episode_time_s=35`, every episode ended manually with →) |
| Features | `observation.images.front` (480×640, AV1), `observation.state` (6), `action` (6) |

Inspection (`lerobot-dataset-viz` plus a per-episode check of the parquet data):

- No empty episodes. Motion starts 1–3 s in, and each episode ends with 2–5 s at rest.
- No episode hit the timeout.
- **The rest pose is inconsistent:** `wrist_flex` at the end of an episode ranges from 43 to 74, and episode 2 ends with the gripper open.
- During fast moves the follower lags the leader by up to 28.6 units (p99 ≤ 19). That gap between `action` (leader) and `observation.state` (follower) is in the data.
- Every timestamp is exactly 33.33 ms apart, but that proves nothing about real loop timing: LeRobot writes `timestamp = frame_index / fps`. Only the video shows dropped frames.

Earlier test runs (`bt101_smoketest_try1_*`, 2 episodes each) caught one empty episode and three episodes that ran into the old 25 s limit. That's why `episode_time_s` went from 25 to 35.

## Training

### VRAM probe (300 steps)

The open question from Phase 1 was whether 8 GB of VRAM is enough.

| | |
|---|---|
| Baseline (desktop) | 616 MiB |
| Peak during training | 3,438 MiB, so **ACT uses ~2.8 GB** at batch 8, 1 camera, 640×480 |
| GPU utilization | **98–99%**: GPU-bound, data loading keeps up |
| Speed | ~0.15 s/step |

**8 GB is enough for single-camera ACT at batch 8, with ~4.7 GB of headroom.** This needs re-measuring with two cameras.

### Run

ACT with LeRobot defaults (ResNet-18 backbone, `chunk_size=100`, `n_action_steps=100`, lr 1e-5, batch 8):

- **20,000 steps.** One epoch = 11,071 / 8 ≈ 1,384 steps, so this is ≈ **14.5 epochs**.
- Checkpoints every 5k steps (5k, 10k, 15k, 20k), 198 MB of weights each (591 MB with optimizer state).
- Logged to wandb project `bt101`, with checkpoint artifact upload disabled.
- Policy: `ppranav04/act_bt101_smoketest` (private).

<!-- TODO: add the wandb loss curve screenshot (docs/media/act/) -->

## Rollout

`lerobot-rollout --strategy.type=base`, with the same camera config and task string as in recording, `--duration=35`, and `--robot.max_relative_target=30`. That last limit is off by default. I sized it just above the largest leader–follower gap in the demos (28.6), so demo-like motion is unaffected but wild jumps get limited. The follower was placed in the rest pose by hand before each trial.

### Result

The policy has learned the **structure** of the task but not the **precision**:

1. It moves toward the ball area.
2. It stops **short** of the ball.
3. It closes the gripper on nothing.
4. It carries nothing to the box, as if the grasp had worked.

<!-- TODO: per-trial table: checkpoint, position, seen/new, miss direction + distance, reached / grasped / in box / back to rest -->

### Hypotheses (to test)

1. **Depth ambiguity with one camera.** From a single oblique view, distance along the camera's line of sight is the hardest thing to judge. Test: are the misses mostly toward/away from the camera? If so, the wrist cam should fix it.
2. **Too few demos to fill in between positions.** 15 demos spread over the start region. Test: compare positions I demonstrated against new positions between them. Misses only at new positions → generalization. Misses everywhere → precision or data quality.
3. **It can't notice a missed grasp.** Every demo succeeded, so the policy has never seen a miss followed by a retry. With `n_action_steps=100` it also executes ~3.3 s of actions without looking at the camera again, so "close → lift → go to box" can be committed before any new observation. The gripper position (`observation.state[5]`) differs between closing on the ball and closing on nothing, but that signal was never linked to "retry" in the data.


## Reproduce

```bash
# Record
lerobot-record \
    --robot.type=so101_follower \
    --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE6081270-if00 \
    --robot.id=BT101_follower \
    --robot.cameras="{ front: {type: opencv, index_or_path: /dev/v4l/by-id/usb-EBP641570013AD08VH_LG_Smart_Cam_01.00.00-video-index0, width: 640, height: 480, fps: 30, fourcc: MJPG}}" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE6082952-if00 \
    --teleop.id=BT101_leader \
    --display_data=true \
    --dataset.repo_id=ppranav04/bt101_smoketest \
    --dataset.single_task="Pick up the paper ball and put it in the box" \
    --dataset.num_episodes=15 \
    --dataset.episode_time_s=35 \
    --dataset.reset_time_s=15 \
    --dataset.private=true \
    --dataset.streaming_encoding=true \
    --dataset.encoder_threads=2

# Train
lerobot-train \
  --dataset.repo_id=ppranav04/bt101_smoketest_20261003_214244 \
  --policy.type=act \
  --policy.device=cuda \
  --output_dir=$HOME/bt101_outputs/train/act_smoketest \
  --job_name=act_smoketest \
  --steps=20000 \
  --save_freq=5000 \
  --wandb.enable=true \
  --wandb.project=bt101 \
  --wandb.disable_artifact=true \
  --policy.repo_id=ppranav04/act_bt101_smoketest \
  --policy.private=true

# Roll out (one trial per run)
lerobot-rollout \
  --strategy.type=base \
  --policy.path=$HOME/bt101_outputs/train/act_smoketest/checkpoints/020000/pretrained_model \
  --robot.type=so101_follower \
  --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE6081270-if00 \
  --robot.id=BT101_follower \
  --robot.cameras="{ front: {type: opencv, index_or_path: /dev/v4l/by-id/usb-EBP641570013AD08VH_LG_Smart_Cam_01.00.00-video-index0, width: 640, height: 480, fps: 30, fourcc: MJPG}}" \
  --robot.max_relative_target=30 \
  --task="Pick up the paper ball and put it in the box" \
  --duration=35 \
  --display_data=true
```
