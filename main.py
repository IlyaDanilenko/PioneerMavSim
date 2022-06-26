import sys, json
from enum import Enum
from ObjectVisualizator.main import SettingsManager, VisWidget, VisualizationWorld, remapRGB
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QListWidget, QPushButton, QInputDialog, QStackedWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QLabel, QLineEdit, QMessageBox, QScrollArea, QListWidgetItem, QDialog, QComboBox
from pymavlink import mavutil
from pymavlink.dialects.v20 import common
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from threading import Thread
from time import sleep, time
from math import sqrt, hypot

class Language:
    words = {
        "fire" : "Пожар",
        "drone" : "Коптер",
        "temp" : "Температура",
        "arm" : "Двигатели заведены",
        "True" : "Да",
        "False" : "Нет",
        "workspace" : "Рабочее пространство",
        "polygon" : "Полигон",
        "objects" : "Объекты",
        "simulation" : "Симуляция",
        "axis" : "Оси",
        "sensitivity" : "Чувствительность",
        "background" : "Фон",
        "camera" : "Камера",
        "position" : "Позиция",
        "angle" : "Угол",
        "trajectory" : "Траектория",
        "need" : "Необходимость",
        "marker" : "Маркер",
        "distance" : "Расстояние",
        "scale" : "Масштаб",
        "color" : "Цвет",
        "image_name" : "Путь до изображения",
        "path" : "Путь",
        "speed" : "Скорость",
        "min_temp" : "Мин. Температура",
        "max_temp" : "Макс. Температура",
        "static" : "Статичность",
        "radius" : "Радиус"
    }

    def __init__(self):
        pass

    def get_word(self, word : str, language = "rus"):
        try:
            if language == "rus":
                return self.words[word]
            else:
                return self.words.keys()[list(self.words.values()).index(word)]
        except KeyError:
            return word

class SimulationSettings:
    def __init__(self, simulation : dict):
        self.speed = simulation['drone']['speed']
        self.fire_static = simulation['fire']['static']
        self.fire_radius = simulation['fire']['radius']
        self.fire_min_temp = simulation['fire']['min_temp']
        self.fire_max_temp = simulation['fire']['max_temp']

class SimulationSettingManager(SettingsManager):
    def __init__(self):
        self.simulation = None
        self.__raw_data = None
        self.__path = None
        super().__init__()

    def load(self, path : str):
        self.__path = path
        self.__raw_data = super().load(path)
        self.simulation = SimulationSettings(self.__raw_data['simulation'])
        return self.__raw_data

    def __dict__(self):
        return self.__raw_data

    def update_from_dict(self, data_dict : dict):
        self.__raw_data = data_dict

    def write(self):
        with open(self.__path, 'w') as f:
            json.dump(self.__raw_data, f)

class FireModel:
    def __init__(self, x = 0.0, y = 0.0, min_temp = 20.0, max_temp = 60.0, radius = 0.5):
        self.x = x
        self.y = y
        self.__min_temp = min_temp
        self.__max_temp = max_temp
        self.__radius = radius

    def get_status(self) -> dict:
        return {"temp" : self.temp}

    def get_temp(self, position, static = True):
        dist = lambda p1, p2: hypot((p2[0] - p1[0]), (p2[1] - p1[1]))

        distance = dist(position, (self.x , self.y))

        if distance >= self.__radius:
            return self.__min_temp
        else:
            if static:
                return self.__max_temp
            else:
                k = 1 - distance / self.__radius
                t = k * (self.__max_temp - self.__min_temp)
                return self.__min_temp + t

class DroneModel:
    def __init__(self, x = 0.0, y= 0.0, z = 0.0, yaw = 0.0, speed = 60):
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.speed = speed
        self.color = (0, 0, 0)
        self.temp_sensor_data = 20.0

        self.takeoff_status = False
        self.preflight_status = False
        self.inprogress = False
        self.__last_position = (x, y, z, yaw)

    def set_color(self, r = 0, g = 0, b = 0):
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
            else:
                return
            sleep(1.0 / self.speed)

    def takeoff(self):
        self.inprogress = True
        for _ in range(100):
            self.z += 0.01
            sleep(1.0 / self.speed)
        self.takeoff_status = True
        self.inprogress = False

    def landing(self):
        self.inprogress = True
        for _ in range(int(self.z * 100)):
            self.z -= 0.01
            sleep(1.0 / self.speed)
        self.takeoff_status = False
        self.preflight_status = False
        self.inprogress = False

    def disarm(self):
        self.z = 0.0
        self.preflight_status = False
        self.takeoff_status = False

