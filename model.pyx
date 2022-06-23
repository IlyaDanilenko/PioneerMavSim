cdef class FireModel:
    cdef public float x
    cdef public float y
    cdef public float temp

    def __init__(self, x = 0.0, y = 0.0, temp = 60.0):
        self.x = x
        self.y = y
        self.temp = temp

cdef class DroneModel:
    cdef public float x
    cdef public float y
    cdef public float z
    cdef public float yaw
    cdef public int speed
    cdef public tuple color
    cdef float default_temp_data
    cdef float temp_sensor_data
    cdef public bool takeoff_status
    cdef public bool preflight_status
    cdef public bool inprogress
    cdef tuple last_position

    def __init__(self, x = 0.0, y= 0.0, z = 0.0, yaw = 0.0, speed = 60):
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.speed = speed
        self.color = (0, 0, 0)
        self.__default_temp_data = 20.0
        self.__temp_sensor_data = 20.0

        self.takeoff_status = False
        self.preflight_status = False
        self.inprogress = False
        self.__last_position = (x, y, z, yaw)

    

