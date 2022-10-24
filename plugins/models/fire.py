from math import hypot
from pioneersim.simulation.model import Model

class FireModel(Model):
    def __init__(self, id = 0, x = 0.0, y = 0.0, min_temp = 20.0, max_temp = 60.0, radius = 0.5):
        self.id = id
        self.x = x
        self.y = y
        self.__min_temp = min_temp
        self.__max_temp = max_temp
        self.__radius = radius

    def set_position(self, x : float, y : float):
        self.x = x
        self.y = y

    def get_status(self) -> dict:
        return {"min_temp" : self.__min_temp, "max_temp" : self.__max_temp}

    def get_temp(self, position, static = True):
        dist = lambda p1, p2: hypot((p2[0] - p1[0]), (p2[1] - p1[1]))

        distance = dist(position, (self.x , self.y))

        if distance >= self.__radius:
            return self.__min_temp
        else:
            if static:
                return self.__max_temp
            else:
                k = 1 - distance / self.__radius
                t = k * (self.__max_temp - self.__min_temp)
                return self.__min_temp + t

    @classmethod
    def pack(cls, data) -> dict:
        data_dict = {}
        position_dict = {}
        position_dict['x'] = data[0][0]
        position_dict['y'] = data[0][1]
        data_dict['position'] = position_dict
        return data_dict

    @classmethod
    def unpack(cls, data) -> list:
        position = (data['position']['x'], data['position']['y'])
        return [position]

    @classmethod
    def model_name(cls) -> str:
        return 'fire'

    @classmethod
    def status(self) -> bool:
        return False

    @classmethod
    def check_fields(self, fields):
        return True

    @classmethod
    def get_description(cls, field) -> str:
        return f"Позиция: {field[0]}"

    @classmethod
    def transform(cls, fields = None) -> list:
        if fields is None:
            return [(0.0, 0.0)]
        else:
            return [(float(fields[0]), float(fields[1]))]