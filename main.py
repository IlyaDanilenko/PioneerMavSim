import sys, json, os
from ObjectVisualizator.main import VisWidget, VisualizationWorld
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QListWidget, QPushButton, QStackedWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QLabel, QLineEdit, QMessageBox, QScrollArea, QListWidgetItem, QDialog, QComboBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from threading import Thread
from time import sleep
from pioneersim.settings.language import Language
from pioneersim.utils import ModelType
from pioneersim.managers import SimulationSettingManager, ObjectsManager

class ObjectDialog(QDialog):
    def __init__(self, type = None, fields = None):
        self.__type = type
        if fields is None:
            self.__fields = []
        else:
            self.__fields = fields

        self.__field_inputs = []

        super().__init__()
        self.setWindowModality(Qt.ApplicationModal)

        self.main_layout = QVBoxLayout()

        if self.__type is None:
            self.setWindowTitle("Добавить объект")
            self.setGeometry(200, 200, 500, 50)

            combo = QComboBox()
            for name in ModelType.get_str_list():
                combo.addItem(Language.get_word(name))
            combo.activated[str].connect(self.__on_active)

            self.main_layout.addWidget(combo)
        else:
            self.setWindowTitle("Изменение объекта")
            self.render_interface()

        self.setLayout(self.main_layout)

    def __on_active(self, text):
        for model in ModelType:
            if text == Language.get_word(str(model)):
                self.__type = model
        self.render_interface()

    def render_interface(self):
        if len(self.__fields) != len(self.__type.model.transform()):
            self.__fields = self.__type.model.transform()
        if self.__type == ModelType.DRONEMAVLINK:
            self.drone_interface(*self.__fields)
        elif self.__type == ModelType.FIRE:
            self.fire_interface(*self.__fields)
        elif self.__type == ModelType.AREA:
            self.area_interface(*self.__fields)

    def __cancel_click(self):
        self.__fields = None
        self.close()

    def __save_click(self):
        fields = [field.text() for field in self.__field_inputs]
        self.__fields = self.__type.model.transform(fields)
        self.close()

    def remove_interfaces(self):
        self.__field_inputs = []
        count = self.main_layout.count()
        if count == 1:
            return
        else:
            while count > 1:
                self.main_layout.removeWidget(self.main_layout.itemAt(1).widget())
                count = self.main_layout.count()

    def drone_interface(self, hostname : str, port : int, position : tuple, color : tuple):
        self.remove_interfaces()

        hostname_widget = QWidget()
        hostname_layout = QHBoxLayout(hostname_widget)
        hostname_text = QLabel()
        hostname_text.setText('Hostname')
        hostname_input = QLineEdit(hostname)
        hostname_layout.addWidget(hostname_text)
        hostname_layout.addWidget(hostname_input, 100)
        hostname_widget.setLayout(hostname_layout)
        self.__field_inputs.append(hostname_input)

        port_widget = QWidget()
        port_layout = QHBoxLayout(port_widget)
        port_text = QLabel()
        port_text.setText('Port')
        port_input = QLineEdit(str(port))
        port_layout.addWidget(port_text)
        port_layout.addWidget(port_input, 100)
        port_widget.setLayout(port_layout)
        self.__field_inputs.append(port_input)

        x_widget = QWidget()
        x_layout = QHBoxLayout(x_widget)
        x_text = QLabel()
        x_text.setText('Координата X')
        x_input = QLineEdit(str(position[0]))
        x_layout.addWidget(x_text)
        x_layout.addWidget(x_input, 100)
        x_widget.setLayout(x_layout)
        self.__field_inputs.append(x_input)

        y_widget = QWidget()
        y_layout = QHBoxLayout(y_widget)
        y_text = QLabel()
        y_text.setText('Координата Y')
        y_input = QLineEdit(str(position[1]))
        y_layout.addWidget(y_text)
        y_layout.addWidget(y_input, 100)
        y_widget.setLayout(y_layout)
        self.__field_inputs.append(y_input)

        z_widget = QWidget()
        z_layout = QHBoxLayout(z_widget)
        z_text = QLabel()
        z_text.setText('Координата Z')
        z_input = QLineEdit(str(position[2]))
        z_layout.addWidget(z_text)
        z_layout.addWidget(z_input, 100)
        z_widget.setLayout(z_layout)
        self.__field_inputs.append(z_input)

        r_widget = QWidget()
        r_layout = QHBoxLayout(r_widget)
        r_text = QLabel()
        r_text.setText('Цвет траектории R')
        r_input = QLineEdit(str(color[0]))
        r_layout.addWidget(r_text)
        r_layout.addWidget(r_input, 100)
        r_widget.setLayout(r_layout)
        self.__field_inputs.append(r_input)

        g_widget = QWidget()
        g_layout = QHBoxLayout(g_widget)
        g_text = QLabel()
        g_text.setText('Цвет траектории G')
        g_input = QLineEdit(str(color[1]))
        g_layout.addWidget(g_text)
        g_layout.addWidget(g_input, 100)
        g_widget.setLayout(g_layout)
        self.__field_inputs.append(g_input)

        b_widget = QWidget()
        b_layout = QHBoxLayout(b_widget)
        b_text = QLabel()
        b_text.setText('Цвет траектории B')
        b_input = QLineEdit(str(color[2]))
        b_layout.addWidget(b_text)
        b_layout.addWidget(b_input, 100)
        b_widget.setLayout(b_layout)
        self.__field_inputs.append(b_input)

        control = QWidget()
        control_layout = QGridLayout(control)
        cancel_button = QPushButton()
        cancel_button.setText("Отменить")
        cancel_button.clicked.connect(self.__cancel_click)
        save_button = QPushButton()
        save_button.setText("Сохранить")
        save_button.clicked.connect(self.__save_click)
        control_layout.addWidget(cancel_button, 0, 0)
        control_layout.addWidget(save_button, 0, 1)
        control.setLayout(control_layout)

        self.main_layout.addWidget(hostname_widget)
        self.main_layout.addWidget(port_widget)
        self.main_layout.addWidget(x_widget)
        self.main_layout.addWidget(y_widget)
        self.main_layout.addWidget(z_widget)
        self.main_layout.addWidget(r_widget)
        self.main_layout.addWidget(g_widget)
        self.main_layout.addWidget(b_widget)
        self.main_layout.addWidget(control)

    def fire_interface(self, position : tuple):
        self.remove_interfaces()

        x_widget = QWidget()
        x_layout = QHBoxLayout(x_widget)
        x_text = QLabel()
        x_text.setText('Координата X')
        x_input = QLineEdit(str(position[0]))
        x_layout.addWidget(x_text)
        x_layout.addWidget(x_input, 100)
        x_widget.setLayout(x_layout)
        self.__field_inputs.append(x_input)

        y_widget = QWidget()
        y_layout = QHBoxLayout(y_widget)
        y_text = QLabel()
        y_text.setText('Координата Y')
        y_input = QLineEdit(str(position[1]))
        y_layout.addWidget(y_text)
        y_layout.addWidget(y_input, 100)
        y_widget.setLayout(y_layout)
        self.__field_inputs.append(y_input)

        control = QWidget()
        control_layout = QGridLayout(control)
        cancel_button = QPushButton()
        cancel_button.setText("Отменить")
        cancel_button.clicked.connect(self.__cancel_click)
        save_button = QPushButton()
        save_button.setText("Сохранить")
        save_button.clicked.connect(self.__save_click)
        control_layout.addWidget(cancel_button, 0, 0)
        control_layout.addWidget(save_button, 0, 1)
        control.setLayout(control_layout)

        self.main_layout.addWidget(x_widget)
        self.main_layout.addWidget(y_widget)
        self.main_layout.addWidget(control)

    def area_interface(self, position : tuple, scale : tuple, color : tuple):
        self.remove_interfaces()

        x_widget = QWidget()
        x_layout = QHBoxLayout(x_widget)
        x_text = QLabel()
        x_text.setText('Координата X')
        x_input = QLineEdit(str(position[0]))
        x_layout.addWidget(x_text)
        x_layout.addWidget(x_input, 100)
        x_widget.setLayout(x_layout)
        self.__field_inputs.append(x_input)

        y_widget = QWidget()
        y_layout = QHBoxLayout(y_widget)
        y_text = QLabel()
        y_text.setText('Координата Y')
        y_input = QLineEdit(str(position[1]))
        y_layout.addWidget(y_text)
        y_layout.addWidget(y_input, 100)
        y_widget.setLayout(y_layout)
        self.__field_inputs.append(y_input)

        s1_widget = QWidget()
        s1_layout = QHBoxLayout(s1_widget)
        s1_text = QLabel()
        s1_text.setText('Размер X')
        s1_input = QLineEdit(str(scale[0]))
        s1_layout.addWidget(s1_text)
        s1_layout.addWidget(s1_input, 100)
        s1_widget.setLayout(s1_layout)
        self.__field_inputs.append(s1_input)

        s2_widget = QWidget()
        s2_layout = QHBoxLayout(s2_widget)
        s2_text = QLabel()
        s2_text.setText('Размер Y')
        s2_input = QLineEdit(str(scale[1]))
        s2_layout.addWidget(s2_text)
        s2_layout.addWidget(s2_input, 100)
        s2_widget.setLayout(s2_layout)
        self.__field_inputs.append(s2_input)

        s3_widget = QWidget()
        s3_layout = QHBoxLayout(s3_widget)
        s3_text = QLabel()
        s3_text.setText('Размер Z')
        s3_input = QLineEdit(str(scale[2]))
        s3_layout.addWidget(s3_text)
        s3_layout.addWidget(s3_input, 100)
        s3_widget.setLayout(s3_layout)
        self.__field_inputs.append(s3_input)

        r_widget = QWidget()
        r_layout = QHBoxLayout(r_widget)
        r_text = QLabel()
        r_text.setText('Цвет R')
        r_input = QLineEdit(str(color[0]))
        r_layout.addWidget(r_text)
        r_layout.addWidget(r_input, 100)
        r_widget.setLayout(r_layout)
        self.__field_inputs.append(r_input)

        g_widget = QWidget()
        g_layout = QHBoxLayout(g_widget)
        g_text = QLabel()
        g_text.setText('Цвет G')
        g_input = QLineEdit(str(color[1]))
        g_layout.addWidget(g_text)
        g_layout.addWidget(g_input, 100)
        g_widget.setLayout(g_layout)
        self.__field_inputs.append(g_input)

        b_widget = QWidget()
        b_layout = QHBoxLayout(b_widget)
        b_text = QLabel()
        b_text.setText('Цвет B')
        b_input = QLineEdit(str(color[2]))
        b_layout.addWidget(b_text)
        b_layout.addWidget(b_input, 100)
        b_widget.setLayout(b_layout)
        self.__field_inputs.append(b_input)

        control = QWidget()
        control_layout = QGridLayout(control)
        cancel_button = QPushButton()
        cancel_button.setText("Отменить")
        cancel_button.clicked.connect(self.__cancel_click)
        save_button = QPushButton()
        save_button.setText("Сохранить")
        save_button.clicked.connect(self.__save_click)
        control_layout.addWidget(cancel_button, 0, 0)
        control_layout.addWidget(save_button, 0, 1)
        control.setLayout(control_layout)

        self.main_layout.addWidget(x_widget)
        self.main_layout.addWidget(y_widget)
        self.main_layout.addWidget(s1_widget)
        self.main_layout.addWidget(s2_widget)
        self.main_layout.addWidget(s3_widget)
        self.main_layout.addWidget(r_widget)
        self.main_layout.addWidget(g_widget)
        self.main_layout.addWidget(b_widget)
        self.main_layout.addWidget(control)        

    def exec_(self) -> list[str, list]:
        super().exec_()
        return self.__type, self.__fields

