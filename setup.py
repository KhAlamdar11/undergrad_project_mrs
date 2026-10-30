from setuptools import find_packages, setup

package_name = 'undergrad_project_mrs'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            # <name you type after ros2 run> = <package>.<file>:<function>
            'mission_template = undergrad_project_mrs.mission_template:main',
        ],
    },
)
