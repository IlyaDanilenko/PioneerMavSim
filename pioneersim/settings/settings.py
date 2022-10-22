class SimulationSettings:
    def __init__(self, simulation : dict):
        self.speed = simulation['drone']['speed']
        self.battery_need = simulation['drone']['battery_need']
        self.battery_capacity = simulation['drone']['battery_capacity']
        self.battery_max = simulation['drone']['battery_max']
        self.battery_off = simulation['drone']['battery_off']
        self.fire_static = simulation['fire']['static']
        self.fire_radius = simulation['fire']['radius']
        self.fire_min_temp = simulation['fire']['min_temp']
        self.fire_max_temp = simulation['fire']['max_temp']