class MavlinkUnit:
    def __init__(self, hostname='localhost', port=8001, start_position = (0, 0, 0), heartbeat_rate = 1/10, speed = 60):
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
            distance = int(self.model.temp_sensor_data)
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
            sleep(0.05)
        self.model.inprogress = True
        self.model.set_pos(x, y, z, yaw)
        self.model.go_to_point(x, y, z)
        self.model.update_yaw(yaw)
        if self.model.inprogress:
            self.__item += 1
        self.model.inprogress = False
        
    def __message_handler(self):
        try:
            takeoff_once = False
            landing_once = False
            while self.online:
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
        except Exception as e:
            print(str(e))
            self.online = False
            print(f'{self.hostname}:{self.port} offline')
        self.master.close()

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
        return {"arm" : self.model.preflight_status or self.model.takeoff_status}

    def start(self):
        self.model = DroneModel(*self.__start_position, speed = self.__speed)
        self.master = mavutil.mavlink_connection(f'udpin:{self.hostname}:{self.port}', source_component=26, dialect = 'common')
        self.online = True

        self.__live_thread = Thread(target=self.__live_handler)
        self.__live_thread.daemon = True

        self.__message_thread = Thread(target=self.__message_handler)
        self.__message_thread.daemon = True

        self.__live_thread.start()
        self.__message_thread.start()

class ModelType(Enum):
    DRONE = ['drone', MavlinkUnit]
    FIRE = ['fire', FireModel]

class ObjectsManager():
    def __init__(self, visualization : VisualizationWorld, update_time = 0.0002):
        self.visualization = visualization
        self.__update_time = update_time
        self.objects = []

        self.__run = False

    def add_server(self, hostname : str, port : int, start_position : tuple):
        self.objects.append(MavlinkUnit(hostname, port, start_position, speed=self.visualization.settings.simulation.speed))
        self.visualization.add_model(ModelType.DRONE.value[0], start_position, 0)

    def add_fire(self, position : tuple):
        self.objects.append(FireModel(
            *position,
            self.visualization.settings.simulation.fire_min_temp,
            self.visualization.settings.simulation.fire_max_temp,
            self.visualization.settings.simulation.fire_radius
        ))
        self.visualization.add_model(ModelType.FIRE.value[0], (*position, 0.0), 0)
        self.visualization.change_model_color(-1, *remapRGB(200, 44, 31))

    def remove_objects(self, index : int):
        if type(self.objects[index]) == ModelType.DRONE.value[1]:
            self.objects[index].online = False
        self.objects.pop(index)
        self.visualization.remove_model(index)

    def update_drone_info(self, index: int, hostname : str, port : int, position : tuple):
        self.objects[index].set_start_position(*position)
        self.objects[index].set_hostname(hostname)
        self.objects[index].set_port(port)

    def update_fire_info(self, index : int, position : tuple):
        self.visualization.change_model_position(index, (*position, 0), 0)

    def get_status_info_by_type(self, model_type : ModelType) -> list:
        status_data = []
        for object in self.objects:
            if type(object) == model_type.value[1]:
                status_data.append(object.get_status())
        return status_data

    def __drone_target(self, index : int):
        server = self.objects[index]
        while self.__run:
            new_position = server.get_position()
            new_yaw = server.get_yaw()
            model_x, model_y, model_z, model_yaw = self.visualization.get_model_position(index)
            if new_position != (model_x, model_y, model_z) or new_yaw != model_yaw:
                self.visualization.change_model_position(index, new_position, new_yaw)
            new_color = server.get_led_color()
            model_color = self.visualization.get_model_color(index)
            if new_color != model_color:
                if not any(model_color):
                    self.visualization.change_model_color(index)
                else:
                    self.visualization.change_model_color(index, *new_color)

            sleep(self.__update_time)

    def __fire_target(self, index : int):
        fire = self.objects[index]
        static = self.visualization.settings.simulation.fire_static
        while self.__run:
            for index in range(len(self.objects)):
                if type(self.objects[index]) == ModelType.DRONE.value[1]:
                    drone_x, drone_y, _ = self.objects[index].get_position()
                    if drone_x is not None:
                        temp = fire.get_temp((drone_x, drone_y), static)
                        self.objects[index].model.temp_sensor_data = temp

            sleep(self.__update_time)

    def start(self):
        if not self.__run:
            self.__run = True
            for index in range(len(self.objects)):
                if type(self.objects[index]) == ModelType.DRONE.value[1]:
                    self.objects[index].start()
                    Thread(target=self.__drone_target, args=(index, )).start()
                elif type(self.objects[index]) == ModelType.FIRE.value[1]:
                    Thread(target=self.__fire_target, args=(index, )).start()

    def close(self):
        for server in self.objects:
            if type(server) == ModelType.DRONE.value[1]:
                server.online = False
        self.__run = False

