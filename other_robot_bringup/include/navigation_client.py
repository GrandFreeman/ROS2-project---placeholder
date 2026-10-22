import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.action.client import ClientGoalHandle, GoalStatus

from nav2_msgs.action import NavigateToPose
#from geometry_msgs.msg import PoseStamped




class NavigationClient(Node):

    def __init__(self):
        super().__init__("navigation_client")
        self.action_client = ActionClient(
            self,
            NavigateToPose,
            "navigate_to_pose"
        )

        self.goal_accepted = False
        self.navigation_complete = False
        self.navigation_successful = False

        self.locations = {    
            "room1": (10.97, 4.0, 0.0),
            "room2": (15.92, -4.0, 0.0),
            "medical_shop": (26.36, -6.18, 0.0),
            "initial_pose": (-0.04, -0.06, 0.0)
        }

        self.get_logger().info("Navigation client initialized")

    def navigate_to_pose(self, x, y, z, w=1.0):

        #self.goal_accepted = False
        #self.navigation_complete = False
        #self.navigation_successful = False

        while not self.action_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().info("Waiting for action server...")
        

        goal_msg = NavigateToPose.Goal()

        goal_msg.pose.header.frame_id = "map"
    
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.position.z = z
    
        goal_msg.pose.pose.orientation.w = w
        goal_msg.pose.pose.orientation.x = 0.0
        goal_msg.pose.pose.orientation.y = 0.0
        goal_msg.pose.pose.orientation.z = 0.0

        self.get_logger().info(f"Navigating to position: x={x:.2f}, y={y:.2f}, z={z:.2f}")

        future = self.action_client.send_goal_async(
        goal_msg,
        feedback_callback=self.feedback_callback
    )
        future.add_done_callback(self.goalResponse_callback)

        while rclpy.ok() and not self.navigation_complete:
            rclpy.spin_once(self, timeout_sec=0.1)

        time.sleep(2)
        return self.navigation_successful 


    def deliver_medicine(self, order_number):

    
        shop = self.locations["medical_shop"]

        if (order_number == "1"):
            room = self.locations["room1"]
        elif (order_number == "2"):
            room = self.locations["room2"]
        else:
            return False

        initial = self.locations["initial_pose"]


        self.get_logger().info("Moving to medical shop to collect medicine...")
        if not self.navigate_to_pose(*shop):
            self.get_logger().info("Failed to reach medical shop")
            return False

        self.get_logger().info("Collecting medicine...")
        time.sleep(15)

        self.get_logger().info("Delivering medicine...")
        if not self.navigate_to_pose(*room):
            self.get_logger().info("Failed to reach room")
            return False

        time.sleep(10)
        self.get_logger().info("Returning to initial position...")
        if not self.navigate_to_pose(*initial):
            self.get_logger().info("Failed to return to initial position")
            return False

        self.get_logger().info("Delivery completed!")

    

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(
            f"Distance remaining = {feedback.distance_remaining}" 
            )
        
    def goalResponse_callback(self, future):
        self.goal_handle_: ClientGoalHandle = future.result()
        if self.goal_handle_.accepted:
            self.get_logger().info("Goal got accepted")
            self.goal_handle_.get_result_async().add_done_callback(
                self.result_callback)
        else:
            self.get_logger().info("Goal got rejected")
        

    def result_callback(self, future):
        status = future.result().status
        #result = future.result().result
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info("Success")
            self.navigation_successful = True
        elif status == GoalStatus.STATUS_ABORTED:
            self.get_logger().error("Aborted")
            self.navigation_successful = False
        elif status == GoalStatus.STATUS_CANCELED:
            self.get_logger().warn("Canceled")
            self.navigation_successful = False
        self.navigation_complete = True
        #self.get_logger().info("Result: " + str(result))


def main():

    rclpy.init()

    navigator = NavigationClient()

    while rclpy.ok():

        navigator.get_logger().info("Enter order number (1 for Room1, 2 for Room2, q to quit):")

        order = input("Order: ")

        if order == "q" or order == "Q":
            break
        if order != "1" and order != "2":
            navigator.get_logger().info("invalid")
            continue

        try:
            navigator.deliver_medicine(order)
            rclpy.spin_once(navigator)

        except Exception as e:
            navigator.get_logger().error(
                f"Error during navigation: {e}"
            )

    rclpy.shutdown()


if __name__ == "__main__":
    main()
