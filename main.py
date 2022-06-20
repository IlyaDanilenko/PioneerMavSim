import sys, json
from ObjectVisualizator.main import SettingsManager, VisWidget, VisualizationWorld
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QListWidget, QPushButton, QInputDialog, QStackedWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QLabel, QLineEdit, QMessageBox, QScrollArea, QListWidgetItem, QDialog
from pymavlink import mavutil
from pymavlink.dialects.v20 import common
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from threading import Thread
from time import sleep, time
from math import sqrt

class SimulationSettings:
    def __init__(self, simulation : dict):
        self.speed = simulation['speed']

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

class MavlinkUnitModel():
    def __init__(self, x = 0.0, y= 0.0, z = 0.0, yaw = 0.0, speed = 60):
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.speed = speed
        self.color = [0, 0, 0]

        self.takeoff_status = False
        self.preflight_status = False
        self.inprogress = False
        self.__last_position = (x, y, z, yaw)

    def set_color(self, r = 0, g = 0, b = 0):
        self.color = [r, g, b]

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
            self.x += delta_x / l * 0.01
            self.y += delta_y / l * 0.01
            self.z += delta_z / l * 0.01
            sleep(1.0 / self.speed)

    def update_yaw(self, angle : float):
        old_angle = int(self.yaw)
        pri = 1
        if angle < 0.0:
            pri = -1
        for new_angle in range(old_angle, old_angle + int(angle), pri):
            self.yaw = new_angle
            sleep(1.0 / self.speed)

    def takeoff(self):
        self.inprogress = True
        for _ in range(0, 200):
            self.z += 0.01
            sleep(1.0 / self.speed)
        self.takeoff_status = True
        self.inprogress = False

    def landing(self):
        self.inprogress = True
        for _ in range(int(self.z * 100), 0, -1):
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
    def __init__(self, hostname='localhost', port=8001, start_position = (0, 0, 0), heartbeat_rate = 1/4, speed = 60):
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
        self.master.mav.mission_item_reached_send(self.__item)
        self.master.mav.srcComponent = 26
        self.master.mav.local_position_ned_send(int(time()), self.model.x, self.model.y, self.model.z, 0, 0, 0)

    def __live_handler(self):
        while self.online:
            self.__status_send()
            sleep(self.heartbeat_rate / 2)
            self.__heartbeat_send()
            sleep(self.heartbeat_rate / 2)

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
        self.model.inprogress = True
        self.model.set_pos(x, y, z, yaw)
        self.model.go_to_point(x, y, z)
        self.model.update_yaw(yaw)
        self.__item += 1
        self.model.inprogress = False

    def __landing_target(self):
        self.model.landing()
        self.__command_ack_send(21)
        
    def __message_handler(self):
        try:
            while self.online:
                msg = self.master.recv_match(timeout=0.1)
                if msg is not None:
                    # print(msg)
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
                                    self.__command_ack_send(msg.command)
                                    Thread(target=self.model.takeoff).start()
                                self.model.inprogress = False
                            else:
                                self.__command_denied_send(msg.command)
                        elif msg.command == 21: # landing
                            if not self.model.inprogress:
                                if self.model.takeoff_status:
                                    self.__command_ack_send(msg.command)
                                    Thread(target=self.__landing_target).start()
                                else:
                                    self.__command_denied_send(msg.command)
                        elif msg.command == 31010: # led control
                            self.model.set_color(msg.param2, msg.param3, msg.param4)
                            self.__command_ack_send(msg.command)
                    elif msg.get_type() == "SET_POSITION_TARGET_LOCAL_NED":
                        if not self.model.inprogress and self.model.check_pos(msg.x, msg.y, msg.z, msg.yaw):
                            Thread(target=self.__go_to_point_target, args=(msg.x, msg.y, msg.z, msg.yaw)).start()
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
        return self.model.x, self.model.y, self.model.z

    def get_yaw(self) -> float:
        return self.model.yaw

    def get_start_position(self) -> tuple[float, float, float]:
        return self.__start_position

    def start(self):
        self.model = MavlinkUnitModel(*self.__start_position, speed = self.__speed)
        self.master = mavutil.mavlink_connection(f'udpin:{self.hostname}:{self.port}', source_component=26, dialect = 'common')
        self.online = True

        self.__live_thread = Thread(target=self.__live_handler)
        self.__live_thread.daemon = True

        self.__message_thread = Thread(target=self.__message_handler)
        self.__message_thread.daemon = True

        self.__live_thread.start()
        self.__message_thread.start()

