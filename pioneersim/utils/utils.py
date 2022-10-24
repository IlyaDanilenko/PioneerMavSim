from enum import Enum
from pioneersim.simulation.plugins import get_plugin_classes
from plugins.models import *

__model_name = []
__classes = get_plugin_classes('models', 'Model')
for name in __classes:
    __model_name.append(name.lower().replace('model', '').upper())

_dynamic_code = ''
for index in range(len(__classes)):
    _dynamic_code += f'{__model_name[index]} = [{__classes[index]}.model_name(), {__classes[index]}]\n'

class ModelType(Enum):
    exec(_dynamic_code)

    def __str__(self):
        return self.value[0]

    @property
    def model(self):
        return self.value[1]

    @classmethod
    def get_type_from_name(cls, name):
        for member_name in cls._member_names_:
            if str(cls[member_name]) == name:
                return cls[member_name]

    @classmethod
    def get_str_list(cls):
        return [str(cls[name]) for name in cls._member_names_]

def count_by_type(objects : list, model_type: ModelType):
    id = 0
    for obj in objects:
        if type(obj) == model_type.model:
            id += 1
    return id