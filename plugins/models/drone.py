from time import sleep, time
from threading import Thread
from pymavlink import mavutil
from pymavlink.dialects.v20 import common
from PyQt5.QtCore import pyqtSignal, QObject
from math import sqrt, cos, sin, radians
from pioneersim.simulation.model import Model

class SimpleDroneModel(QObject):
    change_position = pyqtSignal()
    change_color = pyqtSignal()

    def __init__(self, x = 0.0, y= 0.0, z = 0.0, yaw = 0.0, speed = 60, battery_need = True, battery_capacity = 1300, battery_voltage = 7.2):
        super().__init__()
        battery_time = battery_capacity * 27.7
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.speed = speed
        self.color = (0, 0, 0)
        self.__temp_sensor_data = []
        self.__current_battery = battery_time

        self.takeoff_status = False
        self.preflight_status = False
        self.inprogress = False
        self.__last_position = (x, y, z, yaw)
        self.__max_battery = battery_time
        self.__battery_voltage = battery_voltage

        if battery_need:
            Thread(target=self.__battery_target).start()

    def stop(self):
        self.__current_battery = -1
        
    def __battery_target(self):
        while self.__current_battery > 0.0:
            if self.preflight_status:
                self.__current_battery -= 1
                sleep(1)
            else:
                self.__current_battery -= 0.5
                sleep(1)

    def set_color(self, r = 0, g = 0, b = 0):
        self.change_color.emit()
        self.color = (r, g, b)

    def check_pos(self, x : float, y : float, z : float, yaw : float) -> bool:
        return (x, y, z, yaw) != self.__last_position

    def set_pos(self, x : float, y : float, z : float, yaw : float):
        self.__last_position = (x, y, z, yaw)

    def go_to_point(self, x : float, y : float, z : float):
        delta_x = x - self.x
        delta_y = y - self.y
        delta_z = z - self.z
        l = sqrt(delta_x ** 2 + delta_y ** 2 + delta_z ** 2)
        for _ in range(int(l * 100) - 1):
            if self.inprogress:
                self.x += delta_x / l * 0.01
                self.y += delta_y / l * 0.01
                self.z += delta_z / l * 0.01
                self.change_position.emit()
            else:
                return
            sleep(1.0 / self.speed)

    def update_yaw(self, angle : float):
        old_angle = int(self.yaw)
        pri = 1
        if angle < 0.0:
            pri = -1
        for new_angle in range(old_angle, old_angle + int(angle), pri):
            if self.inprogress:
                self.yaw = new_angle
                self.change_position.emit()
            else:
                return
            sleep(1.0 / self.speed)

    def takeoff(self):
        self.inprogress = True
        for _ in range(100):
            self.z += 0.01
            self.change_position.emit()
            sleep(1.0 / self.speed)
        self.takeoff_status = True
        self.inprogress = False

    def landing(self):
        self.inprogress = True
        for _ in range(int(self.z * 100)):
            self.z -= 0.01
            self.change_position.emit()
            sleep(1.0 / self.speed)
        self.takeoff_status = False
        self.preflight_status = False
        self.inprogress = False
        self.set_pos(self.x, self.y, 0.0, self.yaw)

    def disarm(self):
        self.z = 0.0
        self.change_position.emit()
        self.preflight_status = False
        self.takeoff_status = False
        self.set_pos(self.x, self.y, 0.0, self.yaw)
       
    def get_temp(self) -> float:
        if len(self.__temp_sensor_data) != 0:
            return max(self.__temp_sensor_data)
        else:
            return 20.0
        
    def set_temp(self, id, temp):
        if id < len(self.__temp_sensor_data):
            self.__temp_sensor_data[id] = temp
        else:
            self.__temp_sensor_data.append(temp)

    def get_battery(self) -> float:
        return round(self.__current_battery / self.__max_battery * self.__battery_voltage, 1)

