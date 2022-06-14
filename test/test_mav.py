from gs_router.python.piosdk import Pioneer
from time import sleep

pioneer = Pioneer(method=2, pioneer_ip='localhost', pioneer_mavlink_port=8001)
print("OKKK")
pioneer.arm()
sleep(2)
pioneer.takeoff()
sleep(3)
pioneer.go_to_local_point(1, 1, 1, yaw = 90)
print("send")
while not pioneer.point_reached(True):
    lps = pioneer.get_local_position_lps()
    if lps is not None:
        print(lps)
pioneer.go_to_local_point(8, 8, 2, yaw = 90)
while not pioneer.point_reached(True):
    lps = pioneer.get_local_position_lps()
    if lps is not None:
        print(lps)
pioneer.land()