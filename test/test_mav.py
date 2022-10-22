from gs_router.python.piosdk import Pioneer
from time import sleep

port = int(input("Port: "))
pioneer = Pioneer(method=2, pioneer_ip='localhost', pioneer_mavlink_port=port, logger=False)
print("OKKK")
pioneer.led_control(255, 255, 0, 0)
pioneer.arm()
sleep(2)
pioneer.takeoff()
sleep(3)
# pioneer.go_to_local_point(1, 1, 1, yaw = 90)
# print("send")
# while not pioneer.point_reached(True):
#     lps = pioneer.get_local_position_lps()
#     if lps is not None:
#         print(lps)
# pioneer.go_to_local_point(8, 8, 2, yaw = 90)
# while not pioneer.point_reached(True):
#     lps = pioneer.get_local_position_lps()
#     if lps is not None:
#         print(lps)
for i in range(10):
    pioneer.send_rc_channels(1500, 2000, 1500, 1500) # поворот по yaw
    # while not pioneer.point_reached(True):
    #     pass
    sleep(0.0001)

print("YAW UPDATE FINISH")

for i in range(100):
    pioneer.send_rc_channels(
        channel_1 = 1500, 
        channel_2 = 1500,
        channel_3 = 2000,
        channel_4 = 2000) # движение вперед
    sleep(0.0001)

for i in range(100):
    pioneer.send_rc_channels(
        channel_1 = 1500, 
        channel_2 = 1500,
        channel_3 = 1000,
        channel_4 = 1000) # движение вперед
    sleep(0.0001)
pioneer.land()