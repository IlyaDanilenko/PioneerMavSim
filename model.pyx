# distutils: language=c++

from libcpp cimport bool
from libc.math cimport sqrt, modf
from cython.parallel import prange

cdef extern from *:
    """
    #if defined(_WIN32) || defined(MS_WINDOWS) || defined(_MSC_VER)
      #include "stdlib.h"
      #define myapp_sleep(m)  _sleep(m)
    #else
      #include <unistd.h>
      #define myapp_sleep(m)  ((void) usleep((m) * 1000))
    #endif
    """
    # using "myapp_" prefix in the C code to prevent C naming conflicts
    void sleep "myapp_sleep"(int milliseconds) nogil


cdef class FireModel:
    cdef public float x
    cdef public float y
    cdef public float temp

    def __init__(self, x = 0.0, y = 0.0, temp = 60.0):
        self.x = x
        self.y = y
        self.temp = temp

    def get_status(self) -> dict:
        return {"temp" : self.temp}

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
        self.default_temp_data = 20.0
        self.temp_sensor_data = 20.0

        self.takeoff_status = False
        self.preflight_status = False
        self.inprogress = False
        self.last_position = (x, y, z, yaw)

    def set_color(self, r = 0, g = 0, b = 0):
        self.color = (r, g, b)

    def set_temp_sensor_data(self, data = None):
        if data is None:
            if self.temp_sensor_data != self.default_temp_data:
                self.temp_sensor_data = self.default_temp_data
        else:
            if self.temp_sensor_data != data:
                self.temp_sensor_data = data

    def get_temp_sensor_data(self) -> float:
        return self.temp_sensor_data

    def check_pos(self, x : float, y : float, z : float, yaw : float) -> bool:
        return (x, y, z, yaw) != self.last_position

    def set_pos(self, x : float, y : float, z : float, yaw : float):
        self.last_position = (x, y, z, yaw)

    def go_to_point(self, x : float, y : float, z : float):
        cdef float delta_x = x - self.x
        cdef float delta_y = y - self.y
        cdef float delta_z = z - self.z
        cdef Py_ssize_t i
        cdef float l = sqrt(delta_x ** 2 + delta_y ** 2 + delta_z ** 2)
        cdef int n = int((l * 100) - 1)
        for i in prange(n, nogil = True):
            self.x += delta_x / l * 0.01
            self.y += delta_y / l * 0.01
            self.z += delta_z / l * 0.01
            sleep(1000 // self.speed)

    def update_yaw(self, angle : float):
        cdef int old_angle = int(self.yaw)
        cdef int pri = 1
        if angle < 0.0:
            pri = -1
        cdef int new_angle
        cdef int n = old_angle + int(angle)
        for new_angle in prange(old_angle, n, pri, nogil = True):
            self.yaw = float(new_angle)
            sleep(1000 // self.speed)

    def takeoff(self):
        self.inprogress = True
        cdef Py_ssize_t i
        for i in prange(100, nogil = True):
            self.z += 0.01
            sleep(1000 // self.speed)
        self.takeoff_status = True
        self.inprogress = False

    def landing(self):
        self.inprogress = True
        cdef Py_ssize_t i
        cdef int n = int(self.z * 100)
        for i in prange(n, nogil = True):
            self.z -= 0.01
            sleep(1000 // self.speed)
        self.takeoff_status = False
        self.preflight_status = False
        self.inprogress = False

    def disarm(self):
        self.z = 0.0
        self.preflight_status = False
        self.takeoff_status = False