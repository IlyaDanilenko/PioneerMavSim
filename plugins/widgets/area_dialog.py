from pioneersim.widgets.dialog import ObjectDialogLoader
from PyQt5.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QLabel

class AreaDialogLoader(ObjectDialogLoader):

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

        s1_widget = QWidget()
        s1_layout = QHBoxLayout(s1_widget)
        s1_text = QLabel()
        s1_text.setText('Размер X')
        s1_input = QLineEdit(str(fields[1][0]))
        s1_layout.addWidget(s1_text)
        s1_layout.addWidget(s1_input, 100)
        s1_widget.setLayout(s1_layout)
        field_inputs.append(s1_input)
        widgets.append(s1_widget)

        s2_widget = QWidget()
        s2_layout = QHBoxLayout(s2_widget)
        s2_text = QLabel()
        s2_text.setText('Размер Y')
        s2_input = QLineEdit(str(fields[1][1]))
        s2_layout.addWidget(s2_text)
        s2_layout.addWidget(s2_input, 100)
        s2_widget.setLayout(s2_layout)
        field_inputs.append(s2_input)
        widgets.append(s2_widget)

        s3_widget = QWidget()
        s3_layout = QHBoxLayout(s3_widget)
        s3_text = QLabel()
        s3_text.setText('Размер Z')
        s3_input = QLineEdit(str(fields[1][2]))
        s3_layout.addWidget(s3_text)
        s3_layout.addWidget(s3_input, 100)
        s3_widget.setLayout(s3_layout)
        field_inputs.append(s3_input)
        widgets.append(s3_widget)

        r_widget = QWidget()
        r_layout = QHBoxLayout(r_widget)
        r_text = QLabel()
        r_text.setText('Цвет R')
        r_input = QLineEdit(str(fields[2][0]))
        r_layout.addWidget(r_text)
        r_layout.addWidget(r_input, 100)
        r_widget.setLayout(r_layout)
        field_inputs.append(r_input)
        widgets.append(r_widget)

        g_widget = QWidget()
        g_layout = QHBoxLayout(g_widget)
        g_text = QLabel()
        g_text.setText('Цвет G')
        g_input = QLineEdit(str(fields[2][1]))
        g_layout.addWidget(g_text)
        g_layout.addWidget(g_input, 100)
        g_widget.setLayout(g_layout)
        field_inputs.append(g_input)
        widgets.append(g_widget)

        b_widget = QWidget()
        b_layout = QHBoxLayout(b_widget)
        b_text = QLabel()
        b_text.setText('Цвет B')
        b_input = QLineEdit(str(fields[2][2]))
        b_layout.addWidget(b_text)
        b_layout.addWidget(b_input, 100)
        b_widget.setLayout(b_layout)
        field_inputs.append(b_input)
        widgets.append(b_widget)

        return field_inputs, widgets