class DroneMavlinkModel(Model):
    def __init__(self, hostname='localhost', port=8001, start_position = (0, 0, 0), speed = 60, battery_need = True, battery_capacity = 1300, battery_max = 7.2, battery_off = 6.6, heartbeat_rate = 1/10):
        self.hostname = hostname
        self.online = False
        self.port = port
        self.heartbeat_rate = heartbeat_rate
        self.__item = 0
        self.model = None
        self.master = None
        self.__live_thread = None
        self.__message_thread = None
        self.__speed = speed
        self.__battery_need = battery_need
        self.__battery_capacity = battery_capacity
        self.__battery_max = battery_max
        self.__battery_off = battery_off
        self.__start_position = start_position

    def __heartbeat_send(self):
        self.master.mav.heartbeat_send(
            type = mavutil.mavlink.MAV_TYPE_ONBOARD_CONTROLLER,
            autopilot = mavutil.mavlink.MAV_AUTOPILOT_INVALID,
            base_mode = 0,
            custom_mode = 0,
            system_status = 0
        )

    def __status_send(self):
        self.master.mav.srcComponent = 26
        self.master.mav.local_position_ned_send(int(time()), self.model.x, self.model.y, self.model.z, 0, 0, 0)
        self.master.mav.mission_item_reached_send(self.__item)

    def __distance_sensor_send(self, type):
        if type == common.MAV_DISTANCE_SENSOR_UNKNOWN:
            distance = int(self.model.get_temp())
        elif type == common.MAV_DISTANCE_SENSOR_LASER:
            distance = self.model.z
        self.master.mav.distance_sensor_send(
            time_boot_ms = int(time()),
            min_distance = 0,
            max_distance = 100,
            current_distance = distance,
            type = type,
            id = 0,
            orientation = common.MAV_SENSOR_ROTATION_NONE,
            covariance = 0
        )

    def __live_handler(self):
        while self.online:
            self.__status_send()
            sleep(self.heartbeat_rate / 3)
            self.__distance_sensor_send(common.MAV_DISTANCE_SENSOR_UNKNOWN)
            sleep(self.heartbeat_rate / 3)
            self.__heartbeat_send()
            sleep(self.heartbeat_rate / 3)

    def __command_ack_send(self, command : int):
        self.master.mav.command_ack_send(
            command = command,
            result = common.MAV_RESULT_ACCEPTED
        )

    def __comand_inprogress_send(self, command : int):
        self.master.mav.command_ack_send(
            command = command,
            result = common.MAV_RESULT_IN_PROGRESS
        )

    def __command_denied_send(self, command : int):
        self.master.mav.command_ack_send(
            command = command,
            result = common.MAV_RESULT_DENIED
        )

    def __go_to_point_target(self, x : float, y : float, z : float, yaw : float):
        if self.model.inprogress:
            self.model.inprogress = False
            sleep(0.025)
        self.model.inprogress = True
        self.model.set_pos(x, y, z, yaw)
        self.model.update_yaw(yaw)
        self.model.go_to_point(x, y, z)
        if self.model.inprogress:
            self.__item += 1
        self.model.inprogress = False
        self.model.set_pos(-1, -1, -1, -1)
        
    def __message_handler(self):
        try:
            takeoff_once = False
            landing_once = False
            while self.online:
                if self.model.get_battery() > self.__battery_off:
                    msg = self.master.recv_match(timeout=0.1)
                    if msg is not None:
                        if msg.get_type() == "COMMAND_LONG":
                            if msg.command == 400: # preflight and disarm
                                if not self.model.preflight_status:
                                    self.__command_ack_send(msg.command)
                                    self.model.preflight_status = True
                                else:
                                    self.model.disarm()
                                    self.__command_ack_send(msg.command)
                            elif msg.command == 22: # takeoff
                                if not self.model.takeoff_status:
                                    if not self.model.inprogress:
                                        if not takeoff_once:
                                            Thread(target=self.model.takeoff).start()
                                            takeoff_once = True
                                    else:
                                        self.__comand_inprogress_send(msg.command)
                                else:
                                    if takeoff_once:
                                        self.__command_ack_send(msg.command)
                                        takeoff_once = False
                                    else:
                                        self.__command_denied_send(msg.command)
                            elif msg.command == 21: # landing
                                if self.model.takeoff_status:
                                    if not self.model.inprogress:
                                        if not landing_once:
                                            Thread(target=self.model.landing).start()
                                            landing_once = True
                                    else:
                                        self.__comand_inprogress_send(msg.command)
                                else:
                                    if landing_once:
                                        self.__command_ack_send(msg.command)
                                        landing_once = False
                                    else:
                                        self.__command_denied_send(msg.command)
                            elif msg.command == 31010: # led control
                                self.model.set_color(msg.param2, msg.param3, msg.param4)
                                self.__command_ack_send(msg.command)
                        elif msg.get_type() == "SET_POSITION_TARGET_LOCAL_NED":
                            if self.model.check_pos(msg.x, msg.y, msg.z, msg.yaw):
                                self.master.mav.srcComponent = 1
                                self.master.mav.position_target_local_ned_send(
                                    time_boot_ms = 0,
                                    coordinate_frame = msg.coordinate_frame,
                                    type_mask = msg.type_mask,
                                    x = msg.x,
                                    y = msg.y,
                                    z = msg.z,
                                    vx = msg.vx,
                                    vy = msg.vy,
                                    vz = msg.vz,
                                    afx = msg.afx,
                                    afy = msg.afy,
                                    afz = msg.afz,
                                    yaw_rate = msg.yaw_rate,
                                    yaw = msg.yaw
                                )
                                Thread(target=self.__go_to_point_target, args=(msg.x, msg.y, msg.z, msg.yaw)).start()
                        elif msg.get_type() == "RC_CHANNELS_OVERRIDE":
                            channel_1 = msg.chan1_raw
                            channel_2 = msg.chan2_raw
                            channel_3 = msg.chan3_raw
                            channel_4 = msg.chan4_raw

                            delta_x = 0.0
                            delta_y = 0.0
                            delta_z = 0.0
                            delta_yaw = 0.0

                            drone_x = 0.0
                            drone_y = 0.0

                            if channel_2 < 1500:
                                delta_yaw = 5
                            elif channel_2 > 1500:
                                delta_yaw = -5

                            if channel_4 < 1500:
                                drone_x = -0.05
                            elif channel_4 > 1500:
                                drone_x = 0.05

                            if channel_3 < 1500:
                                drone_y = -0.05
                            elif channel_3 > 1500:
                                drone_y = 0.05

                            x1 = drone_y * sin(radians(360 - self.model.yaw + delta_yaw))
                            y1 = drone_y * cos(radians(360 - self.model.yaw + delta_yaw))

                            x2 = drone_x * cos(radians(self.model.yaw + delta_yaw))
                            y2 = drone_x * sin(radians(self.model.yaw + delta_yaw))

                            delta_x = x1 + x2
                            delta_y = y1 + y2

                            if channel_1 < 1500:
                                delta_z = -0.05
                            elif channel_1 > 1500:
                                delta_z = 0.05

                            self.__go_to_point_target(self.model.x + delta_x, self.model.y + delta_y, self.model.z + delta_z, delta_yaw)
                            sleep(0.0001)
                else:
                    if self.model.inprogress:
                        self.model.inprogress = False
                        sleep(0.025)
                    Thread(target=self.model.landing).start()
                    break
        except Exception as e:
            print(str(e))
            self.online = False
        print(f'{self.hostname}:{self.port} offline')
        self.master.close()
        self.model.stop()

    def set_speed(self, speed : int):
        if self.model is not None:
            self.model.speed = speed

    def set_start_position(self, x : float, y : float, z : float):
        if not self.online:
            self.__start_position = (x, y, z)

    def set_hostname(self, hostname : str):
        if not self.online:
            self.hostname = hostname

    def set_port(self, port : int):
        if not self.online:
            self.port = port

    def get_led_color(self) -> list[int]:
        return self.model.color

    def get_position(self) -> tuple[float, float, float]:
        if self.model is not None:
            return self.model.x, self.model.y, self.model.z
        else:
            return None, None, None

    def get_yaw(self) -> float:
        return self.model.yaw

    def get_start_position(self) -> tuple[float, float, float]:
        return self.__start_position

    def get_status(self) -> dict:
        if self.model is not None:
            return {"arm" : self.model.preflight_status or self.model.takeoff_status, "power" : f'{self.model.get_battery()} V.'}
        else:
            return {"arm" : False, "power" : "0 V."}

    def get_temp(self) -> float:
        return self.model.get_temp()
    
    def set_temp(self, id, temp):
        self.model.set_temp(id, temp)
    
    def start(self):
        self.model = SimpleDroneModel(*self.__start_position, 0, self.__speed, self.__battery_need, self.__battery_capacity, self.__battery_max)
        self.master = mavutil.mavlink_connection(f'udpin:{self.hostname}:{self.port}', source_component=26, dialect = 'common')
        self.online = True

        self.__live_thread = Thread(target=self.__live_handler)
        self.__live_thread.daemon = True

        self.__message_thread = Thread(target=self.__message_handler)
        self.__message_thread.daemon = True

        self.__live_thread.start()
        self.__message_thread.start()

    @classmethod
    def pack(cls, data) -> dict:
        data_dict = {}
        data_dict['hostname'] = data[0]
        data_dict['port'] = data[1]

        position_dict = {}
        position_dict['x'] = data[2][0]
        position_dict['y'] = data[2][1]
        position_dict['z'] = data[2][2]

        data_dict['start_position'] = position_dict

        color_dict = {}
        color_dict['r'] = data[3][0]
        color_dict['g'] = data[3][1]
        color_dict['b'] = data[3][2]

        data_dict['trajectory_color'] = color_dict
        return data_dict

    @classmethod
    def unpack(cls, data) -> list:
        position = (data['start_position']['x'], data['start_position']['y'], data['start_position']['z'])
        color = (data['trajectory_color']['r'], data['trajectory_color']['g'], data['trajectory_color']['b'])
        return [data['hostname'], data['port'], position, color]

    @classmethod
    def model_name(cls) -> str:
        return 'drone'

    @classmethod
    def status(cls) -> bool:
        return True

    @classmethod
    def check_fields(cls, fields) -> bool:
        return fields[0] != ''

    @classmethod
    def get_description(cls, field) -> str:
        return f"Хост: {field[0]}, Порт: {field[1]}, Стартовая позиция: {field[2]}, Цвет траектории: {field[3]}"

    @classmethod
    def transform(cls, fields = None) -> list:
        if fields is None:
            return ["", 0, (0.0, 0.0, 0.0), (0, 0, 0)]
        else:
            return [str(fields[0]), int(fields[1]), (float(fields[2]), float(fields[3]), float(fields[4])), (int(fields[5]), int(fields[6]), int(fields[7]))]
