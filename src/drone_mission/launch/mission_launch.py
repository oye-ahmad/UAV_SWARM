from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    fcu_url_arg = DeclareLaunchArgument(
        'fcu_url', default_value='udp://:14550@127.0.0.1:14557',
        description='MAVROS FCU connection URL (matches ArduPilot SITL output)'
    )
    gcs_url_arg = DeclareLaunchArgument(
        'gcs_url', default_value='', description='Optional GCS bridge URL'
    )
    takeoff_alt_arg = DeclareLaunchArgument(
        'takeoff_altitude', default_value='10.0'
    )
    hover_duration_arg = DeclareLaunchArgument(
        'hover_duration', default_value='5.0'
    )
    battery_failsafe_arg = DeclareLaunchArgument(
        'battery_failsafe_pct', default_value='20.0'
    )

    mavros_launch_file = os.path.join(
        get_package_share_directory('mavros'), 'launch', 'apm.launch'
    )

    # MAVROS's own launch files ship in XML (frontend) format, not Python.
    # AnyLaunchDescriptionSource auto-detects the format instead of assuming
    # one, which is what broke here originally.
    mavros_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(mavros_launch_file),
        launch_arguments={
            'fcu_url': LaunchConfiguration('fcu_url'),
            'gcs_url': LaunchConfiguration('gcs_url'),
        }.items()
    )

    telemetry_node = Node(
        package='drone_mission',
        executable='telemetry_monitor',
        name='telemetry_monitor',
        output='screen'
    )

    flight_controller_node = Node(
        package='drone_mission',
        executable='flight_controller',
        name='flight_controller',
        output='screen'
    )

    mission_controller_node = Node(
        package='drone_mission',
        executable='mission_controller',
        name='mission_controller',
        output='screen',
        parameters=[{
            'takeoff_altitude': LaunchConfiguration('takeoff_altitude'),
            'hover_duration': LaunchConfiguration('hover_duration'),
            'battery_failsafe_pct': LaunchConfiguration('battery_failsafe_pct'),
        }]
    )

    return LaunchDescription([
        fcu_url_arg,
        gcs_url_arg,
        takeoff_alt_arg,
        hover_duration_arg,
        battery_failsafe_arg,
        mavros_launch,
        telemetry_node,
        flight_controller_node,
        mission_controller_node,
    ])
