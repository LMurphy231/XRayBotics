import numpy as np
#import RobotCommunicator as com

import AutomatedTests.pathsRemade as paths


def format_position(position: np.ndarray) -> str:
    """
    format_position()
    Format a position for display.

    Values that are effectively zero are displayed as 0.
    """

    position: np.ndarray = position.copy()

    # Replace values extremely close to zero with exactly zero
    position[np.isclose(position, 0.0)] = 0.0

    return np.array2string(position, precision=3)

def straight_path_simulation():

    # Define starting and ending positions
    p1: np.ndarray = np.array([10, 20, 30])
    p2: np.ndarray = np.array([20, 40, 60])

    # ============================================================
    # CREATE PATH
    # ============================================================

    path: list = paths.straight_path(p1, p2)

    # ============================================================
    # GENERAL INFORMATION
    # ============================================================

    print("\n========== STRAIGHT PATH SIMULATION ==========")

    print(f"Start position:  {format_position(p1)}")
    print(f"Target position: {format_position(p2)}")
    print(f"Displacement:    {format_position(p2 - p1)}")

    # ============================================================
    # PATH
    # ============================================================

    print("\n========== STRAIGHT PATH ==========")

    print(f"Number of moves: {len(path)}")

    current_position: np.ndarray = p1.copy()

    for i in range(len(path)):

        movement: np.ndarray = path[i]

        new_position: np.ndarray = current_position + movement

        print(f"\nMove {i + 1}")

        print(
            f"  Movement: "
            f"{format_position(movement)}"
        )

        print(
            f"  From:     "
            f"{format_position(current_position)}"
        )

        print(
            f"  To:       "
            f"{format_position(new_position)}"
        )

        current_position = new_position

    print("\nFinal position:")

    print(
        f"  Expected: "
        f"{format_position(p2)}"
    )

    print(
        f"  Actual:   "
        f"{format_position(current_position)}"
    )

    if np.allclose(current_position, p2):
        print("  Result:   SUCCESS")
    else:
        print("  Result:   ERROR")

    print("\n============================================")

# NOT ACTUAL IMPLEMENTATION - that's for Alan
# MOCK STRUCTURE PSEUDOCODE TO HELP WITH WRITING THE TEST LOGIC
class DataProcessing:
    
    def calculate_mean(data: list):
        mean: float = np.mean(data)
        return mean

    def find_max(data: list):
        maximum: float = np.max(data)
        return maximum

    def find_min(data: list):
        minimum: float = np.min(data)
        return minimum

    def get_center_1(data: list):
        '''
        get_center_1
        Mock function representing processing of scan data
        to determine a center position and corresponding
        light intensity.

        center = (max + min) / 2
        '''

        # Placeholder processing
        return

    def get_center_2(data: list):
        '''
        get_center_2
        Mock function representing processing of scan data
        to determine a second center position and corresponding
        light intensity.

        center = (max + min) / 2
        '''

        # Placeholder processing
        return

    def get_offset(data: list):
        '''
        get_offset
        Mock function representing calculation of an offset.

        offset = max - min
        '''

        # Placeholder processing
        return


