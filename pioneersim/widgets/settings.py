from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QTabWidget, QMessageBox, QScrollArea, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit
from pioneersim.settings.language import Language

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