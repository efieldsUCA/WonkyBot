from setuptools import find_packages, setup
import os
from glob import glob

package_name = "solid_octo"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "configs"),
            glob(os.path.join("configs", "*.yaml")),
        ),
        (
            os.path.join("share", package_name, "config"),
            glob(os.path.join("config", "*.yaml")),
        ),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*.py")),
        ),
    ],
    package_data={"solid_octo": ["colors.json"]},
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="robopi",
    maintainer_email="robopi@todo.todo",
    description="TODO: Package description",
    license="MIT",
    extras_require={
        "test": [
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [
            "diff_drive_controller = solid_octo.diff_drive_controller:main",
            "octo_pilot = solid_octo.octo_pilot:main",
            "blind_navigator = solid_octo.blind_navigator:main",
            "detector_node = solid_octo.detector_node:main",
            "sorting_master = solid_octo.sorting_master:main",
            "waypoint_navigator = solid_octo.waypoint_navigator:main",
            "vision_tester = solid_octo.vision_tester:main",
            "detection_3d = solid_octo.detection_3d_node:main",
        ],
    },
)
