
from pioneersim.utils import ModelType, get_plugin_classes
from pioneersim.settings.language import Language
from plugins.widgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QGridLayout, QListWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QListWidgetItem, QDialog, QComboBox

class ObjectDialog(QDialog):
    def __init__(self, type = None, fields = None):
        self.__type = type
        if fields is None:
            self.__fields = []
        else:
            self.__fields = fields

        self.__field_inputs = []

        super().__init__()

        self.objects_loader = {}
        
        classes = get_plugin_classes('widgets', 'ObjectDialogLoader')
        for index in range(len(ModelType._member_names_)):
            model_type = ModelType[ModelType._member_names_[index]]
            for loader_classes in classes:
                if str(model_type) == loader_classes.replace('DialogLoader', '').lower():
                    exec(f"self.objects_loader[model_type] = {loader_classes}")

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
        zeros_field = self.__type.model.transform()
        if len(self.__fields) != len(zeros_field):
            self.__fields = zeros_field
        
        self.remove_interfaces()
        self.__field_inputs, widgets = self.objects_loader[self.__type].get_interface(self.__fields)

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

        for widget in widgets:
            self.main_layout.addWidget(widget)

        self.main_layout.addWidget(control)

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

    def exec_(self) -> list[str, list]:
        super().exec_()
        return self.__type, self.__fields

class MenuWidgetItem(QWidget):
    def __init__(self, type : ModelType, field = None):
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