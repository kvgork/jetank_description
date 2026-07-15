cmake_minimum_required(VERSION 3.8)
project(jetank_description)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)

# Install resource directories. Each is installed only if present so the
# package builds cleanly when optional dirs (meshes/launch/config) are absent.
foreach(_dir urdf meshes launch config)
  if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/${_dir}")
    install(DIRECTORY ${_dir}/
      DESTINATION share/${PROJECT_NAME}/${_dir}
      PATTERN "__pycache__" EXCLUDE
    )
  endif()
endforeach()

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()

  # Verify the xacro robot model expands to valid URDF (the package deliverable).
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_urdf test/test_urdf.py)
endif()

ament_package()
