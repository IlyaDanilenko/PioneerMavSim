import inspect, sys

def get_plugin_classes(plugin_type, base_class_filter=None):
    classes = [cls_name for cls_name, cls_obj in inspect.getmembers(sys.modules[f'plugins.{plugin_type}']) if inspect.isclass(cls_obj)]
    if base_class_filter is not None:
        exec(f"from plugins.{plugin_type} import *")
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