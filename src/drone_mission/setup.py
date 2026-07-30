import os
from glob import glob
from setuptools import setup

package_name = 'drone_mission'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Ahmad',
    maintainer_email='ahmad@example.com',
    description='Autonomous waypoint mission controller for ArduPilot SITL via MAVROS2',
    license='MIT',
    entry_points={
        'console_scripts': [
            'telemetry_monitor = drone_mission.telemetry_monitor:main',
            'flight_controller = drone_mission.flight_controller:main',
            'mission_controller = drone_mission.mission_controller:main',
        ],
    },
)
