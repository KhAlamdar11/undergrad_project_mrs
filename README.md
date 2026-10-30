# undergrad_project_mrs

Your ROS 2 package for the multi-robot tether task in [hero_sim](https://github.com/KhAlamdar11/hero_sim). It contains one script, `mission_template.py`, which shows how to command each part of the task from Python:

- the ground robot (UGV) drives a bit to its right and back;
- the drone (UAV) takes off, flies a bit and lands;
- the winch pulls the tether in, then lets it out.

Use it as a starting point for your own code.

## Setup

Set up hero_sim first (see its README). Then, inside the docker container:

```bash
cd ~/ros2_ws/src
git clone https://github.com/KhAlamdar11/undergrad_project_mrs.git
cd ~/ros2_ws
colcon build --symlink-install --packages-up-to undergrad_project_mrs
source ~/ros2_ws/install/setup.bash
```

## Run the template

Start the simulator with the tether scenario:

```bash
cd ~/ros2_ws/src/hero_sim/startup
bash start.sh tether_demo.yaml
```

Then, in another terminal:

```bash
ros2 run undergrad_project_mrs mission_template
```

Watch it in RViz. The terminal prints where the object is after each step.

## What the template uses

| Name | Kind | Type | |
|---|---|---|---|
| `/herover_1/go_to` | service | `crazyflie_interfaces/srv/GoTo` | drive the UGV to x, y, yaw |
| `/cf_1/takeoff` | service | `crazyflie_interfaces/srv/Takeoff` | rise to `height` |
| `/cf_1/go_to` | service | `crazyflie_interfaces/srv/GoTo` | fly to x, y, z, yaw |
| `/cf_1/land` | service | `crazyflie_interfaces/srv/Land` | come down to `height` |
| `/winch/cmd_rate` | topic, you publish | `std_msgs/Float64` | m/s: negative pulls in, positive lets out. Kept until the next message |
| `/tether/object_pose` | topic, you read | `geometry_msgs/PoseStamped` | where the object is |

The hero_sim README lists everything else: `cmd_vel` for the UGV, the tether feedback topics, the obstacles.

## Add your own script

1. Put it next to the template: `undergrad_project_mrs/my_mission.py`, with a `main()` function.
2. Register it in `setup.py`, under `console_scripts`:
   ```python
   'my_mission = undergrad_project_mrs.my_mission:main',
   ```
3. Build again (`colcon build --symlink-install --packages-up-to undergrad_project_mrs`), then `ros2 run undergrad_project_mrs my_mission`.

With `--symlink-install`, later edits to the script need no rebuild. Rebuild only after changing `setup.py` or adding files.