class ObjectDialog(QDialog):
    def __init__(self, type = None, fields = None):
        self.__type = type
        if fields is None:
            self.__fields = []
        else:
            self.__fields = fields

        self.__field_inputs = []

        super().__init__()
        self.setWindowModality(Qt.ApplicationModal)

        self.main_layout = QVBoxLayout()

        if self.__type is None:
            self.setWindowTitle("Добавить объект")
            self.setGeometry(200, 200, 500, 50)

            combo = QComboBox()
            combo.addItem(Language().get_word(ModelType.DRONE.value[0]))
            combo.addItem(Language().get_word(ModelType.FIRE.value[0]))
            combo.activated[str].connect(self.__on_active)

            self.main_layout.addWidget(combo)
        else:
            self.setWindowTitle("Изменение объекта")
            self.render_interface()

        self.setLayout(self.main_layout)

    def __on_active(self, text):
        if text == Language().get_word(ModelType.DRONE.value[0]):
            self.__type = ModelType.DRONE
        elif text == Language().get_word(ModelType.FIRE.value[0]):
            self.__type = ModelType.FIRE

        self.render_interface()

    def render_interface(self):
        if self.__type == ModelType.DRONE:
            if len(self.__fields) != 3:
                self.__fields = ["", 0, (0.0, 0.0, 0.0)]
            self.drone_interface(*self.__fields)
        elif self.__type == ModelType.FIRE:
            if len(self.__fields) != 1:
                self.__fields = [(0.0, 0.0)]
            self.fire_interface(*self.__fields)

    def __cancel_click(self):
        self.close()

    def __save_click(self):
        fields = [field.text() for field in self.__field_inputs]
        if self.__type == ModelType.DRONE:
            self.__fields = [str(fields[0]), int(fields[1]), (float(fields[2]), float(fields[3]), float(fields[4]))]
        elif self.__type == ModelType.FIRE:
            self.__fields = [(float(fields[0]), float(fields[1]))]
        self.close()

    def remove_interfaces(self):
        count = self.main_layout.count()
        if count == 1:
            return
        elif count == 7 or count == 4:
            while count != 1:
                self.main_layout.removeWidget(self.main_layout.itemAt(1).widget())
                count = self.main_layout.count()

    def drone_interface(self, hostname : str, port : int, position : tuple):
        self.remove_interfaces()

        hostname_widget = QWidget()
        hostname_layout = QHBoxLayout(hostname_widget)
        hostname_text = QLabel()
        hostname_text.setText('Hostname')
        hostname_input = QLineEdit(hostname)
        hostname_layout.addWidget(hostname_text)
        hostname_layout.addWidget(hostname_input, 100)
        hostname_widget.setLayout(hostname_layout)
        self.__field_inputs.append(hostname_input)

        port_widget = QWidget()
        port_layout = QHBoxLayout(port_widget)
        port_text = QLabel()
        port_text.setText('Port')
        port_input = QLineEdit(str(port))
        port_layout.addWidget(port_text)
        port_layout.addWidget(port_input, 100)
        port_widget.setLayout(port_layout)
        self.__field_inputs.append(port_input)

        x_widget = QWidget()
        x_layout = QHBoxLayout(x_widget)
        x_text = QLabel()
        x_text.setText('Координата X')
        x_input = QLineEdit(str(position[0]))
        x_layout.addWidget(x_text)
        x_layout.addWidget(x_input, 100)
        x_widget.setLayout(x_layout)
        self.__field_inputs.append(x_input)

        y_widget = QWidget()
        y_layout = QHBoxLayout(y_widget)
        y_text = QLabel()
        y_text.setText('Координата Y')
        y_input = QLineEdit(str(position[1]))
        y_layout.addWidget(y_text)
        y_layout.addWidget(y_input, 100)
        y_widget.setLayout(y_layout)
        self.__field_inputs.append(y_input)

        z_widget = QWidget()
        z_layout = QHBoxLayout(z_widget)
        z_text = QLabel()
        z_text.setText('Координата Z')
        z_input = QLineEdit(str(position[2]))
        z_layout.addWidget(z_text)
        z_layout.addWidget(z_input, 100)
        z_widget.setLayout(z_layout)
        self.__field_inputs.append(z_input)

        control = QWidget()
        control_layout = QGridLayout(control)
        cancel_button = QPushButton()
        cancel_button.setText("Отменить")
        cancel_button.clicked.connect(self.__cancel_click)
        save_button = QPushButton()
        save_button.setText("Сохранить")
        save_button.clicked.connect(self.__save_click)
        control_layout.addWidget(cancel_button, 0, 0)
        control_layout.addWidget(save_button, 0, 1)
        control.setLayout(control_layout)

        self.main_layout.addWidget(hostname_widget)
        self.main_layout.addWidget(port_widget)
        self.main_layout.addWidget(x_widget)
        self.main_layout.addWidget(y_widget)
        self.main_layout.addWidget(z_widget)
        self.main_layout.addWidget(control)

    def fire_interface(self, position : tuple):
        self.remove_interfaces()

        x_widget = QWidget()
        x_layout = QHBoxLayout(x_widget)
        x_text = QLabel()
        x_text.setText('Координата X')
        x_input = QLineEdit(str(position[0]))
        x_layout.addWidget(x_text)
        x_layout.addWidget(x_input, 100)
        x_widget.setLayout(x_layout)
        self.__field_inputs.append(x_input)

        y_widget = QWidget()
        y_layout = QHBoxLayout(y_widget)
        y_text = QLabel()
        y_text.setText('Координата Y')
        y_input = QLineEdit(str(position[1]))
        y_layout.addWidget(y_text)
        y_layout.addWidget(y_input, 100)
        y_widget.setLayout(y_layout)
        self.__field_inputs.append(y_input)

        control = QWidget()
        control_layout = QGridLayout(control)
        cancel_button = QPushButton()
        cancel_button.setText("Отменить")
        cancel_button.clicked.connect(self.__cancel_click)
        save_button = QPushButton()
        save_button.setText("Сохранить")
        save_button.clicked.connect(self.__save_click)
        control_layout.addWidget(cancel_button, 0, 0)
        control_layout.addWidget(save_button, 0, 1)
        control.setLayout(control_layout)

        self.main_layout.addWidget(x_widget)
        self.main_layout.addWidget(y_widget)
        self.main_layout.addWidget(control)

    def exec_(self) -> list[str, list]:
        super().exec_()
        return self.__type, self.__fields

