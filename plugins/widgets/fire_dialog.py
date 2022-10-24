from pioneersim.widgets.dialog import ObjectDialogLoader
from PyQt5.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QLabel

class FireDialogLoader(ObjectDialogLoader):

    @classmethod
    def get_interface(cls, fields) -> tuple[list[QLineEdit], list[QWidget]]:
        field_inputs = []
        widgets = []

        x_widget = QWidget()
        x_layout = QHBoxLayout(x_widget)
        x_text = QLabel()
        x_text.setText('Координата X')
        x_input = QLineEdit(str(fields[0][0]))
        x_layout.addWidget(x_text)
        x_layout.addWidget(x_input, 100)
        x_widget.setLayout(x_layout)
        field_inputs.append(x_input)
        widgets.append(x_widget)

        y_widget = QWidget()
        y_layout = QHBoxLayout(y_widget)
        y_text = QLabel()
        y_text.setText('Координата Y')
        y_input = QLineEdit(str(fields[0][1]))
        y_layout.addWidget(y_text)
        y_layout.addWidget(y_input, 100)
        y_widget.setLayout(y_layout)
        field_inputs.append(y_input)
        widgets.append(y_widget)

        return field_inputs, widgets