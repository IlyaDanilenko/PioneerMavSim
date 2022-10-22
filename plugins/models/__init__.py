import glob
import platform

__separator = '/'
if platform.system() == 'Windows':
    __separator = '\\'
plugin_list = [plugin.split(__separator)[-1].replace('.py', '') for plugin in glob.glob(__file__.replace('__init__', '*'))]
plugin_list.remove('__init__')

for plugin in plugin_list:
    exec(f"from .{plugin} import *")