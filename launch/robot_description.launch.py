"""
Canonical robot_description bring-up for the JeTank model.

Single include point for publishing the robot model: expands the canonical
entrypoint ``urdf/jetank_ros2_control.urdf.xacro`` and starts
``robot_state_publisher`` with the result. Launch arguments map 1:1 onto the
model's xacro args (``use_sim``, ``use_ros2_control``, ``hardware``) so every
consumer (visualisation, sim, MoveIt, hardware bringup) publishes the same
geometry. Include this file instead of running xacro yourself:

    IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('jetank_description'),
                         'launch', 'robot_description.launch.py')),
        launch_arguments={'use_ros2_control': 'false'}.items(),
    )
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """Expand the canonical xacro model and start robot_state_publisher."""
    pkg_share = get_package_share_directory('jetank_description')
    xacro_file = os.path.join(pkg_share, 'urdf', 'jetank_ros2_control.urdf.xacro')

    use_sim = LaunchConfiguration('use_sim')
    use_ros2_control = LaunchConfiguration('use_ros2_control')
    hardware = LaunchConfiguration('hardware')
    use_sim_time = LaunchConfiguration('use_sim_time')

    robot_description = Command([
        FindExecutable(name='xacro'), ' ', xacro_file,
        ' use_sim:=', use_sim,
        ' use_ros2_control:=', use_ros2_control,
        ' hardware:=', hardware,
    ])

    return LaunchDescription([
        # Defaults mirror the xacro arg defaults in jetank_ros2_control.urdf.xacro.
        DeclareLaunchArgument(
            'use_sim',
            default_value='false',
            description='true: Gazebo (IgnitionSystem) ros2_control backend; '
                        'false: the non-sim backend selected by "hardware"'
        ),
        DeclareLaunchArgument(
            'use_ros2_control',
            default_value='true',
            description='Include the ros2_control block '
                        '(pulls in jetank_motor_control/config/ros2_control.xacro)'
        ),
        DeclareLaunchArgument(
            'hardware',
            default_value='mock',
            description='Non-sim ros2_control backend: "mock" '
                        '(mock_components/GenericSystem, no motors move) or '
                        '"serial" (real JetankSerialHardware Feetech servos). '
                        'Ignored when use_sim:=true'
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'
        ),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{
                'robot_description': ParameterValue(robot_description, value_type=str),
                'use_sim_time': use_sim_time,
            }]
        ),
    ])
