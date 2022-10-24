from threading import Thread
from time import sleep
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QScrollArea, QVBoxLayout, QLabel
from pioneersim.managers import ObjectsManager
from pioneersim.utils import ModelType
from pioneersim.settings.language import Language
from ObjectVisualizator.main import VisWidget

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

        font = QFont("Times", 16)

        for name in ModelType._member_names_:
            model_type = ModelType[name]
            if model_type.model.status():
                status = self.__server.get_status_info_by_type(model_type)

                for index in range(len(status)):
                    status_widget = QWidget(self)
                    layout = QVBoxLayout(status_widget)
                    drone_name = QLabel(f'{Language.get_word(str(model_type))} - {index + 1}')
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
            for name in ModelType._member_names_:
                model_type = ModelType[name]
                if model_type.model.status():
                    Thread(target=self.__update_label_target, args=(model_type,)).start()
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