class MenuWidgetItem(QWidget):
    def __init__(self, type = ModelType.DRONE, field = None):
        self.__type = type
        self.__field = field

        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)

        layout = QHBoxLayout(self)
        self.text = QLabel()
        self.__set_text()

        button = QPushButton(self)
        button.setText('Изменить')
        button.clicked.connect(self.__button_click)

        layout.addWidget(self.text, 100)
        layout.addWidget(button)
        self.setLayout(layout)

    def __button_click(self):
        dialog = ObjectDialog(self.__type, self.__field)
        _, self.__field = dialog.exec_()
        self.__set_text()

    def __set_text(self):
        if self.__type == ModelType.DRONE:
            self.text.setText(f"TYPE: DRONE, HOSTNAME: {self.__field[0]}, PORT: {self.__field[1]}, START POSITION: {self.__field[2]}")
        elif self.__type == ModelType.FIRE:
            self.text.setText(f"TYPE: FIRE, POSITION: {self.__field[0]}")

    def get_start_data(self) -> tuple:
        return self.__type, self.__field

class MenuWidget(QWidget):
    def __init__(self, add_func, remove_func, sim_func, set_func):
        super().__init__()

        self.main_layout = QGridLayout(self)

        self.list = QListWidget(self)
        self.list.setContentsMargins(0, 0, 0, 100)
        self.list.clicked.connect(self.__remove_button_activate)

        self.add_button = QPushButton(self)
        self.add_button.setText("Добавить объект")
        self.add_button.clicked.connect(add_func)

        self.remove_button = QPushButton(self)
        self.remove_button.setText("Удалить объект")
        self.remove_button.setEnabled(False)
        self.remove_button.clicked.connect(remove_func)

        self.sim_button = QPushButton(self)
        self.sim_button.setText("Включить симуляцию")
        self.sim_button.clicked.connect(sim_func)

        self.set_button = QPushButton(self)
        self.set_button.setText("Настройки")
        self.set_button.clicked.connect(set_func)

        buttons_group = QWidget(self)
        buttons_group_layout = QGridLayout(self)
        buttons_group_layout.addWidget(self.set_button, 0, 0)
        buttons_group_layout.addWidget(self.add_button, 0, 1)
        buttons_group_layout.addWidget(self.remove_button, 0, 2)
        buttons_group_layout.addWidget(self.sim_button, 0, 3)
        buttons_group.setLayout(buttons_group_layout)

        self.main_layout.addWidget(self.list, 0, 0)
        self.main_layout.addWidget(buttons_group, 1, 0)

        self.setLayout(self.main_layout)

    def __add(self, widget):
        new_item = QListWidgetItem()
        new_item.setSizeHint(widget.sizeHint()) 
        self.list.addItem(new_item)
        self.list.setItemWidget(new_item, widget)

    def add_drone(self, hostname : str, port : int, start_position : tuple):
        self.__add(MenuWidgetItem(ModelType.DRONE, [hostname, port, start_position]))

    def add_fire(self, position: tuple):
        self.__add(MenuWidgetItem(ModelType.FIRE, [position]))

    def remove_current(self) -> int:
        row = self.list.currentRow()
        self.list.takeItem(row)
        self.remove_button.setEnabled(False)
        return row

    def get_items(self) -> list[MenuWidgetItem]:
        items = [self.list.item(x) for x in range(self.list.count())]
        widgets = []
        for item in items:
            widgets.append(self.list.itemWidget(item))
        return widgets

    def __remove_button_activate(self):
        self.remove_button.setEnabled(True)

