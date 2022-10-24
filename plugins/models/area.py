from pioneersim.simulation.model import Model

class AreaModel(Model):
    def __init__(self, x = 0.0, y = 0.0, scale = (0.0, 0.0, 0.0)):
        self.x = x
        self.y = y
        self.scale = scale

    def set_position(self, x : float, y : float):
        self.x = x
        self.y = y

    def get_status(self) -> dict:
        return {}

    @classmethod
    def pack(cls, data) -> dict:
        data_dict = {}
        position_dict = {}
        position_dict['x'] = data[0][0]
        position_dict['y'] = data[0][1]
        data_dict['position'] = position_dict

        scale_dict = {}
        scale_dict['x'] = data[1][0]
        scale_dict['y'] = data[1][1]
        scale_dict['z'] = data[1][2]
        data_dict['scale'] = scale_dict

        color_dict = {}
        color_dict['r'] = data[2][0]
        color_dict['g'] = data[2][1]
        color_dict['b'] = data[2][2]

        data_dict['color'] = color_dict
        return data_dict

    @classmethod
    def unpack(cls, data) -> list:
        position = (data['position']['x'], data['position']['y'])
        scale = (data['scale']['x'], data['scale']['y'], data['scale']['z'])
        color = (data['color']['r'], data['color']['g'], data['color']['b'])
        return [position, scale, color]

    @classmethod
    def model_name(cls) -> str:
        return 'area'

    @classmethod
    def status(cls) -> bool:
        return False

    @classmethod
    def check_fields(cls, fields) -> bool:
        return True

    @classmethod
    def get_description(cls, field) -> str:
        return f"Позиция: {field[0]}, Размер: {field[1]}, Цвет: {field[2]}"

    @classmethod
    def transform(cls, fields = None) -> list:
        if fields is None:
            return [(0.0, 0.0), (0.0, 0.0, 0.0), (0, 0, 0)]
        else:
            return [(float(fields[0]), float(fields[1])), (float(fields[2]), float(fields[3]), float(fields[4])), (int(fields[5]), int(fields[6]), int(fields[7]))]