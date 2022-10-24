from abc import ABC, abstractmethod

class Model(ABC):

    @abstractmethod
    def get_status(self) -> dict:
        pass

    @classmethod
    @abstractmethod
    def pack(cls, data) -> dict:
        pass

    @classmethod
    @abstractmethod
    def unpack(cls, data) -> list:
        pass

    @classmethod
    @abstractmethod
    def model_name(self) -> str:
        pass

    @classmethod
    @abstractmethod
    def status(cls) -> bool:
        pass

    @classmethod
    @abstractmethod
    def check_fields(cls, fields) -> bool:
        pass

    @classmethod
    @abstractmethod
    def get_description(cls, field) -> str:
        pass

    @classmethod
    @abstractmethod
    def transform(cls, fields = None) -> list:
        pass