class StatusWidget(QWidget):
    def __init__(self, server : ObjectsManager):
        self.__server = server
        super().__init__()

        self.main_layout = QVBoxLayout(self)

        self.__updateble_label = []
        self.setGeometry(200, 200, 500, 500)
        self.setWindowTitle("Статус")

        self.setContentsMargins(0, 0, 0, 0)

    def update(self):
        if self.main_layout.count() != 0:
            self.main_layout.removeWidget(self.main_layout.itemAt(0).widget())
        self.__updateble_label = []
        scroll_layout = QVBoxLayout(self)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea(self)
        scroll_area.setContentsMargins(0, 0, 0, 0)

        widget = QWidget(scroll_area)
        widget.setLayout(scroll_layout)
        widget.setContentsMargins(0, 0, 0, 0)

        status = self.__server.get_status_info_by_type(ModelType.DRONE)

        font = QFont("Times", 16)
        for index in range(len(status)):
            status_widget = QWidget(self)
            layout = QVBoxLayout(status_widget)
            drone_name = QLabel(f'{Language().get_word(ModelType.DRONE.value[0])} - {index + 1}')
            drone_name.setFont(font)
            layout.addWidget(drone_name)
            for name, value in status[index].items():
                value_str = f'\t{Language().get_word(name)} : {Language().get_word(str(value))}'
                self.__updateble_label.append(QLabel(value_str))
                layout.addWidget(self.__updateble_label[-1])
            status_widget.setLayout(layout)
            scroll_layout.addWidget(status_widget)

        scroll_area.setWidget(widget)
        self.main_layout.addWidget(scroll_area)

    def __update_label_target(self, type):
        while not self.isHidden():
            status = self.__server.get_status_info_by_type(type)
            update_index = 0
            for index in range(len(status)):
                for name, value in status[index].items():
                    self.__updateble_label[update_index].setText(f'\t{Language().get_word(name)} : {Language().get_word(str(value))}')
                    update_index += 1
            sleep(0.01)

    def open(self):
        if self.isHidden():
            self.show()
            Thread(target=self.__update_label_target, args=(ModelType.DRONE,)).start()
        else:
            self.hide()