class MenuWidgetItem(QWidget):
    def __init__(self, type = ModelType.DRONEMAVLINK, field = None):
        self.__type = type
        self.__field = field

        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)

        layout = QHBoxLayout(self)
        self.text = QLabel()
        self.__set_text()

        button = QPushButton(self)
        button.setText('Изменить')
        button.clicked.connect(self.__button_click)

        layout.addWidget(self.text, 100)
        layout.addWidget(button)
        self.setLayout(layout)

    def __button_click(self):
        dialog = ObjectDialog(self.__type, self.__field)
        _, fields = dialog.exec_()
        if fields is not None:
            self.__set_text()
            self.__field = fields

    def __set_text(self):
        self.text.setText(f"Тип: {Language.get_word(str(self.__type))}, " + self.__type.model.get_description(self.__field))

    def get_start_data(self) -> tuple:
        return self.__type, self.__field

class MenuWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.main_layout = QGridLayout(self)

        self.list = QListWidget(self)
        self.list.setContentsMargins(0, 0, 0, 100)
        self.list.clicked.connect(self.__remove_button_activate)

        self.add_button = QPushButton(self)
        self.add_button.setText("Добавить объект")

        self.remove_button = QPushButton(self)
        self.remove_button.setText("Удалить объект")
        self.remove_button.setEnabled(False)

        self.sim_button = QPushButton(self)
        self.sim_button.setText("Включить симуляцию")

        self.set_button = QPushButton(self)
        self.set_button.setText("Настройки")

        buttons_group = QWidget(self)
        buttons_group_layout = QGridLayout(self)
        buttons_group_layout.addWidget(self.set_button, 0, 0)
        buttons_group_layout.addWidget(self.add_button, 0, 1)
        buttons_group_layout.addWidget(self.remove_button, 0, 2)
        buttons_group_layout.addWidget(self.sim_button, 0, 3)
        buttons_group.setLayout(buttons_group_layout)

        self.main_layout.addWidget(self.list, 0, 0)
        self.main_layout.addWidget(buttons_group, 1, 0)

        self.setLayout(self.main_layout)

    def add_object(self, type : ModelType, fields : list):
        if type is not None:
            widget = MenuWidgetItem(type, fields)
            new_item = QListWidgetItem()
            new_item.setSizeHint(widget.sizeHint()) 
            self.list.addItem(new_item)
            self.list.setItemWidget(new_item, widget)

    def remove_current(self) -> int:
        row = self.list.currentRow()
        self.list.takeItem(row)
        self.remove_button.setEnabled(False)
        return row

    def get_items(self) -> list[MenuWidgetItem]:
        items = [self.list.item(x) for x in range(self.list.count())]
        widgets = []
        for item in items:
            widgets.append(self.list.itemWidget(item))
        return widgets

    def __remove_button_activate(self):
        self.remove_button.setEnabled(True)

