from pioneersim.utils import ModelType
from pioneersim.simulation.manager import ModelManager
from ObjectVisualizator.main import VisualizationWorld, remapRGB

class AreaModelManager(ModelManager):

    def __init__(self, objects: list, visualization: VisualizationWorld):
        super().__init__(objects, visualization)
        self.object_type = ModelType.AREA

    def create_model(self, fields: list):
        x, y, z = fields[-2]
        x, y, z = x, z, y
        self.objects.append(self.object_type.model(*fields[0], fields[-2]))
        self.visualization.add_model(str(self.object_type), (*fields[0], 0.0), 0, False)
        self.visualization.change_model_scale(-1, (x, y, z))
        self.visualization.change_model_color(-1, *remapRGB(*fields[-1]))

    def update_model(self, index: int, fields: list):
        x, y, z = fields[1]
        x, y, z = x, z, y
        self.visualization.change_model_position(index, (*fields[0], 0), 0)
        self.visualization.change_model_scale(index, (x, y, z))
        self.visualization.change_model_color(index,  *remapRGB(*fields[-1]))
        self.objects[index].set_position(*fields[0])

    def remove_model(self, index: int):
        pass

    def start(self, index: int):
        pass

    def close(self, index: int):
        pass