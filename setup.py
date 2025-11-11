from setuptools import setup, find_packages
import os

# Read version from version module
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'hbos_bluetooth_service', '_version.py')
    with open(version_file, 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"\'')
    raise RuntimeError('Unable to find version string.')

# Read requirements from requirements.txt
with open(os.path.join(os.path.dirname(__file__), "requirements.txt")) as f:
    requirements = [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]

setup(
    name="hbos-bluetooth-service",
    version=get_version(),
    description="HiFiBerry Bluetooth Service",
    long_description="HiFiBerry Bluetooth Service, that manages all the incomming Bluetooth connections. "
                     "The settings can be adjusted via the web interface or a config file.",
    author="HiFiBerry",
    author_email="support@hifiberry.com",
    license="MIT",
    packages=find_packages(),
    install_requires=requirements,
    data_files=[
        ('/usr/lib/systemd/system', [
            'systemd/hbos-bluetooth.service'
        ]),
        ('/usr/share/man/man1', [
            'man/hbos-bluetooth.1'
        ]),
    ],
    entry_points={
        "console_scripts": [
            "hbos-bluetooth=hbos_bluetooth_service.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)


