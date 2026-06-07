# Copyright 2024 koen
#
# Licensed under the MIT License.
"""Exercise the package deliverable: expand the xacro model to valid URDF.

These tests run ``xacro`` on the real robot description files shipped by this
package and assert the resulting URDF parses as XML, has a ``<robot>`` root, and
contains the expected kinematic links. No ROS runtime is required.
"""
import os
import xml.etree.ElementTree as ET

import pytest
import xacro

# urdf/ lives one level up from this test/ directory in the package source tree.
URDF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "urdf")


def _process(filename, mappings=None):
    """Run xacro on a description file and return (xml_string, set_of_link_names)."""
    path = os.path.join(URDF_DIR, filename)
    assert os.path.isfile(path), f"missing description file: {path}"
    doc = xacro.process_file(path, mappings=mappings or {})
    xml = doc.toxml()
    root = ET.fromstring(xml)
    assert root.tag == "robot", f"expected <robot> root, got <{root.tag}>"
    links = {link.get("name") for link in root.iter("link")}
    return xml, links


def test_jetank_xacro_expands_to_robot():
    """The self-contained jetank.xacro expands to a non-empty URDF robot."""
    xml, links = _process("jetank.xacro")
    assert len(xml) > 0
    # Core frames and a representative link from each component subtree.
    for expected in (
        "base_link",
        "chassis",
        "imu_link",
        "camera_base_plate_link",
        "arm_base_link",
        "gripper_base_link",
        "laser",
    ):
        assert expected in links, f"{expected!r} missing from {sorted(links)}"
    # Diff-drive base has six wheels in this model.
    wheel_links = {name for name in links if name and name.endswith("_wheel")}
    assert len(wheel_links) == 6, f"expected 6 wheels, got {sorted(wheel_links)}"


def test_top_entrypoint_expands_without_ros2_control():
    """The documented top entrypoint expands; ros2_control off keeps it self-contained.

    With use_ros2_control:=false the model does not pull in the sibling
    jetank_motor_control package, so this exercises only jetank_description.
    """
    xml, links = _process(
        "jetank_ros2_control.urdf.xacro", mappings={"use_ros2_control": "false"}
    )
    assert len(xml) > 0
    for expected in (
        "base_footprint",
        "base_link",
        "chassis",
        "camera_link",
        "imu_link",
        "laser",
    ):
        assert expected in links, f"{expected!r} missing from {sorted(links)}"
    # Arm chain S1..S5 must be present.
    for i in range(1, 6):
        assert f"S{i}_link" in links, f"S{i}_link missing from {sorted(links)}"


@pytest.mark.parametrize("filename", ["jetank.xacro", "jetank_ros2_control.urdf.xacro"])
def test_robot_name_is_jetank(filename):
    """Both entrypoints name the robot 'jetank' (consumed by RViz/MoveIt/Gazebo)."""
    mappings = {"use_ros2_control": "false"} if "ros2_control" in filename else {}
    xml, _ = _process(filename, mappings=mappings)
    root = ET.fromstring(xml)
    assert root.get("name") == "jetank"