class DroneManager():
    def __init__(self, visualization : VisualizationWorld, update_time = 0.0001):
        self.visualization = visualization
        self.__update_time = update_time
        self.mavlink_servers = []

        self.__run = False

    def add_server(self, hostname : str, port : int, start_position : tuple):
        self.mavlink_servers.append(MavlinkUnit(hostname, port, start_position, speed=self.visualization.settings.simulation.speed))
        self.visualization.add_model('drone', start_position, 0)

    def remove_server(self, index : int):
        self.mavlink_servers[index].online = False
        self.mavlink_servers.pop(index)
        self.visualization.remove_model(index)

    def update_start_position(self, index : int, start_position : tuple):
        self.mavlink_servers[index].set_start_position(*start_position)

    def update_hostname_port(self, index : int, hostname : str, port : int):
        self.mavlink_servers[index].set_hostname(hostname)
        self.mavlink_servers[index].set_port(port)

    def __target(self, index : int):
        server = self.mavlink_servers[index]
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

    def start(self):
        if not self.__run:
            self.__run = True
            for index in range(len(self.mavlink_servers)):
                self.mavlink_servers[index].start()
                Thread(target=self.__target, args=(index, )).start()

    def close(self):
        for server in self.mavlink_servers:
            server.online = False
        self.__run = False

class MenuItemDialog(QDialog):
    def __init__(self, hostname : str, port : int, position : tuple):
        self.__hostname = hostname
        self.__port = port
        self.__position = position
        super().__init__()
        self.setWindowTitle("Изменение настройки устройства")
        self.setWindowModality(Qt.ApplicationModal)

        layout = QVBoxLayout()

        hostname_widget = QWidget()
        hostname_layout = QHBoxLayout(hostname_widget)
        hostname_text = QLabel()
        hostname_text.setText('Hostname')
        self.__hostname_input = QLineEdit(hostname)
        hostname_layout.addWidget(hostname_text)
        hostname_layout.addWidget(self.__hostname_input, 100)
        hostname_widget.setLayout(hostname_layout)

        port_widget = QWidget()
        port_layout = QHBoxLayout(port_widget)
        port_text = QLabel()
        port_text.setText('Port')
        self.__port_input = QLineEdit(str(port))
        port_layout.addWidget(port_text)
        port_layout.addWidget(self.__port_input, 100)
        port_widget.setLayout(port_layout)

        x_widget = QWidget()
        x_layout = QHBoxLayout(x_widget)
        x_text = QLabel()
        x_text.setText('Координата X')
        self.__x_input = QLineEdit(str(position[0]))
        x_layout.addWidget(x_text)
        x_layout.addWidget(self.__x_input, 100)
        x_widget.setLayout(x_layout)

        y_widget = QWidget()
        y_layout = QHBoxLayout(y_widget)
        y_text = QLabel()
        y_text.setText('Координата Y')
        self.__y_input = QLineEdit(str(position[1]))
        y_layout.addWidget(y_text)
        y_layout.addWidget(self.__y_input, 100)
        y_widget.setLayout(y_layout)

        z_widget = QWidget()
        z_layout = QHBoxLayout(z_widget)
        z_text = QLabel()
        z_text.setText('Координата Z')
        self.__z_input = QLineEdit(str(position[2]))
        z_layout.addWidget(z_text)
        z_layout.addWidget(self.__z_input, 100)
        z_widget.setLayout(z_layout)

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

        layout.addWidget(hostname_widget)
        layout.addWidget(port_widget)
        layout.addWidget(x_widget)
        layout.addWidget(y_widget)
        layout.addWidget(z_widget)
        layout.addWidget(control)

        self.setLayout(layout)

    def __cancel_click(self):
        self.close()

    def __save_click(self):
        self.__hostname = self.__hostname_input.text()
        self.__port = int(self.__port_input.text())
        self.__position = (float(self.__x_input.text()), float(self.__y_input.text()), float(self.__z_input.text()))
        self.close()

    def exec_(self) -> tuple[str, int, tuple[float, float, float]]:
        super().exec_()
        return self.__hostname, self.__port, self.__position

class MenuWidgetItem(QWidget):
    def __init__(self, hostname, port, start_position = (0.0, 0.0, 0.0)):
        self.__hostname = hostname
        self.__port = port
        self.__start_position = start_position
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
        dialog = MenuItemDialog(self.__hostname, self.__port, self.__start_position)
        self.__hostname, self.__port, self.__start_position = dialog.exec_()
        self.__set_text()

    def __set_text(self):
        self.text.setText(f"HOSTNAME: {self.__hostname}, PORT: {self.__port}, START POSITION: {self.__start_position}")

    def get_start_data(self) -> tuple[str, int, tuple[float, float, float]]:
        return self.__hostname, self.__port, self.__start_position

