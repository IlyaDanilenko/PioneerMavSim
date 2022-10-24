from abc import ABC, abstractmethod
from PyQt5.QtWidgets import QWidget, QLineEdit

class ObjectDialogLoader(ABC):

    @classmethod
    @abstractmethod
    def get_interface(cls, fields) -> tuple[list[QLineEdit], list[QWidget]]:
        pass