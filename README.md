# jetank_description

URDF/xacro robot model for the JeTank robot (primitive geometry — no meshes).
Consumed by Gazebo, MoveIt 2, robot_state_publisher and RViz.

## Model structure

```
base_footprint → base_link → chassis ─┬─ jetank_arm (S1..S5)
                                       │     └─ S5_link → jetank_gripper
                                       │     └─ S1_link → jetank_camera → camera_link → imu_link
                                       ├─ jetank_wheels (4× continuous, diff-drive)
                                       └─ rplidar (laser)
```

- **Top entrypoint:** `urdf/jetank_ros2_control.urdf.xacro`
  - mappings: `use_sim` (true ⇒ `ign_ros2_control/IgnitionSystem`, false ⇒
    `jetank_motor_control/JetankSerialHardware`), `use_ros2_control`.
- **Components:** `urdf/components/{arm,gripper,wheels,camera,lidar,imu}.xacro`
- **Controllers (sim):** `joint_state_broadcaster`, `diff_drive_controller`,
  `gripper_controller` (active), `arm_controller` (inactive unless
  `start_arm_active:=true`). Config in
  `jetank_motor_control/config/jetank_controllers.yaml`.

## Sensors (all have full `gz` sensor blocks — publish in simulation)

| Sensor | Frame | Topic | Rate |
|---|---|---|---|
| 2D lidar (`gpu_lidar`) | `laser` | `/scan` | 10 Hz, 360 samples, 0.05–12 m |
| IMU | `imu_link` | `/imu` | 100 Hz |
| Stereo camera (L/R) | `camera_{left,right}_optical_frame` | `/stereo_camera/{left,right}/image_raw` | 30 Hz, 640×360 |

## ⚠️ Known issues (flagged for maintainer)

These are **verified in sim** and need URDF edits:

1. **IMU moves with the arm (matches hardware — not a URDF bug).**
   `jetank_ros2_control.urdf.xacro:71` mounts `imu_sensor` on `camera_link`, a
   child of `S1_link` (the rotating arm base, line 66). This is **physically
   accurate** — the real IMU is bolted to the camera, so the model is correct and
   should stay as-is. Caveat for fusion: because the IMU rides the arm, its
   orientation is **only valid for EKF/SLAM/Nav2 when the arm is parked**. If you
   need a base-fixed IMU for continuous fusion, that's a *hardware* change (relocate
   the sensor), not a model fix.

2. **Camera gz sensor referenced to the optical frame.** `components/camera.xacro:68,105`
   put the `<sensor type="camera">` on `camera_{left,right}_optical_frame`, which
   carries the standard optical rotation `rpy="-1.5708 0 -1.5708"`. Ignition
   cameras image along the frame **+X**, but optical +X points to the robot's
   right → the simulated image is ~90° off in RViz. **Fix:** reference the
   `<sensor>` to a forward‑X frame (e.g. `camera_link` or a dedicated
   `camera_*_frame`) and keep `<ignition_frame_id>` on the optical frame so ROS
   images stay in the optical convention.

3. **Verify two mounts.**
   - `components/lidar.xacro` `laser_joint rpy="0 0 π"` rotates the scan's zero
     reference 180° (full 360° coverage is intact, but the angle origin is
     mirrored — confirm it matches the physical RPLidar zero).
   - Camera mounted on `S1_link` (arm) means the camera view swings with the
     arm — confirm intended vs. a fixed chassis/mast mount.