class StatusWidget(QWidget):
    def __init__(self, server : ObjectsManager):
        self.__server = server
        super().__init__()

        self.main_layout = QVBoxLayout(self)

        self.__updateble_label = []
        self.setGeometry(200, 200, 500, 500)
        self.setWindowTitle("Статус")

        self.setContentsMargins(0, 0, 0, 0)

    def update(self):
        if self.main_layout.count() != 0:
            self.main_layout.removeWidget(self.main_layout.itemAt(0).widget())
        self.__updateble_label = []
        scroll_layout = QVBoxLayout(self)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea(self)
        scroll_area.setContentsMargins(0, 0, 0, 0)

        widget = QWidget(scroll_area)
        widget.setLayout(scroll_layout)
        widget.setContentsMargins(0, 0, 0, 0)

        status = self.__server.get_status_info_by_type(ModelType.DRONEMAVLINK)

        font = QFont("Times", 16)
        for index in range(len(status)):
            status_widget = QWidget(self)
            layout = QVBoxLayout(status_widget)
            drone_name = QLabel(f'{Language.get_word(str(ModelType.DRONEMAVLINK))} - {index + 1}')
            drone_name.setFont(font)
            layout.addWidget(drone_name)
            for name, value in status[index].items():
                value_str = f'\t{Language.get_word(name)} : {Language.get_word(str(value))}'
                self.__updateble_label.append(QLabel(value_str))
                layout.addWidget(self.__updateble_label[-1])
            status_widget.setLayout(layout)
            scroll_layout.addWidget(status_widget)

        scroll_area.setWidget(widget)
        self.main_layout.addWidget(scroll_area)

    def __update_label_target(self, type):
        while not self.isHidden():
            status = self.__server.get_status_info_by_type(type)
            update_index = 0
            for index in range(len(status)):
                for name, value in status[index].items():
                    self.__updateble_label[update_index].setText(f'\t{Language.get_word(name)} : {Language.get_word(str(value))}')
                    update_index += 1
            sleep(0.01)

    def open(self):
        if self.isHidden():
            self.show()
            Thread(target=self.__update_label_target, args=(ModelType.DRONEMAVLINK,)).start()
        else:
            self.hide()

