import roslibpy
from threading import Thread
from PyQt5.QtCore import pyqtSignal, QObject
from math import degrees, acos
from pioneersim.simulation.model import Model
import docker
from time import sleep

class SimulationContainer:
    def __init__(self, ros_port : int , workspace : str, terminal_port = 8090, code_port = 9999):
        self.__ros_port = ros_port
        self.__terminal_port = terminal_port
        self.__code_port = code_port
        self.__workspace = workspace
        self.__client = docker.from_env()
        self.container = None

    def start(self):
        self.container = self.__client.containers.run(
            "geoscan/pioneer-max-sim:onti23",
            volumes = {self.__workspace : {'bind' : '/root/workspace', 'mode' : 'rw'}},
            ports = {
                self.__ros_port : self.__ros_port,
                self.__terminal_port : self.__terminal_port,
                self.__code_port : self.__code_port},
            detach = True
        )
        self.container.start()
        sleep(1)
        self.container.exec_run(
            f"bash -c \"source \"/opt/ros/noetic/setup.bash\"; roslaunch rosbridge_server rosbridge_websocket.launch address:=localhost port:={self.__ros_port}\"",
            detach=True
        )

    def stop(self):
        if self.container is not None:
            self.container.stop()
            self.container.remove()
            self.container = None

class SimpleROSDroneModel(QObject):
    change_position = pyqtSignal()
    change_color = pyqtSignal()

    def __init__(self, x = 0.0, y= 0.0, z = 0.0, yaw = 0.0):
        super().__init__()
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.color = (0, 0, 0)

    def set_color(self, r = 0, g = 0, b = 0):
        self.color = (r, g, b)
        self.change_color.emit()

    def set_position(self, x : float, y : float, z : float, yaw : float):
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.change_position.emit()

class DroneROSModel(Model):
    def __init__(self, port=6666, workspace = ""):
        self.online = False
        self.__port = port
        self.__workspace = workspace
        self.model = None
        self.client = None
        self.container = None
        self.__message_thread = None
        

    def __change_drone_state(self, message):
        x = message['pose']['position']['x']
        y = message['pose']['position']['y']
        z = message['pose']['position']['z']
        yaw = degrees(acos(message['pose']['orientation']['x']))

        if x != self.model.x or y != self.model.y or z != self.model.z or yaw != self.model.yaw:
            self.model.set_position(x, y, z, yaw)

        r = message['color']['r']
        g = message['color']['g']
        b = message['color']['b']
        if (r, g, b) != self.model.color:
            self.model.set_color(r, g, b)

    def __message_handler(self):
        drone_topic = roslibpy.Topic(self.client, "visualization_marker", "visualization_msgs/Marker")
        drone_topic.subscribe(self.__change_drone_state)

        while self.online:
            pass
        
        print(f'{self.__port} offline')
        self.container.stop()
        self.client.close()
        self.client = None

    def start(self):
        self.container = SimulationContainer(self.__port, self.__workspace)
        self.container.start()
        self.model = SimpleROSDroneModel()
        self.client = roslibpy.Ros('localhost', self.__port)
        try:
            self.client.run()
            self.online = True

            self.__message_thread = Thread(target=self.__message_handler)
            self.__message_thread.daemon = True
            self.__message_thread.start()
        except roslibpy.core.RosTimeoutError:
            print("Нет соединения с ROS")
            self.container.stop()
            self.client.close()
            self.client = None

    def get_led_color(self) -> list[int]:
        return self.model.color

    def get_position(self) -> tuple[float, float, float]:
        if self.model is not None:
            return self.model.x, self.model.y, self.model.z
        else:
            return None, None, None

    def get_yaw(self) -> float:
        return self.model.yaw

    def set_port(self, port : int):
        if not self.online:
            self.__port = port

    def set_workspace(self, workspace : str):
        if not self.online:
            self.__workspace = workspace

    @classmethod
    def pack(cls, data) -> dict:
        data_dict = {}
        data_dict['port'] = data[0]
        data_dict['workspace'] = data[1]

        color_dict = {}
        color_dict['r'] = data[2][0]
        color_dict['g'] = data[2][1]
        color_dict['b'] = data[2][2]

        data_dict['trajectory_color'] = color_dict
        return data_dict

    def get_status(self) -> dict:
        return {"ROS" : self.online}

    @classmethod
    def unpack(cls, data) -> list:
        color = (data['trajectory_color']['r'], data['trajectory_color']['g'], data['trajectory_color']['b'])
        return [data['port'], data['workspace'], color]

    @classmethod
    def model_name(cls) -> str:
        return 'droneros'

    @classmethod
    def status(cls) -> bool:
        return True

    @classmethod
    def check_fields(cls, fields) -> bool:
        return fields[0] != 0 and fields[1] != ""

    @classmethod
    def get_description(cls, field) -> str:
        return f"Порт: {field[0]}, Рабочая папка: {field[1]}, Цвет траектории: {field[2]}"

    @classmethod
    def transform(cls, fields = None) -> list:
        if fields is None:
            return [6666, "", (0, 0, 0)]
        else:
            return [int(fields[0]), str(fields[1]),(int(fields[2]), int(fields[3]), int(fields[4]))]
