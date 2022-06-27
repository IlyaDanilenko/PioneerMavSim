from setuptools import Extension, setup
from Cython.Build import cythonize
import platform

if platform.system() == "Windows":
    openmp_name = "-openmp"
else:
    openmp_name = "-fopenmp"

print(openmp_name)

ext_modules = [
    Extension(
        "model",
        ["model.pyx"],
        extra_compile_args=[openmp_name],
        extra_link_args=[openmp_name],
    )
]

setup(
    ext_modules=cythonize(ext_modules),
)