class SimWidget(QWidget):
    def __init__(self, world, main, server):
        super().__init__()

        self.status_widget = StatusWidget(server)

        self.vis_widget = VisWidget(world, main, server)
        self.vis_widget.setContentsMargins(0, 0, 0 , 100)

        self.center_button = QPushButton(self)
        self.center_button.setText("Центр сверху")
        self.center_button.clicked.connect(self.__center_button_click)

        self.right_down_button = QPushButton(self)
        self.right_down_button.setText("Правый нижний угол")
        self.right_down_button.clicked.connect(self.__right_down_button_click)

        self.right_up_button = QPushButton(self)
        self.right_up_button.setText("Правый верхний угол")
        self.right_up_button.clicked.connect(self.__right_up_button_click)

        self.left_up_button = QPushButton(self)
        self.left_up_button.setText("Левый верхний угол")
        self.left_up_button.clicked.connect(self.__left_up_button_click)

        self.left_down_button = QPushButton(self)
        self.left_down_button.setText("Левый нижний угол")
        self.left_down_button.clicked.connect(self.__left_down_button_click)

        self.trajectory_button = QPushButton(self)
        if world.settings.workspace.trajectory:
            self.trajectory_button.setText("Скрыть траекторию")
        else:
            self.trajectory_button.setText("Показать траекторию")
        self.trajectory_button.clicked.connect(self.__trajectories_button_click)

        self.status_button = QPushButton(self)
        self.status_button.setText("Панель статусов")
        self.status_button.clicked.connect(self.status_widget.open)

        buttons_group = QWidget(self)
        buttons_group_layout = QHBoxLayout(self)
        buttons_group_layout.setContentsMargins(5, 10, 5, 5)
        buttons_group_layout.addWidget(self.center_button)
        buttons_group_layout.addWidget(self.right_down_button)
        buttons_group_layout.addWidget(self.right_up_button)
        buttons_group_layout.addWidget(self.left_up_button)
        buttons_group_layout.addWidget(self.left_down_button)
        buttons_group_layout.addWidget(self.trajectory_button)
        buttons_group_layout.addWidget(self.status_button)
        buttons_group.setLayout(buttons_group_layout)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(buttons_group)
        self.main_layout.addWidget(self.vis_widget, 1)
        self.setLayout(self.main_layout)

    def keyReleaseEvent(self, event):
        self.vis_widget.keyReleaseEvent(event)

    def __center_button_click(self):
        self.vis_widget.world.camera.setPos(self.vis_widget.world.settings.polygon.scale.get_x(), self.vis_widget.world.settings.polygon.scale.get_z(), self.vis_widget.world.settings.polygon.scale.get_y() * 2.5)
        self.vis_widget.world.camera.setHpr(0, -90, 0)

    def __right_down_button_click(self):
        self.vis_widget.world.camera.setPos(self.vis_widget.world.settings.polygon.scale.get_x() * 3.5, -self.vis_widget.world.settings.polygon.scale.get_z() * 1.5, self.vis_widget.world.settings.polygon.scale.get_y() * 1.5)
        self.vis_widget.world.camera.setHpr(45, -45, 0)

    def __right_up_button_click(self):
        self.vis_widget.world.camera.setPos(self.vis_widget.world.settings.polygon.scale.get_x() * 3.5, self.vis_widget.world.settings.polygon.scale.get_z() * 3.5, self.vis_widget.world.settings.polygon.scale.get_y() * 1.5)
        self.vis_widget.world.camera.setHpr(135, -45, 0)

    def __left_up_button_click(self):
        self.vis_widget.world.camera.setPos(-self.vis_widget.world.settings.polygon.scale.get_z() * 1.5, self.vis_widget.world.settings.polygon.scale.get_z() * 3.5, self.vis_widget.world.settings.polygon.scale.get_y() * 1.5)
        self.vis_widget.world.camera.setHpr(-135, -45, 0)

    def __left_down_button_click(self):
        self.vis_widget.world.camera.setPos(-self.vis_widget.world.settings.polygon.scale.get_z() * 1.5, -self.vis_widget.world.settings.polygon.scale.get_z() * 1.5, self.vis_widget.world.settings.polygon.scale.get_y() * 1.5)
        self.vis_widget.world.camera.setHpr(-45, -45, 0)

    def __trajectories_button_click(self):
        visible = not self.vis_widget.world.get_trajectory_visible()
        self.vis_widget.world.set_trajectory_visible(visible)
        if visible:
            self.trajectory_button.setText("Скрыть траекторию")
        else:
            self.trajectory_button.setText("Показать траекторию")

