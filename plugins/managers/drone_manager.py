from pioneersim.utils import ModelType
from pioneersim.simulation.manager import ModelManager
from ObjectVisualizator.main import VisualizationWorld, remapRGB
from PyQt5.QtCore import QObject

class DroneModelManager(ModelManager):
    
    def __init__(self, objects: list, visualization: VisualizationWorld):
        super().__init__(objects, visualization)
        self.object_type = ModelType.DRONEMAVLINK
        self.__signaler = QObject()

    def __get_index_by_model(self, model):
        for index in range(len(self.objects)):
            if (self.objects[index].model == model) and (type(self.objects[index]) == ModelType.DRONEMAVLINK.model):
                return index
        return -1

    def __drone_change_position(self):
        if self.run:
            index = self.__get_index_by_model(self.__signaler.sender())
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
        if self.run:
            index = self.__get_index_by_model(self.__signaler.sender())
            if index != -1:
                new_color = self.objects[index].get_led_color()
                model_color = self.visualization.get_model_color(index)
                if new_color != model_color:
                    if not any(model_color):
                        self.visualization.change_model_color(index)
                    else:
                        self.visualization.change_model_color(index, *new_color)

    def create_model(self, fields: list):
        self.visualization.add_model(str(self.object_type), fields[-2], 0, True, fields[-1])
        self.objects.append(self.object_type.model(
            *fields[0:-1],
            speed = self.visualization.settings.simulation.speed,
            battery_need = self.visualization.settings.simulation.battery_need,
            battery_capacity = self.visualization.settings.simulation.battery_capacity,
            battery_max = self.visualization.settings.simulation.battery_max,
            battery_off = self.visualization.settings.simulation.battery_off
        ))

    def update_model(self, index : int, fields: list):
        self.objects[index].set_start_position(*fields[2])
        self.objects[index].set_hostname(fields[0])
        self.objects[index].set_port(fields[1])
        self.visualization.change_trajectory_color(index, *remapRGB(*fields[-1]))

    def remove_model(self, index: int):
        self.close(index)

    def start(self, index: int):
        self.objects[index].start()
        self.objects[index].model.change_position.connect(self.__drone_change_position)
        self.objects[index].model.change_color.connect(self.__drone_change_color)
        self.objects[index].model.change_position.emit()
        self.objects[index].model.change_color.emit()

    def close(self, index : int):
        self.objects[index].online = False
    