class SimWidget(QWidget):
    def __init__(self, world, main, server, escape_callback):
        self.__escape_callback = escape_callback
        super().__init__()

        self.status_widget = StatusWidget(server)

        self.vis_widget = VisWidget(world, main, server)
        self.vis_widget.setContentsMargins(0, 0, 0 , 100)
        self.vis_widget.close = self.__escape_callback

        self.center_button = QPushButton(self)
        self.center_button.setText("Центр сверху")
        self.center_button.clicked.connect(self.__center_button_click)

        self.right_down_button = QPushButton(self)
        self.right_down_button.setText("Правый нижний угол")
        self.right_down_button.clicked.connect(self.__right_down_button_click)

        self.right_up_button = QPushButton(self)
        self.right_up_button.setText("Правый верхний угол")
        self.right_up_button.clicked.connect(self.__right_up_button_click)

        self.left_up_button = QPushButton(self)
        self.left_up_button.setText("Левый верхний угол")
        self.left_up_button.clicked.connect(self.__left_up_button_click)

        self.left_down_button = QPushButton(self)
        self.left_down_button.setText("Левый нижний угол")
        self.left_down_button.clicked.connect(self.__left_down_button_click)

        self.trajectory_button = QPushButton(self)
        if world.settings.workspace.trajectory:
            self.trajectory_button.setText("Скрыть траекторию")
        else:
            self.trajectory_button.setText("Показать траекторию")
        self.trajectory_button.clicked.connect(self.__trajectories_button_click)

        self.status_button = QPushButton(self)
        self.status_button.setText("Панель статусов")
        self.status_button.clicked.connect(self.status_widget.open)

        buttons_group = QWidget(self)
        buttons_group_layout = QHBoxLayout(self)
        buttons_group_layout.setContentsMargins(5, 10, 5, 5)
        buttons_group_layout.addWidget(self.center_button)
        buttons_group_layout.addWidget(self.right_down_button)
        buttons_group_layout.addWidget(self.right_up_button)
        buttons_group_layout.addWidget(self.left_up_button)
        buttons_group_layout.addWidget(self.left_down_button)
        buttons_group_layout.addWidget(self.trajectory_button)
        buttons_group_layout.addWidget(self.status_button)
        buttons_group.setLayout(buttons_group_layout)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(buttons_group)
        self.main_layout.addWidget(self.vis_widget, 1)
        self.setLayout(self.main_layout)

    def keyReleaseEvent(self, event):
        self.vis_widget.keyReleaseEvent(event)

    def __center_button_click(self):
        self.vis_widget.world.camera.setPos(self.vis_widget.world.settings.polygon.scale.get_x(), self.vis_widget.world.settings.polygon.scale.get_z(), self.vis_widget.world.settings.polygon.scale.get_y() * 2.5)
        self.vis_widget.world.camera.setHpr(0, -90, 0)

    def __right_down_button_click(self):
        self.vis_widget.world.camera.setPos(self.vis_widget.world.settings.polygon.scale.get_x() * 3.5, -self.vis_widget.world.settings.polygon.scale.get_z() * 1.5, self.vis_widget.world.settings.polygon.scale.get_y() * 1.5)
        self.vis_widget.world.camera.setHpr(45, -45, 0)

    def __right_up_button_click(self):
        self.vis_widget.world.camera.setPos(self.vis_widget.world.settings.polygon.scale.get_x() * 3.5, self.vis_widget.world.settings.polygon.scale.get_z() * 3.5, self.vis_widget.world.settings.polygon.scale.get_y() * 1.5)
        self.vis_widget.world.camera.setHpr(135, -45, 0)

    def __left_up_button_click(self):
        self.vis_widget.world.camera.setPos(-self.vis_widget.world.settings.polygon.scale.get_z() * 1.5, self.vis_widget.world.settings.polygon.scale.get_z() * 3.5, self.vis_widget.world.settings.polygon.scale.get_y() * 1.5)
        self.vis_widget.world.camera.setHpr(-135, -45, 0)

    def __left_down_button_click(self):
        self.vis_widget.world.camera.setPos(-self.vis_widget.world.settings.polygon.scale.get_z() * 1.5, -self.vis_widget.world.settings.polygon.scale.get_z() * 1.5, self.vis_widget.world.settings.polygon.scale.get_y() * 1.5)
        self.vis_widget.world.camera.setHpr(-45, -45, 0)

    def __trajectories_button_click(self):
        visible = not self.vis_widget.world.get_trajectory_visible()
        self.vis_widget.world.set_trajectory_visible(visible)
        if visible:
            self.trajectory_button.setText("Скрыть траекторию")
        else:
            self.trajectory_button.setText("Показать траекторию")

