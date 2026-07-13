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

These are **verified in sim**:

1. **IMU moves with the arm (matches hardware — not a URDF bug).**
   `jetank_ros2_control.urdf.xacro:71` mounts `imu_sensor` on `camera_link`, a
   child of `S1_link` (the rotating arm base, line 66). This is **physically
   accurate** — the real IMU is bolted to the camera, so the model is correct and
   should stay as-is. Caveat for fusion: because the IMU rides the arm, its
   orientation is **only valid for EKF/SLAM/Nav2 when the arm is parked**. If you
   need a base-fixed IMU for continuous fusion, that's a *hardware* change (relocate
   the sensor), not a model fix.

2. **Verify two mounts.**
   - `components/lidar.xacro` `laser_joint rpy="0 0 π"` rotates the scan's zero
     reference 180° (full 360° coverage is intact, but the angle origin is
     mirrored — confirm it matches the physical RPLidar zero).
   - Camera mounted on `S1_link` (arm) means the camera view swings with the
     arm — confirm intended vs. a fixed chassis/mast mount.

---

## ROS 2 API

`jetank_description` is a **pure robot-description package** (ament_cmake). It contains **no runtime nodes, executables, launch files, or message/service/action definitions of its own** — there is no `src/`, `launch/`, `scripts/`, Python module, or `msg/`/`srv/`/`action/` directory. It therefore publishes/subscribes to **no ROS 2 topics directly** and exposes no services or actions.

What it provides is the URDF/xacro robot model (primitive geometry, no meshes), consumed by `robot_state_publisher`, RViz, MoveIt 2 and Gazebo (Fortress/Ignition) in sibling packages.

### Provided artifacts

| Type | Path | Notes |
|---|---|---|
| Top-level entrypoint | `urdf/jetank_ros2_control.urdf.xacro` | Main robot model with `ros2_control` integration |
| Robot/component xacros | `urdf/jetank.xacro`, `urdf/components/{arm,gripper,wheels,camera,lidar,imu}.xacro` | Component macros |
| Sensor gz blocks | `urdf/components/{camera,lidar,imu}.xacro`, `urdf/sensors.gazebo` | Ignition `<sensor>` definitions |
| Materials / properties | `urdf/materials.xacro`, `urdf/properties.xacro`, `urdf/jetank_parameters.xacro`, `urdf/macros.xacro` | Shared xacro definitions |

The CMakeLists installs `urdf/`, `meshes/`, `launch/`, `config/` only if present; only `urdf/` exists in the tree.

### Top-level xacro arguments (`urdf/jetank_ros2_control.urdf.xacro`)

| Arg | Default | Effect |
|---|---|---|
| `use_sim` | `false` | `true` ⇒ `ign_ros2_control/IgnitionSystem`; `false` ⇒ `jetank_motor_control/JetankSerialHardware` hardware interface |
| `use_ros2_control` | `true` | Includes the `ros2_control` block + `jetank_motor_control/config/ros2_control.xacro` |

### Sensor topics declared in the model (Gazebo/Ignition transport)

These are **not** topics this package's nodes publish (it has none) — they are `<topic>` names inside the URDF `<sensor>` blocks. They are bridged to ROS 2 by the simulation/bridge configuration in sibling packages and exist **only in simulation**.

| Sensor | gz topic | Ignition frame id | Update rate | Config |
|---|---|---|---|---|
| 2D lidar (`gpu_lidar`, name `rplidar`) | `scan` | `laser` | 10 Hz | 360 samples, range 0.18–12.0 m (`components/lidar.xacro`) |
| IMU (`imu_sensor`) | `imu` | `imu_link` | 100 Hz | `components/imu.xacro` |
| Stereo camera left (`stereo_camera_left`) | `stereo_camera/left/image_raw` | `camera_left_optical_frame` | 30 Hz | 640×360 (`components/camera.xacro`) |
| Stereo camera right (`stereo_camera_right`) | `stereo_camera/right/image_raw` | `camera_right_optical_frame` | 30 Hz | 640×360 (`components/camera.xacro`) |

ROS 2 message types (e.g. `sensor_msgs/LaserScan`, `sensor_msgs/Imu`, `sensor_msgs/Image`) and the final remapped ROS topic names depend on the ros_gz bridge in `jetank_simulation`, which is outside this package — verify there for the actual ROS-side wire names.

## Tests

`test/test_urdf.py` exercises the package deliverable — it expands the shipped
xacro models to URDF via the `xacro` API (no ROS runtime) and asserts on the
resulting XML:

- **`test_jetank_xacro_expands_to_robot`** — `jetank.xacro` expands to a
  non-empty `<robot>` with core/component links (`base_link`, `chassis`,
  `imu_link`, `camera_base_plate_link`, `arm_base_link`, `gripper_base_link`,
  `laser`) and exactly **6** `*_wheel` links.
- **`test_top_entrypoint_expands_without_ros2_control`** — the top entrypoint
  `jetank_ros2_control.urdf.xacro` (with `use_ros2_control:=false`, so it stays
  self-contained and pulls in no sibling package) expands and contains the core
  frames plus the full `S1..S5` arm chain.
- **`test_robot_name_is_jetank`** (parametrized over both entrypoints) — the
  `<robot>` root is named `jetank` (the name consumed by RViz/MoveIt/Gazebo).

Wired via `ament_cmake_pytest` in `CMakeLists.txt`.

Run them:

```bash
# standalone pytest
pixi run -- bash -c 'cd src/jetank_description && python -m pytest test/ -q'
# under colcon
colcon test --packages-select jetank_description
colcon test-result --verbose
```