def gravity_test_automated_simulation():
    """
    gravity_test_automated_simulation()
    Simulate the automated gravity test.
    """

    print("\n============================================================")
    print("              GRAVITY TEST SIMULATION")
    print("============================================================")

    # ============================================================
    # TEST PARAMETERS
    # ============================================================

    est_isocenter: np.ndarray = np.array([0.0, 0.0, 0.0])
    length: float = 5.0
    width: float = 5.0
    angle: float = 45.0

    # Gravity test is performed in the YZ plane
    grav_test_axes: tuple = ("y", "z")

    print("\n========== TEST PARAMETERS ==========")
    print(
        f"Isocenter: "
        f"{format_position(est_isocenter)}"
    )
    print(f"Length:    {length:.3f}")
    print(f"Width:     {width:.3f}")
    print(f"Angle:     {angle:.3f} degrees")
    print(
        f"Axes:      "
        f"{grav_test_axes[0].upper()}, "
        f"{grav_test_axes[1].upper()}"
    )
    print("=====================================")

    # ============================================================
    # CALCULATE FOUR POINTS
    # ============================================================

    print("\n========== CALCULATE FOUR POINTS ==========")

    rectangle_points: list = paths.calculate_four_points_rectangle(est_isocenter, length, width, grav_test_axes[0], grav_test_axes[1])

    for i in range(len(rectangle_points)):
        print(
            f"P{i + 1}: "
            f"{format_position(rectangle_points[i])}"
        )

    print("===========================================")

    # ============================================================
    # ROTATE POINTS
    # ============================================================

    print("\n========== ROTATE POINTS ==========")

    # Determine rotation axis
    if grav_test_axes[0] == "x" and grav_test_axes[1] == "y":
        rotation_axis: str = "z"

    elif grav_test_axes[0] == "x" and grav_test_axes[1] == "z":
        rotation_axis: str = "y"

    elif grav_test_axes[0] == "y" and grav_test_axes[1] == "z":
        rotation_axis: str = "x"

    else:
        raise ValueError("Invalid plane axes.")

    print(f"Rotation angle: {angle:.3f} degrees")
    print(f"Rotation axis:  {rotation_axis.upper()}")

    if angle != 0.0:

        rectangle_points = paths.rotate_points(
            rectangle_points,
            angle,
            grav_test_axes[0],
            grav_test_axes[1]
        )

    for i in range(len(rectangle_points)):

        print(
            f"P{i + 1}: "
            f"{format_position(rectangle_points[i])}"
        )

    print("===================================")

    # ============================================================
    # CREATE RECTANGLE PATH
    # ============================================================

    print("\n========== CREATE RECTANGLE PATH ==========")

    rectangle_paths: list = paths.rectangle_path(est_isocenter, rectangle_points)

    print("===========================================")

    # ============================================================
    # EXECUTE GRAVITY TEST
    # ============================================================

    print("\n========== EXECUTE GRAVITY TEST ==========")

    scan_data: list = movement_functions_simulation(rectangle_paths, step_length=1.0)

    print("==========================================")

    return scan_data

def path_functions_simulation(isocenter: np.ndarray, length: float, width: float,
                              angle: float, axis_1: str, axis_2: str):
    """
    path_functions_simulation()
    Test calculate_four_points_rectangle(), rotate_points(), and rectangle_path().
    """

    print("\n============================================================")
    print("              PATH FUNCTIONS SIMULATION")
    print("============================================================")

    # ============================================================
    # TEST PARAMETERS
    # ============================================================

    print("\n========== TEST PARAMETERS ==========")

    print(
        f"Isocenter: "
        f"{format_position(isocenter)}"
    )

    print(f"Length:    {length:.3f}")
    print(f"Width:     {width:.3f}")
    print(f"Angle:     {angle:.3f} degrees")
    print(f"Axes:      {axis_1.upper()}, {axis_2.upper()}")

    print("=====================================")

    # ============================================================
    # CALCULATE FOUR POINTS
    # ============================================================

    print("\n========== CALCULATE FOUR POINTS ==========")

    points: list = paths.calculate_four_points_rectangle(
        isocenter,
        length,
        width,
        axis_1,
        axis_2
    )

    for i in range(len(points)):

        print(
            f"P{i + 1}: "
            f"{format_position(points[i])}"
        )

    print("===========================================")

    # ============================================================
    # ROTATE POINTS
    # ============================================================

    print("\n========== ROTATE POINTS ==========")

    # Determine rotation axis
    if axis_1 == "x" and axis_2 == "y":
        rotation_axis: str = "z"

    elif axis_1 == "x" and axis_2 == "z":
        rotation_axis: str = "y"

    elif axis_1 == "y" and axis_2 == "z":
        rotation_axis: str = "x"

    else:
        raise ValueError("Invalid plane axes.")

    print(f"Rotation angle: {angle:.3f} degrees")
    print(f"Rotation axis:  {rotation_axis.upper()}")

    if angle != 0.0:

        path_points: list = paths.rotate_points(
            points,
            angle,
            axis_1,
            axis_2
        )

    else:

        path_points: list = points

    for i in range(len(path_points)):

        print(
            f"P{i + 1}: "
            f"{format_position(path_points[i])}"
        )

    print("===================================")

    # ============================================================
    # CREATE RECTANGLE PATH
    # ============================================================

    print("\n========== CREATE RECTANGLE PATH ==========")

    rectangle_paths: list = paths.rectangle_path(
        isocenter,
        path_points
    )

    print("===========================================")

    # ============================================================
    # DISPLAY PATH INFORMATION
    # ============================================================

    print("\n========== PATH INFORMATION ==========")

    for i in range(len(rectangle_paths)):

        movement_path: list = rectangle_paths[i][0]
        scan: bool = rectangle_paths[i][1]
        start_position: np.ndarray = rectangle_paths[i][2]

        print(f"\nPath {i + 1}")

        if i == 0:
            print("  Path: Isocenter -> P1")

        elif i == 1:
            print("  Path: P1 -> P2")

        elif i == 2:
            print("  Path: P2 -> P3")

        elif i == 3:
            print("  Path: P3 -> P4")

        print(
            f"  Start: "
            f"{format_position(start_position)}"
        )

        print(f"  Scan:  {scan}")
        print(f"  Num moves: {len(movement_path)}")

        for j in range(len(movement_path)):

            print(
                f"    Movement {j + 1}: "
                f"{format_position(movement_path[j])}"
            )

    print("\n=====================================")

    return rectangle_paths

