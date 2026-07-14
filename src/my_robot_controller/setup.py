from setuptools import find_packages, setup
from glob import glob 
import os
package_name = 'my_robot_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (
            os.path.join('share',package_name,'launch'),
            glob('my_robot_controller/launch/*.py'),
        )
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='barkat',
    maintainer_email='suneela.sz@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            "ahmad_node = my_robot_controller.my_first_node:main",
            "subscriber_node = my_robot_controller.subscriber:main"
        ],
    },
)