class MenuWidget(QWidget):
    def __init__(self, add_func, remove_func, sim_func, set_func):
        super().__init__()

        self.main_layout = QGridLayout(self)

        self.list = QListWidget(self)
        self.list.setContentsMargins(0, 0, 0, 100)
        self.list.clicked.connect(self.__remove_button_activate)

        self.add_button = QPushButton(self)
        self.add_button.setText("Добавить квадрокоптер")
        self.add_button.clicked.connect(add_func)

        self.remove_button = QPushButton(self)
        self.remove_button.setText("Удалить коптер")
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

    def add(self, hostname : str, port : int, start_position : tuple):
        new_item_widget = MenuWidgetItem(hostname, port, start_position)
        new_item = QListWidgetItem()
        new_item.setSizeHint(new_item_widget.sizeHint()) 
        self.list.addItem(new_item)
        self.list.setItemWidget(new_item, new_item_widget)

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

class SimWidget(QWidget):
    def __init__(self, world, main, server, escape_callback):
        self.__escape_callback = escape_callback
        super().__init__()

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

        buttons_group = QWidget(self)
        buttons_group_layout = QHBoxLayout(self)
        buttons_group_layout.setContentsMargins(5, 10, 5, 5)
        buttons_group_layout.addWidget(self.center_button)
        buttons_group_layout.addWidget(self.right_down_button)
        buttons_group_layout.addWidget(self.right_up_button)
        buttons_group_layout.addWidget(self.left_up_button)
        buttons_group_layout.addWidget(self.left_down_button)
        buttons_group_layout.addWidget(self.trajectory_button)
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
        widget.setContentsMargins(0, 0, 0, 0)

        self._add_param(self.__data)
        scroll_area.setWidget(widget)
        main_layout.addWidget(scroll_area)
                
        self.setLayout(main_layout)

    def _add_param(self, data_dict : dict, lavel = 1):
        for key in data_dict:
            font = QFont("Times", 24 // lavel)
            label = QLabel(self)
            label.setText(key)
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
            self.tab_widget.addTab(self.__widgets[-1], item[0])

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

        self.drone_manager = DroneManager(self.world)

        widgets = QStackedWidget(self)

        self.world_widget = SimWidget(self.world, self, self.drone_manager, self.__back_to_menu)
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
                    position = (data['start_position']['x'], data['start_position']['y'], data['start_position']['z'])
                    self.add_server(data['hostname'], data['port'], position)
        except FileNotFoundError:
            pass

    def save(self, path : str):
        with open(path, 'w') as f:
            save_list = []

            items = self.menu.get_items()
            for index in range(len(items)):
                data = items[index].get_start_data()
                data_dict = {}
                data_dict['hostname'] = data[0]
                data_dict['port'] = data[1]

                position_dict = {}
                position_dict['x'] = data[2][0]
                position_dict['y'] = data[2][1]
                position_dict['z'] = data[2][2]

                data_dict['start_position'] = position_dict
                save_list.append(data_dict)
            json.dump(save_list, f)

    def add_server(self, hostname : str, port : int, start_position = (0.0, 0.0, 0.0)):
        self.menu.add(hostname, port, start_position)
        self.drone_manager.add_server(hostname, port, start_position)

    def __add_func(self):
        count = 0
        hostname = ""
        port = 0
        while True:
            text, ok = QInputDialog.getText(self, 'Добавить коптер', 'Введите ip коптера (ip:порт)')
            if ok:
                count = text.count(':')
                if count == 1:
                    hostname, port = text.split(':')
                    if port.isdigit() and len(hostname) > 0:
                        port = int(port)
                        break
            else:
                return
        self.add_server(hostname, port)

    def __remove_func(self):
        index = self.menu.remove_current()
        self.drone_manager.remove_server(index)

    def __start_sim(self):
        self.world.reset_camera()
        self.world.reset_trajectories()
        items = self.menu.get_items()
        for index in range(len(items)):
            data = items[index].get_start_data()
            self.drone_manager.update_start_position(index, data[2])
            self.drone_manager.update_hostname_port(index, data[0], data[1])
            
        self.drone_manager.start()
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
        self.drone_manager.close()
        self.save(self.__save_path)
        super().closeEvent(event)

    def __back_to_menu(self):
        self.drone_manager.close()
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