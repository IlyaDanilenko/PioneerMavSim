from pioneersim.widgets.dialog import ObjectDialogLoader
from PyQt5.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QLabel

class DroneROSDialogLoader(ObjectDialogLoader):

    @classmethod
    def get_interface(cls, fields) -> tuple[list[QLineEdit], list[QWidget]]:
        field_inputs = []
        widgets = []

        port_widget = QWidget()
        port_layout = QHBoxLayout(port_widget)
        port_text = QLabel()
        port_text.setText('Порт')
        port_input = QLineEdit(str(fields[0]))
        port_layout.addWidget(port_text)
        port_layout.addWidget(port_input, 100)
        port_widget.setLayout(port_layout)
        field_inputs.append(port_input)
        widgets.append(port_widget)

        workspace_widget = QWidget()
        workspace_layout = QHBoxLayout(workspace_widget)
        workspace_text = QLabel()
        workspace_text.setText('Рабочая область')
        workspace_input = QLineEdit(str(fields[1]))
        workspace_layout.addWidget(workspace_text)
        workspace_layout.addWidget(workspace_input, 100)
        workspace_widget.setLayout(workspace_layout)
        field_inputs.append(workspace_input)
        widgets.append(workspace_widget)

        r_widget = QWidget()
        r_layout = QHBoxLayout(r_widget)
        r_text = QLabel()
        r_text.setText('Цвет траектории R')
        r_input = QLineEdit(str(fields[2][0]))
        r_layout.addWidget(r_text)
        r_layout.addWidget(r_input, 100)
        r_widget.setLayout(r_layout)
        field_inputs.append(r_input)
        widgets.append(r_widget)

        g_widget = QWidget()
        g_layout = QHBoxLayout(g_widget)
        g_text = QLabel()
        g_text.setText('Цвет траектории G')
        g_input = QLineEdit(str(fields[2][1]))
        g_layout.addWidget(g_text)
        g_layout.addWidget(g_input, 100)
        g_widget.setLayout(g_layout)
        field_inputs.append(g_input)
        widgets.append(g_widget)

        b_widget = QWidget()
        b_layout = QHBoxLayout(b_widget)
        b_text = QLabel()
        b_text.setText('Цвет траектории B')
        b_input = QLineEdit(str(fields[2][2]))
        b_layout.addWidget(b_text)
        b_layout.addWidget(b_input, 100)
        b_widget.setLayout(b_layout)
        field_inputs.append(b_input)
        widgets.append(b_widget)

        return field_inputs, widgets