class SettingsMenuItemWidget(QWidget):
    def __init__(self, name : str, data):
        self.name = name
        self.__data = data
        self.__inputs = []
        super().__init__()

        self.setContentsMargins(0, 0, 0, 0)

        main_layout = QVBoxLayout(self)
        self.scroll_layout = QVBoxLayout(self)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea(self)
        scroll_area.setContentsMargins(0, 0, 0, 0)

        widget = QWidget(scroll_area)
        widget.setLayout(self.scroll_layout)
        widget.setContentsMargins(10, 0, 10, 0)

        self._add_param(self.__data)
        scroll_area.setWidget(widget)
        main_layout.addWidget(scroll_area)
                
        self.setLayout(main_layout)

    def _add_param(self, data_dict : dict, lavel = 1):
        for key in data_dict:
            font = QFont("Times", 24 // lavel)
            label = QLabel(self)
            label.setText(Language.get_word(key))
            label.setFont(font)
            if type(data_dict[key]) == dict:
                self.scroll_layout.addWidget(label)
                self._add_param(data_dict[key], lavel + 1)
            else:
                widget = QWidget(self)
                widget_layout = None
                widget_layout = QHBoxLayout(widget)
                widget_layout.setContentsMargins(0, 0, 0, 0)
                edit = QLineEdit(self)
                edit.setText(str(data_dict[key]))
                self.__inputs.append(edit)
                widget_layout.addWidget(label)
                widget_layout.addWidget(edit, 1)
                widget.setLayout(widget_layout)
                self.scroll_layout.addWidget(widget)

    def get_data_dict(self, data_dict=None, inputs=None) -> dict:
        if inputs is None:
            inputs = []
            for edit in self.__inputs:
                text = edit.text()
                if text.lower() == "true":
                    inputs.append(True)
                elif text.lower() == "false":
                    inputs.append(False)
                elif text.replace('-', '').isdigit():
                    inputs.append(int(text))
                else:
                    try:
                        inputs.append(float(text))
                    except:
                        inputs.append(text)
        if data_dict is None:
            data_dict = self.__data
        for key in data_dict:
            if type(data_dict[key]) == dict:
                data_dict[key] = self.get_data_dict(data_dict[key], inputs)
            else:
                data_dict[key] = inputs.pop(0)
        return data_dict

class SettingsMenuWidget(QWidget):
    escape = pyqtSignal()

    def __init__(self, settings):
        self.settings = settings
        self.__widgets = []
        super().__init__()

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setContentsMargins(0, 0, 0, 0)

        self.ok_button = QPushButton(self)
        self.ok_button.setText("Применить")
        self.ok_button.clicked.connect(self.ok_button_click)

        self.cancel_button = QPushButton(self)
        self.cancel_button.setText("Отменить")

        buttons_group = QWidget(self)
        buttons_group_layout = QHBoxLayout(self)
        buttons_group_layout.setContentsMargins(5, 10, 5, 5)
        buttons_group_layout.addWidget(self.cancel_button)
        buttons_group_layout.addWidget(self.ok_button)
        buttons_group.setLayout(buttons_group_layout)

        for item in self.settings.__dict__().items():
            self.__widgets.append(SettingsMenuItemWidget(*item))
            self.tab_widget.addTab(self.__widgets[-1], Language.get_word(item[0]))

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.tab_widget, 1)
        self.main_layout.addWidget(buttons_group)
        self.setLayout(self.main_layout)

    def ok_button_click(self):
        new_dict = {}
        for element in self.__widgets:
            new_dict[element.name] = element.get_data_dict()

        self.settings.update_from_dict(new_dict)
        QMessageBox.warning(self, "Внимание!", "Настройки будут применены только при следующем запуске")
        self.settings.write()
        self.escape.emit()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.escape.emit()

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
        if fields is not None:
            if type == ModelType.DRONEMAVLINK:
                if fields[0] != '':
                    self.add_object(type, fields)
            else:
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