class SettingsMenuItemWidget(QWidget):
    def __init__(self, name : str, data):
        self.name = name
        self.__data = data
        self.__inputs = []
        super().__init__()

        self.setContentsMargins(0, 0, 0, 0)

        main_layout = QVBoxLayout(self)
        self.scroll_layout = QVBoxLayout(self)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea(self)
        scroll_area.setContentsMargins(0, 0, 0, 0)

        widget = QWidget(scroll_area)
        widget.setLayout(self.scroll_layout)
        widget.setContentsMargins(10, 0, 10, 0)

        self._add_param(self.__data)
        scroll_area.setWidget(widget)
        main_layout.addWidget(scroll_area)
                
        self.setLayout(main_layout)

    def _add_param(self, data_dict : dict, lavel = 1):
        for key in data_dict:
            font = QFont("Times", 24 // lavel)
            label = QLabel(self)
            label.setText(Language().get_word(key))
            label.setFont(font)
            if type(data_dict[key]) == dict:
                self.scroll_layout.addWidget(label)
                self._add_param(data_dict[key], lavel + 1)
            else:
                widget = QWidget(self)
                widget_layout = None
                widget_layout = QHBoxLayout(widget)
                widget_layout.setContentsMargins(0, 0, 0, 0)
                edit = QLineEdit(self)
                edit.setText(str(data_dict[key]))
                self.__inputs.append(edit)
                widget_layout.addWidget(label)
                widget_layout.addWidget(edit, 1)
                widget.setLayout(widget_layout)
                self.scroll_layout.addWidget(widget)

    def get_data_dict(self, data_dict=None, inputs=None) -> dict:
        if inputs is None:
            inputs = []
            for edit in self.__inputs:
                text = edit.text()
                if text.lower() == "true":
                    inputs.append(True)
                elif text.lower() == "false":
                    inputs.append(False)
                elif text.replace('-', '').isdigit():
                    inputs.append(int(text))
                else:
                    try:
                        inputs.append(float(text))
                    except:
                        inputs.append(text)
        if data_dict is None:
            data_dict = self.__data
        for key in data_dict:
            if type(data_dict[key]) == dict:
                data_dict[key] = self.get_data_dict(data_dict[key], inputs)
            else:
                data_dict[key] = inputs.pop(0)
        return data_dict

class SettingsMenuWidget(QWidget):
    def __init__(self, settings, escape_callback):
        self.settings = settings
        self.__escape_callback = escape_callback
        self.__widgets = []
        super().__init__()

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setContentsMargins(0, 0, 0, 0)

        self.ok_button = QPushButton(self)
        self.ok_button.setText("Применить")
        self.ok_button.clicked.connect(self.ok_button_click)

        self.cancel_button = QPushButton(self)
        self.cancel_button.setText("Отменить")
        self.cancel_button.clicked.connect(self.__escape_callback)

        buttons_group = QWidget(self)
        buttons_group_layout = QHBoxLayout(self)
        buttons_group_layout.setContentsMargins(5, 10, 5, 5)
        buttons_group_layout.addWidget(self.cancel_button)
        buttons_group_layout.addWidget(self.ok_button)
        buttons_group.setLayout(buttons_group_layout)

        for item in self.settings.__dict__().items():
            self.__widgets.append(SettingsMenuItemWidget(*item))
            self.tab_widget.addTab(self.__widgets[-1], Language().get_word(item[0]))

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.tab_widget, 1)
        self.main_layout.addWidget(buttons_group)
        self.setLayout(self.main_layout)

    def ok_button_click(self):
        new_dict = {}
        for element in self.__widgets:
            new_dict[element.name] = element.get_data_dict()

        self.settings.update_from_dict(new_dict)
        QMessageBox.warning(self, "Внимание!", "Настройки будут применены только при следующем запуске")
        self.settings.write()
        self.__escape_callback()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.__escape_callback()