def movement_functions_simulation(rectangle_paths: list,
                                  step_length: float = 1.0):
    """
    movement_functions_simulation()
    Test movement functions using an already-created rectangle path.

    Robot movement and light sensor readings are simulated.
    """

    print("\n============================================================")
    print("             MOVEMENT FUNCTIONS SIMULATION")
    print("============================================================")

    # ============================================================
    # TEST PARAMETERS
    # ============================================================

    print("\n========== MOVEMENT TEST PARAMETERS ==========")

    print(f"Step length: {step_length:.3f}")

    print("==============================================")

    # ============================================================
    # INITIALIZE DATA
    # ============================================================

    scan_data: list = []

    current_position: np.ndarray = (
        rectangle_paths[0][2].copy()
    )

    print("\n========== INITIAL POSITION ==========")

    print(
        f"Robot position: "
        f"{format_position(current_position)}"
    )

    print("======================================")

    # ============================================================
    # EXECUTE PATH
    # ============================================================

    print("\n========== EXECUTE PATH ==========")

    for i in range(len(rectangle_paths)):

        movement_path: list = rectangle_paths[i][0]
        scan: bool = rectangle_paths[i][1]
        start_position: np.ndarray = rectangle_paths[i][2]

        print(f"\n--- Executing Path {i + 1} ---")

        print(
            f"Start position: "
            f"{format_position(start_position)}"
        )

        print(f"Scan: {scan}")

        # --------------------------------------------------------
        # MOVE + SCAN
        # --------------------------------------------------------

        if scan:

            print("Action: MOVE + SCAN")

            current_position = start_position.copy()

            for displacement in movement_path:

                mag_displacement: float = np.linalg.norm(
                    displacement
                )

                if mag_displacement == 0:
                    continue

                n_steps: int = int(
                    np.ceil(mag_displacement / step_length)
                )

                movement: np.ndarray = (
                    displacement / n_steps
                )

                for j in range(n_steps):

                    previous_position: np.ndarray = (
                        current_position.copy()
                    )

                    # Simulate robot movement
                    current_position = (
                        current_position + movement
                    )

                    print(f"\n  Step {j + 1}/{n_steps}")

                    print(
                        f"    Movement: "
                        f"{format_position(movement)}"
                    )

                    print(
                        f"    From:     "
                        f"{format_position(previous_position)}"
                    )

                    print(
                        f"    To:       "
                        f"{format_position(current_position)}"
                    )

                    # Simulate light sensor
                    light_intensity: float = np.random.uniform(
                        0.0,
                        1.0
                    )

                    print(
                        f"    Light:    "
                        f"{light_intensity:.3f}"
                    )

                    # Store position + light
                    scan_result: tuple = (
                        current_position.copy(),
                        light_intensity
                    )

                    scan_data.append(scan_result)

                    print("    Data stored.")

        # --------------------------------------------------------
        # MOVE ONLY
        # --------------------------------------------------------

        else:

            print("Action: MOVE ONLY")

            for displacement in movement_path:

                previous_position: np.ndarray = (
                    current_position.copy()
                )

                # Simulate robot movement
                current_position = (
                    current_position + displacement
                )

                print("\n  Move")

                print(
                    f"    Movement: "
                    f"{format_position(displacement)}"
                )

                print(
                    f"    From:     "
                    f"{format_position(previous_position)}"
                )

                print(
                    f"    To:       "
                    f"{format_position(current_position)}"
                )

    print("\nPath execution complete.")

    print("===================================")

    # ============================================================
    # DISPLAY COLLECTED DATA
    # ============================================================

    print("\n========== COLLECTED DATA ==========")

    print(f"Number of scans: {len(scan_data)}")

    for i in range(len(scan_data)):

        position: np.ndarray = scan_data[i][0]
        light_intensity: float = scan_data[i][1]

        print(f"\n  Scan {i + 1}")

        print(
            f"    Position: "
            f"{format_position(position)}"
        )

        print(
            f"    Light:    "
            f"{light_intensity:.3f}"
        )

    print("====================================")

    # ============================================================
    # FINAL POSITION
    # ============================================================

    print("\n========== FINAL POSITION ==========")

    print(
        f"Final robot position: "
        f"{format_position(current_position)}"
    )

    print("====================================")

    return scan_data


