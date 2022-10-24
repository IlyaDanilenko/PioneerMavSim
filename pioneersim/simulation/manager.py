from abc import ABC, abstractmethod
from ObjectVisualizator.main import VisualizationWorld

class ModelManager(ABC):

    @abstractmethod
    def __init__(self, objects : list,  visualization : VisualizationWorld):
        self.objects = objects
        self.visualization = visualization
        self.object_type = None
        self.run = False

    @abstractmethod
    def create_model(self, fields : list):
        pass

    @abstractmethod
    def update_model(self, index : int, fields : list):
        pass

    @abstractmethod
    def remove_model(self, index : int):
        pass

    @abstractmethod
    def start(self, index : int):
        pass

    @abstractmethod
    def close(self, index : int):
        pass