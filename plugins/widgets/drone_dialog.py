from pioneersim.widgets.dialog import ObjectDialogLoader
from PyQt5.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QLabel

class DroneDialogLoader(ObjectDialogLoader):

    @classmethod
    def get_interface(cls, fields) -> tuple[list[QLineEdit], list[QWidget]]:
        field_inputs = []
        widgets = []

        hostname_widget = QWidget()
        hostname_layout = QHBoxLayout(hostname_widget)
        hostname_text = QLabel()
        hostname_text.setText('Хост')
        hostname_input = QLineEdit(fields[0])
        hostname_layout.addWidget(hostname_text)
        hostname_layout.addWidget(hostname_input, 100)
        hostname_widget.setLayout(hostname_layout)
        field_inputs.append(hostname_input)
        widgets.append(hostname_widget)

        port_widget = QWidget()
        port_layout = QHBoxLayout(port_widget)
        port_text = QLabel()
        port_text.setText('Порт')
        port_input = QLineEdit(str(fields[1]))
        port_layout.addWidget(port_text)
        port_layout.addWidget(port_input, 100)
        port_widget.setLayout(port_layout)
        field_inputs.append(port_input)
        widgets.append(port_widget)

        x_widget = QWidget()
        x_layout = QHBoxLayout(x_widget)
        x_text = QLabel()
        x_text.setText('Координата X')
        x_input = QLineEdit(str(fields[2][0]))
        x_layout.addWidget(x_text)
        x_layout.addWidget(x_input, 100)
        x_widget.setLayout(x_layout)
        field_inputs.append(x_input)
        widgets.append(x_widget)

        y_widget = QWidget()
        y_layout = QHBoxLayout(y_widget)
        y_text = QLabel()
        y_text.setText('Координата Y')
        y_input = QLineEdit(str(fields[2][1]))
        y_layout.addWidget(y_text)
        y_layout.addWidget(y_input, 100)
        y_widget.setLayout(y_layout)
        field_inputs.append(y_input)
        widgets.append(y_widget)

        z_widget = QWidget()
        z_layout = QHBoxLayout(z_widget)
        z_text = QLabel()
        z_text.setText('Координата Z')
        z_input = QLineEdit(str(fields[2][2]))
        z_layout.addWidget(z_text)
        z_layout.addWidget(z_input, 100)
        z_widget.setLayout(z_layout)
        field_inputs.append(z_input)
        widgets.append(z_widget)

        r_widget = QWidget()
        r_layout = QHBoxLayout(r_widget)
        r_text = QLabel()
        r_text.setText('Цвет траектории R')
        r_input = QLineEdit(str(fields[3][0]))
        r_layout.addWidget(r_text)
        r_layout.addWidget(r_input, 100)
        r_widget.setLayout(r_layout)
        field_inputs.append(r_input)
        widgets.append(r_widget)

        g_widget = QWidget()
        g_layout = QHBoxLayout(g_widget)
        g_text = QLabel()
        g_text.setText('Цвет траектории G')
        g_input = QLineEdit(str(fields[3][1]))
        g_layout.addWidget(g_text)
        g_layout.addWidget(g_input, 100)
        g_widget.setLayout(g_layout)
        field_inputs.append(g_input)
        widgets.append(g_widget)

        b_widget = QWidget()
        b_layout = QHBoxLayout(b_widget)
        b_text = QLabel()
        b_text.setText('Цвет траектории B')
        b_input = QLineEdit(str(fields[3][2]))
        b_layout.addWidget(b_text)
        b_layout.addWidget(b_input, 100)
        b_widget.setLayout(b_layout)
        field_inputs.append(b_input)
        widgets.append(b_widget)

        return field_inputs, widgets