import sys, json, os
from ObjectVisualizator.main import VisualizationWorld
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from pioneersim.utils import ModelType
from pioneersim.managers import SimulationSettingManager, ObjectsManager
from pioneersim.widgets.menu import MenuWidget, ObjectDialog
from pioneersim.widgets.settings import SettingsMenuWidget
from pioneersim.widgets.simulation import SimWidget

class SimulationWindow(QMainWindow):
    def __init__(self, settings_path : str, save_path : str):
        super().__init__()
        self.setWindowTitle("PioneerMavSim")

        self.__save_path = save_path

        self.settings = SimulationSettingManager()
        self.settings.load(settings_path)

        self.setGeometry(50, 50, 800, 800)
        self.world = VisualizationWorld(self.settings)

        self.objects_manager = ObjectsManager(self.world)

        widgets = QStackedWidget(self)

        self.world_widget = SimWidget(self.world, self, self.objects_manager)
        self.world_widget.vis_widget.close = self.__back_to_menu
        self.world_widget.hide()
        self.world_widget.setGeometry(0, 0, self.width(), self.height())

        self.settings_menu = SettingsMenuWidget(self.settings)
        self.settings_menu.cancel_button.clicked.connect(self.__back_to_menu)
        self.settings_menu.escape.connect(self.__back_to_menu)
        self.settings_menu.setGeometry(0, 0, self.width(), self.height())
        self.settings_menu.hide()

        self.menu = MenuWidget()
        self.menu.add_button.clicked.connect(self.__add_func)
        self.menu.remove_button.clicked.connect(self.__remove_func)
        self.menu.sim_button.clicked.connect(self.__start_sim)
        self.menu.set_button.clicked.connect(self.__open_setting)
        self.menu.show()

        widgets.addWidget(self.menu)
        widgets.addWidget(self.world_widget)
        widgets.addWidget(self.settings_menu)

        self.setCentralWidget(widgets)
        self.load(self.__save_path)

    def resizeEvent(self, event):
        self.world_widget.setGeometry(0,0, self.width(), self.height())
        self.settings_menu.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def load(self, path : str):
        try:
            with open(path, 'r') as f:
                loaded_data = json.load(f)
                for data in loaded_data:
                    type = ModelType.get_type_from_name(data['type'])
                    self.add_object(type, type.model.unpack(data))
        except FileNotFoundError:
            pass
        except KeyError:
            QMessageBox.warning(self, "Внимание!", "Файл сохранения поврежден или не соответствует текущей версии симулятора. Файл сохранения будет удален. Перезапустите симулятор для корректной работы.")
            os.remove(path)
            sys.exit(0)

    def save(self, path : str):
        with open(path, 'w') as f:
            save_list = []

            items = self.menu.get_items()
            for index in range(len(items)):
                type, data = items[index].get_start_data()
                data_dict = {}
                data_dict['type'] = str(type)
                data_dict.update(type.model.pack(data))
                save_list.append(data_dict)
                
            json.dump(save_list, f)

    def add_object(self, type : ModelType, fields : list):
        self.menu.add_object(type, fields)
        self.objects_manager.add_object(type, fields)

    def __add_func(self):
        dialog = ObjectDialog()
        type, fields = dialog.exec_()
        if fields is not None and type is not None:
            if type.model.check_fields(fields):
                self.add_object(type, fields)

    def __remove_func(self):
        index = self.menu.remove_current()
        self.objects_manager.remove_objects(index)

    def __start_sim(self):
        self.world.reset_camera()
        self.world.reset_trajectories()
        items = self.menu.get_items()
        for index in range(len(items)):
            type, data = items[index].get_start_data()
            self.objects_manager.update_info(index, type, data)
            
        self.objects_manager.start()
        self.world_widget.status_widget.update()
        self.menu.hide()
        self.world_widget.show()
        self.menu.clearFocus()
        self.world_widget.setFocus()

    def __open_setting(self):
        self.menu.hide()
        self.menu.clearFocus()
        self.settings_menu.show()
        self.settings_menu.setFocus()

    def closeEvent(self, event):
        self.objects_manager.close()
        self.save(self.__save_path)
        super().closeEvent(event)

    def __back_to_menu(self):
        self.objects_manager.close()
        self.world_widget.hide()
        self.settings_menu.hide()
        self.menu.show()
        self.settings_menu.clearFocus()
        self.world_widget.clearFocus()
        self.menu.setFocus()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = SimulationWindow("settings/settings.json", "save/save.json")
    main.show()

    sys.exit(app.exec_())