class SimulationWindow(QMainWindow):
    def __init__(self, settings_path : str, save_path : str):
        super().__init__()
        self.setWindowTitle("PioneerMavSim")

        self.__save_path = save_path

        self.settings = SimulationSettingManager()
        self.settings.load(settings_path)

        self.setGeometry(50, 50, 800, 800)
        self.world = VisualizationWorld(self.settings)

        self.objects_manager = ObjectsManager(self.world)

        widgets = QStackedWidget(self)

        self.world_widget = SimWidget(self.world, self, self.objects_manager, self.__back_to_menu)
        self.world_widget.hide()
        self.world_widget.setGeometry(0, 0, self.width(), self.height())

        self.settings_menu = SettingsMenuWidget(self.settings, self.__back_to_menu)
        self.settings_menu.setGeometry(0, 0, self.width(), self.height())
        self.settings_menu.hide()

        self.menu = MenuWidget(self.__add_func, self.__remove_func, self.__start_sim, self.__open_setting)
        self.menu.show()

        widgets.addWidget(self.menu)
        widgets.addWidget(self.world_widget)
        widgets.addWidget(self.settings_menu)

        self.setCentralWidget(widgets)
        self.load(self.__save_path)

    def resizeEvent(self, event):
        self.world_widget.setGeometry(0,0, self.width(), self.height())
        self.settings_menu.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def load(self, path : str):
        try:
            with open(path, 'r') as f:
                loaded_data = json.load(f)
                for data in loaded_data:
                    type = data['type']
                    if type == ModelType.DRONE.value[0]:
                        position = (data['start_position']['x'], data['start_position']['y'], data['start_position']['z'])
                        self.add_drone(data['hostname'], data['port'], position)
                    elif type == ModelType.FIRE.value[0]:
                        position = (data['position']['x'], data['position']['y'])
                        self.add_fire(position)
        except FileNotFoundError:
            pass

    def save(self, path : str):
        with open(path, 'w') as f:
            save_list = []

            items = self.menu.get_items()
            for index in range(len(items)):
                type, data = items[index].get_start_data()
                data_dict = {}
                data_dict['type'] = type.value[0]
                if type == ModelType.DRONE:
                    data_dict['hostname'] = data[0]
                    data_dict['port'] = data[1]

                    position_dict = {}
                    position_dict['x'] = data[2][0]
                    position_dict['y'] = data[2][1]
                    position_dict['z'] = data[2][2]

                    data_dict['start_position'] = position_dict
                elif type == ModelType.FIRE:
                    position_dict = {}
                    position_dict['x'] = data[0][0]
                    position_dict['y'] = data[0][1]
                    data_dict['position'] = position_dict
                save_list.append(data_dict)
                
            json.dump(save_list, f)

    def add_drone(self, hostname : str, port : int, start_position = (0.0, 0.0, 0.0)):
        self.menu.add_drone(hostname, port, start_position)
        self.objects_manager.add_server(hostname, port, start_position)

    def add_fire(self, position = (0.0, 0.0)):
        self.menu.add_fire(position)
        self.objects_manager.add_fire(position)

    def __add_func(self):
        dialog = ObjectDialog()
        type, fields = dialog.exec_()
        if type == ModelType.DRONE:
            if fields[0] != '':
                self.add_drone(*fields)
        elif type == ModelType.FIRE:
            self.add_fire(fields[0])

    def __remove_func(self):
        index = self.menu.remove_current()
        self.objects_manager.remove_objects(index)

    def __start_sim(self):
        self.world.reset_camera()
        self.world.reset_trajectories()
        items = self.menu.get_items()
        for index in range(len(items)):
            type, data = items[index].get_start_data()
            if type == ModelType.DRONE:
                self.objects_manager.update_drone_info(index, *data)
            elif type == ModelType.FIRE:
                self.objects_manager.update_fire_info(index, *data)
            
        self.objects_manager.start()
        self.world_widget.status_widget.update()
        self.menu.hide()
        self.world_widget.show()
        self.menu.clearFocus()
        self.world_widget.setFocus()

    def __open_setting(self):
        self.menu.hide()
        self.menu.clearFocus()
        self.settings_menu.show()
        self.settings_menu.setFocus()

    def closeEvent(self, event):
        self.objects_manager.close()
        self.save(self.__save_path)
        super().closeEvent(event)

    def __back_to_menu(self):
        self.objects_manager.close()
        self.world_widget.hide()
        self.settings_menu.hide()
        self.menu.show()
        self.settings_menu.clearFocus()
        self.world_widget.clearFocus()
        self.menu.setFocus()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = SimulationWindow("settings/settings.json", "save/save.json")
    main.show()

    sys.exit(app.exec_())