# SELF-SIMULATION ONLY; FOR MARC'S SUBSYSTEM MEETING AND DOCUMENTATION
def main():

    # ============================================================
    # PATH + MOVEMENT SIMULATION
    # ============================================================

    isocenter: np.ndarray = np.array([0.0, 0.0, 0.0])

    length: float = 5.0
    width: float = 5.0
    angle: float = 90.0

    axis_1: str = "x"
    axis_2: str = "y"

    step_length: float = 1.0

    # Create and display path
    path: list = path_functions_simulation(isocenter, length, width ,angle, axis_1, axis_2)

    # Execute path and simulate scanning
    scan_data: list = movement_functions_simulation(path, step_length)

    # ============================================================
    # GRAVITY TEST SIMULATION
    # ============================================================

    # Uncomment to run gravity test simulation
    gravity_test_scan_data: list = gravity_test_automated_simulation()


if __name__ == "__main__":
    main()
    















# OLD PSEDUOCDOE BELOW
# for direction_name, move_vec in path:
    # start.move(path)
        # scan light while moving
        # append.light_data[]                   # Store light intensity data
        # append.grav_test_position_data[]      # Store positional data (movement vectors)
        # tuple = append.[(dx,dy,dz), light_intensity]  # TODO: Tuple array possibly
    # end.move(path)

# end_data_recording()

# Process data (call needed DataProcessing.function() functions)
    # center1 = get_center_1(tuple)                     # Returns: (x,y,z) and light_intensity
    # center2 = get_center_2(tuple)                     # Returns: (x,y,z) and light_intensity
    # offset = get_offset(grav_test_position_data[])    # Returns offset 

# Didn't find satisfactory light data
    # if (light_data < threshold)
        # path = paths.move_up_to_max_z(x,y,z, *args) # Move up to max z for a new path (different parameters)
        # start_data_recording()
            # start.move(path)
                # scan light while moving
                # append.light_data[]                   # Store light intensity data
                # append.grav_test_position_data[]      # Store positional data (movement vectors)
                # tuple = append.[(dx,dy,dz), light_intensity]  # TODO: Tuple array possibly
            # end.move(path)
        # end_data_recording()

# Continue Here TODO