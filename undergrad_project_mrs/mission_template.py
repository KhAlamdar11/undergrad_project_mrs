"""Template: how to command the UGV, the UAV and the winch from Python.

Start the simulator first, in hero_sim/startup:

    bash start.sh tether_demo.yaml

then, in another terminal:

    ros2 run undergrad_project_mrs mission_template

It runs three steps, one after another:
  1. the UGV drives a bit to its right, then back      /herover_1/go_to
  2. the UAV takes off, flies a bit, lands             /cf_1/takeoff, /cf_1/go_to, /cf_1/land
  3. the winch pulls the tether in, then lets it out   /winch/cmd_rate
and prints where the object is after each step         /tether/object_pose

The services answer right away and the robot then moves on its own for
`duration` seconds. That's why every call is followed by self.wait().
"""
import time

from crazyflie_interfaces.srv import GoTo, Land, Takeoff
from geometry_msgs.msg import Point, PoseStamped
import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from std_msgs.msg import Float64

# Robot names, as in the scenario config
UGV = 'herover_1'
UAV = 'cf_1'


class Mission(Node):

    def __init__(self):
        super().__init__('mission_template')

        # Services we call
        self.ugv_go_to_client = self.create_client(GoTo, f'/{UGV}/go_to')
        self.uav_takeoff_client = self.create_client(Takeoff, f'/{UAV}/takeoff')
        self.uav_go_to_client = self.create_client(GoTo, f'/{UAV}/go_to')
        self.uav_land_client = self.create_client(Land, f'/{UAV}/land')

        # Topics we publish and read
        self.winch_pub = self.create_publisher(Float64, '/winch/cmd_rate', 10)
        self.object_position = None  # updated by on_object_pose
        self.create_subscription(PoseStamped, '/tether/object_pose', self.on_object_pose, 10)

    def run(self):
        self.get_logger().info('1. UGV: a bit to its right, then back')
        self.ugv_go_to(0.0, -0.5, yaw=0.0, duration=2.0)  # it faces +x, so its right is -y
        self.ugv_go_to(0.0, 0.5, yaw=0.0, duration=2.0)
        self.report_object()

        self.get_logger().info('2. UAV: take off, fly a bit forward, land')
        self.uav_takeoff(height=1.0, duration=2.0)
        self.uav_go_to(0.5, 0.0, 0.0, yaw=0.0, duration=2.0)
        self.uav_land(duration=2.0)
        self.report_object()

        self.get_logger().info('3. Winch: pull the tether in, then let it out')
        self.winch(-0.5, seconds=8.0)  # 4 m in: the slack goes, then the object slides
        self.report_object()
        self.winch(0.5, seconds=8.0)   # 4 m out: slack again, the object stays put
        self.report_object()

        self.get_logger().info('done')

    # ------------------------------------------------------------ UGV

    def ugv_go_to(self, x, y, yaw, duration, relative=True):
        """Drive the UGV to x, y (m) and heading yaw (rad) in `duration` s.

        relative=True: x, y are an offset from where it is now (world frame).
        relative=False: x, y are a position in the world frame.
        """
        request = GoTo.Request()
        request.relative = relative
        request.goal = Point(x=float(x), y=float(y))  # goal.z is ignored for the UGV
        request.yaw = float(yaw)
        request.duration = Duration(seconds=duration).to_msg()
        self.call(self.ugv_go_to_client, request)
        self.wait(duration)

    # ------------------------------------------------------------ UAV

    def uav_takeoff(self, height, duration):
        """Rise straight up to `height` (m) in `duration` s."""
        request = Takeoff.Request()
        request.height = float(height)
        request.duration = Duration(seconds=duration).to_msg()
        self.call(self.uav_takeoff_client, request)
        self.wait(duration)

    def uav_go_to(self, x, y, z, yaw, duration, relative=True):
        """Fly to x, y, z (m) and heading yaw (rad) in `duration` s.

        relative=True: x, y, z are an offset from where it is now (world frame).
        relative=False: x, y, z are a position in the world frame.
        """
        request = GoTo.Request()
        request.relative = relative
        request.goal = Point(x=float(x), y=float(y), z=float(z))
        request.yaw = float(yaw)
        request.duration = Duration(seconds=duration).to_msg()
        self.call(self.uav_go_to_client, request)
        self.wait(duration)

    def uav_land(self, duration):
        """Come straight down to the floor in `duration` s."""
        request = Land.Request()
        request.height = 0.0
        request.duration = Duration(seconds=duration).to_msg()
        self.call(self.uav_land_client, request)
        self.wait(duration)

    # ------------------------------------------------------------ winch

    def winch(self, rate, seconds):
        """Run the winch at `rate` m/s for `seconds` s, then stop it.

        rate < 0 pulls the tether in, rate > 0 lets it out. The sim caps it
        at the scenario's max_reel_speed (0.5 m/s in tether_demo.yaml).
        The winch keeps the last rate it got until the next message, so it
        has to be told to stop: rate 0.
        """
        while self.winch_pub.get_subscription_count() == 0:  # the sim isn't listening yet
            self.get_logger().info('waiting for /winch/cmd_rate (is the simulator running?)',
                                   throttle_duration_sec=2.0)
            self.wait(0.1)
        self.winch_pub.publish(Float64(data=float(rate)))
        self.wait(seconds)
        self.winch_pub.publish(Float64(data=0.0))

    # ------------------------------------------------------------ object

    def on_object_pose(self, msg):
        self.object_position = msg.pose.position

    def report_object(self):
        p = self.object_position
        if p is None:
            self.get_logger().info('no /tether/object_pose yet')
        else:
            self.get_logger().info(f'object at x={p.x:.2f}, y={p.y:.2f}')

    # ------------------------------------------------------------ helpers

    def call(self, client, request):
        """Call a service and wait for its answer."""
        while not client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(f'waiting for {client.srv_name} (is the simulator running?)')
        future = client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        return future.result()

    def wait(self, seconds):
        """Wait `seconds` s while still receiving messages (like on_object_pose).

        Don't use time.sleep() for this: nothing is received while it sleeps.
        """
        end = time.monotonic() + seconds
        while rclpy.ok() and time.monotonic() < end:
            rclpy.spin_once(self, timeout_sec=0.05)


def main(args=None):
    rclpy.init(args=args)
    mission = Mission()
    try:
        mission.run()
    except KeyboardInterrupt:
        pass
    finally:
        mission.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
