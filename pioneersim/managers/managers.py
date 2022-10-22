from json import dump
from ObjectVisualizator.main import SettingsManager
from pioneersim.settings.settings import SimulationSettings
from pioneersim.utils import ModelType
from ObjectVisualizator.main import VisualizationWorld, remapRGB
from PyQt5.QtCore import QObject

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
            dump(self.__raw_data, f)

class ObjectsManager(QObject):
    def __init__(self, visualization : VisualizationWorld):
        super().__init__()
        self.visualization = visualization
        self.objects = []

        self.__run = False

    def count_by_type(self, model_type):
        id = 0
        for obj in self.objects:
            if type(obj) == model_type.model():
                id += 1
        return id

    def add_object(self, object_type : ModelType, fields : list):
        if object_type == ModelType.DRONEMAVLINK:
            self.visualization.add_model(str(ModelType.DRONEMAVLINK), fields[-2], 0, True, fields[-1])
            self.objects.append(object_type.model(
                *fields[0:-1],
                speed = self.visualization.settings.simulation.speed,
                battery_need = self.visualization.settings.simulation.battery_need,
                battery_capacity = self.visualization.settings.simulation.battery_capacity,
                battery_max = self.visualization.settings.simulation.battery_max,
                battery_off = self.visualization.settings.simulation.battery_off
            ))
        elif object_type == ModelType.FIRE:
            id = self.count_by_type(ModelType.FIRE)
            self.objects.append(object_type.model(
                id,
                *fields[-1],
                self.visualization.settings.simulation.fire_min_temp,
                self.visualization.settings.simulation.fire_max_temp,
                self.visualization.settings.simulation.fire_radius
            ))
            self.visualization.add_model(str(object_type), (*fields[-1], 0.0), 0, False)
            self.visualization.change_model_color(-1, *remapRGB(200, 44, 31))
        elif object_type == ModelType.AREA:
            x, y, z = fields[-2]
            x, y, z = x, z, y
            self.objects.append(object_type.model(*fields[0], fields[-2]))
            self.visualization.add_model(str(object_type), (*fields[0], 0.0), 0, False)
            self.visualization.change_model_scale(-1, (x, y, z))
            self.visualization.change_model_color(-1, *remapRGB(*fields[-1]))

    def remove_objects(self, index : int):
        if type(self.objects[index]) == ModelType.DRONEMAVLINK.model:
            self.objects[index].online = False
        self.objects.pop(index)
        self.visualization.remove_model(index)

    def update_info(self, index : int, type : ModelType, fields : list):
        if type == ModelType.DRONEMAVLINK:
            self.objects[index].set_start_position(*fields[2])
            self.objects[index].set_hostname(fields[0])
            self.objects[index].set_port(fields[1])
            self.visualization.change_trajectory_color(index, *remapRGB(*fields[-1]))
        elif type == ModelType.FIRE:
            self.visualization.change_model_position(index, (*fields[0], 0), 0)
            self.objects[index].set_position(*fields[0])
        elif type == ModelType.AREA:
            x, y, z = fields[1]
            x, y, z = x, z, y
            self.visualization.change_model_position(index, (*fields[0], 0), 0)
            self.visualization.change_model_scale(index, (x, y, z))
            self.visualization.change_model_color(index,  *remapRGB(*fields[-1]))
            self.objects[index].set_position(*fields[0])

    def get_status_info_by_type(self, model_type : ModelType) -> list:
        status_data = []
        for object in self.objects:
            if type(object) == model_type.model:
                status_data.append(object.get_status())
        return status_data

    def __get_index_by_model(self, model):
        for index in range(len(self.objects)):
            if (self.objects[index].model == model) and (type(self.objects[index]) == ModelType.DRONEMAVLINK.model()):
                return index
        return -1
                

    def __drone_change_position(self):
        if self.__run:
            index = self.__get_index_by_model(self.sender())
            if index != -1:
                position = self.objects[index].get_position()
                self.visualization.change_model_position(
                    index,
                    position,
                    self.objects[index].get_yaw()
                )
                for fire in [f for f in self.objects if type(f) == ModelType.FIRE.model()]:
                    temp = fire.get_temp(
                        tuple(position[0:2]),
                        self.visualization.settings.simulation.fire_static
                    )
                    self.objects[index].set_temp(fire.id, temp)

    def __drone_change_color(self):
        if self.__run:
            index = self.__get_index_by_model(self.sender())
            if index != -1:
                new_color = self.objects[index].get_led_color()
                model_color = self.visualization.get_model_color(index)
                if new_color != model_color:
                    if not any(model_color):
                        self.visualization.change_model_color(index)
                    else:
                        self.visualization.change_model_color(index, *new_color)

    def start(self):
        if not self.__run:
            self.__run = True
            for index in range(len(self.objects)):
                if type(self.objects[index]) == ModelType.DRONEMAVLINK.model:
                    self.objects[index].start()
                    self.objects[index].model.change_position.connect(self.__drone_change_position)
                    self.objects[index].model.change_color.connect(self.__drone_change_color)
                    self.objects[index].model.change_position.emit()
                    self.objects[index].model.change_color.emit()

    def close(self):
        for server in self.objects:
            if type(server) == ModelType.DRONEMAVLINK.model:
                server.online = False
        self.__run = False