from enum import Enum
import inspect, sys
from plugins.models import *

def get_plugin_classes(plugin_type, base_class_filter=None):
    classes = [cls_name for cls_name, cls_obj in inspect.getmembers(sys.modules[f'plugins.{plugin_type}']) if inspect.isclass(cls_obj)]
    if base_class_filter is not None:
        filter_classes = []
        base_classes = []
        for class_name in classes:
            exec(f"base_classes.append({class_name}.__bases__[0].__name__)")
        for index in range(len(base_classes)):
            if base_classes[index] == base_class_filter:
                filter_classes.append(classes[index])
        return filter_classes
    else:
        return classes

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
