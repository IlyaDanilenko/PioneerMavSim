from pioneersim.utils import ModelType, count_by_type
from pioneersim.simulation.manager import ModelManager
from ObjectVisualizator.main import VisualizationWorld, remapRGB

class FireModelManager(ModelManager):

    def __init__(self, objects: list, visualization: VisualizationWorld):
        super().__init__(objects, visualization)
        self.object_type = ModelType.FIRE

    def create_model(self, fields: list):
        id = count_by_type(self.objects, self.object_type)
        self.objects.append(self.object_type.model(
            id,
            *fields[-1],
            self.visualization.settings.simulation.fire_min_temp,
            self.visualization.settings.simulation.fire_max_temp,
            self.visualization.settings.simulation.fire_radius
        ))
        self.visualization.add_model(str(self.object_type), (*fields[-1], 0.0), 0, False)
        self.visualization.change_model_color(-1, *remapRGB(200, 44, 31))

    def update_model(self, index: int, fields: list):
        self.visualization.change_model_position(index, (*fields[0], 0), 0)
        self.objects[index].set_position(*fields[0])

    def remove_model(self, index: int):
        pass

    def start(self, index: int):
        pass

    def close(self, index: int):
        pass