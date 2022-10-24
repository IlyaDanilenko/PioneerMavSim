from json import dump
from ObjectVisualizator.main import SettingsManager
from pioneersim.settings.settings import SimulationSettings
from pioneersim.utils import ModelType, get_plugin_classes
from ObjectVisualizator.main import VisualizationWorld
from plugins.managers import *

class SimulationSettingManager(SettingsManager):
    def __init__(self):
        self.simulation = None
        self.__raw_data = None
        self.__path = None

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

class ObjectsManager:
    def __init__(self, visualization : VisualizationWorld):
        super().__init__()
        self.visualization = visualization
        self.objects = []
        self.model_managers = {}
        
        classes = get_plugin_classes('managers', 'ModelManager')
        for index in range(len(ModelType._member_names_)):
            model_type = ModelType[ModelType._member_names_[index]]
            for manager_classes in classes:
                if str(model_type) == manager_classes.replace('ModelManager', '').lower():
                    exec(f"self.model_managers[model_type] = {manager_classes}(self.objects, self.visualization)")

        self.__run = False

    def __get_model_manager_by_type(self, model_type):
        for key in self.model_managers.keys():
            if key.model == model_type:
                return self.model_managers[key]
        return None

    def add_object(self, object_type : ModelType, fields : list):
        self.model_managers[object_type].create_model(fields)  


    def remove_objects(self, index : int):
        manager = self.__get_model_manager_by_type(type(self.objects[index]))
        if manager is not None:
            manager.remove_model(index)
        self.objects.pop(index)
        self.visualization.remove_model(index)

    def update_info(self, index : int, type : ModelType, fields : list):
        self.model_managers[type].update_model(index, fields)

    def get_status_info_by_type(self, model_type : ModelType) -> list:
        status_data = []
        for object in self.objects:
            if type(object) == model_type.model:
                status_data.append(object.get_status())
        return status_data

    def start(self):
        if not self.__run:
            self.__run = True
            for manager in self.model_managers.values():
                manager.run = True
            for index in range(len(self.objects)):
                manager = self.__get_model_manager_by_type(type(self.objects[index]))
                if manager is not None:
                    manager.start(index)

    def close(self):
        for index in range(len(self.objects)):
            manager = self.__get_model_manager_by_type(type(self.objects[index]))
            if manager is not None:
                manager.close(index)
        for manager in self.model_managers.values():
            manager.run = False
        self.__run = False