import numpy as np
#import RobotCommunicator as com

import AutomatedTests.pathsRemade as paths


def straight_path_simulation():

    # Define starting and ending positions
    p1: np.ndarray = np.array([10, 20, 30])
    p2: np.ndarray = np.array([20, 40, 60])

    increment: int = 5 # Define number of movements

    # ============================================================
    # CREATE PATHS
    # ============================================================

    # Create straight-path moveset (incremental)
    increment_path: list = paths.straight_path(p1, p2, increment, True)

    # Create straight-path moveset (non-incremental)
    direct_path: list = paths.straight_path(p1, p2, increment, False)

    # ============================================================
    # GENERAL INFORMATION
    # ============================================================
    
    print("\n========== STRAIGHT PATH SIMULATION ==========")

    print(f"Start position:  {p1}")
    print(f"Target position: {p2}")
    print(f"Displacement:    {p2 - p1}")
    print(f"Increments:      {increment}")

    # ============================================================
    # INCREMENTAL PATH
    # ============================================================
    
    print("\n========== INCREMENTAL PATH ==========")

    print(f"Number of moves: {len(increment_path)}")

    current_position: np.ndarray = p1.copy()

    for i in range(len(increment_path)):

        movement: np.ndarray = increment_path[i]

        new_position: np.ndarray = current_position + movement

        print(f"\nMove {i + 1}")
        print(f"  Movement: {np.array2string(movement, precision=3)}")
        print(f"  From:     {np.array2string(current_position, precision=3)}")
        print(f"  To:       {np.array2string(new_position, precision=3)}")

        current_position = new_position

    print("\nFinal position:")
    print(f"  Expected: {np.array2string(p2, precision=3)}")
    print(f"  Actual:   {np.array2string(current_position, precision=3)}")

    if np.allclose(current_position, p2):
        print("  Result:   SUCCESS")
    else:
        print("  Result:   ERROR")


    # ============================================================
    # NON-INCREMENTAL PATH
    # ============================================================

    print("\n========== NON-INCREMENTAL PATH ==========")

    print(f"Number of moves: {len(direct_path)}")

    current_position = p1.copy()

    for i in range(len(direct_path)):

        movement: np.ndarray = direct_path[i]

        new_position: np.ndarray = current_position + movement

        print(f"\nMove {i + 1}")
        print(f"  Movement: {np.array2string(movement, precision=3)}")
        print(f"  From:     {np.array2string(current_position, precision=3)}")
        print(f"  To:       {np.array2string(new_position, precision=3)}")

        current_position = new_position

    print("\nFinal position:")
    print(f"  Expected: {np.array2string(p2, precision=3)}")
    print(f"  Actual:   {np.array2string(current_position, precision=3)}")

    if np.allclose(current_position, p2):
        print("  Result:   SUCCESS")
    else:
        print("  Result:   ERROR")

    print("\n============================================")



# NOT ACTUAL IMPLEMENTATION - that's for Alan
# MOCK STRUCTURE PSEUDOCODE TO HELP WITH WRITING THE TEST LOGIC
class DataProcessing:

    def calculate_mean(data: list):
        '''
        calculate_mean
        Calculate the mean of a list of numerical data.
        '''
        mean: float = np.mean(data)

        return mean

    def find_max(data: list):
        '''
        find_max
        Find the maximum value in a list of numerical data.
        '''
        maximum: float = np.max(data)

        return maximum

    def find_min(data: list):
        '''
        find_min
        Find the minimum value in a list of numerical data.
        '''
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

    print("\n")
    print("============================================================")
    print("           GRAVITY TEST AUTOMATED SIMULATION")
    print("============================================================")

    # ============================================================
    # INITIALIZE TEST PARAMETERS
    # ============================================================

    # Randomly generate estimated isocenter
    #x: float = np.random.uniform(-100, 100)
    #y: float = np.random.uniform(-100, 100)
    #z: float = np.random.uniform(-100, 100)
    
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    freq: int = 4500
    Navg: int = 4
    threshold: float = 0.75

    step: int = 1
    length: float = 50     # mm
    width: float = 50       # mm
    #angle: float = np.random.uniform(0, 180)        # Degrees
    angle: float = 0.0

    fr5 = None

    print("\n========== TEST PARAMETERS ==========")

    print(f"Estimated X:        {x:.3f}")
    print(f"Estimated Y:        {y:.3f}")
    print(f"Estimated Z:        {z:.3f}")

    print(f"Frequency:          {freq:.3f}")
    print(f"Number of averages: {Navg:.3f}")
    print(f"Threshold:          {threshold:.3f}")

    print(f"Step:               {step:.3f}")
    print(f"Length:             {length:.3f}")
    print(f"Width:              {width:.3f}")
    print(f"Angle:              {angle:.3f}")

    print("=====================================")

    # ============================================================
    # RETURN TO ESTIMATED ISOCENTER
    # ============================================================

    est_isocenter: np.ndarray = np.array([x, y, z])

    print("\n========== MOVE TO ISOCENTER ==========")

    print(f"Estimated isocenter: "
          f"{np.array2string(est_isocenter, precision=3)}")

    # Real implementation:
    # com._position_move(fr5, est_isocenter)

    print(f"Robot moved to isocenter: "
          f"{np.array2string(est_isocenter, precision=3)}")

    print("SIMULATION: Robot would move to estimated isocenter.")

    print("========================================")

    # ============================================================
    # DEFINE DATA TO COLLECT
    # ============================================================

    grav_test_light_data: list = []
    grav_test_position_data: list = []
    grav_test_scan_data: list = []

    print("\n========== INITIALIZE DATA ==========")

    print(f"Light data:     {grav_test_light_data}")
    print(f"Position data:  {grav_test_position_data}")

    print("=====================================")

    # ============================================================
    # DEFINE PATH TO MOVE IN
    # ============================================================

    print("\n========== CREATE RECTANGLE PATH ==========")

    # Define active axes
    grav_test_axes: tuple = ("y", "z")

    print(f"Active axes: {grav_test_axes}")

    # Calculate four rectangle points
    rectangle_points: list = paths.calculate_four_points_trig(
        est_isocenter,
        length,
        width,
        angle,
        grav_test_axes[0],
        grav_test_axes[1]
    )

    print("\nCalculated rectangle points (Matrix):")

    for i in range(len(rectangle_points)):
        print(f"  P{i + 1}: "
              f"{np.array2string(rectangle_points[i], precision=3)}")

    # Create rectangle path
    path: list = paths.rectangle_path(
        est_isocenter,
        rectangle_points,
        step
    )

    print("\nRectangle path created.")

    print("===========================================")

    # ============================================================
    # DISPLAY PATH INFORMATION
    # ============================================================

    print("\n========== PATH INFORMATION ==========")

    for i in range(len(path)):

        movement_path: list = path[i][0]
        scan: bool = path[i][1]

        print(f"\nPath {i + 1}")

        if i == 0:
            print("  From: Isocenter -> P1")
        elif i == 1:
            print("  From: P1 -> P2")
        elif i == 2:
            print("  From: P2 -> P3")
        elif i == 3:
            print("  From: P3 -> P4")

        print(f"  Scan:      {scan}")
        print(f"  Num moves: {len(movement_path)}")

        for j in range(len(movement_path)):
            print(f"    Move {j + 1}: "
                  f"{np.array2string(movement_path[j], precision=3)}")

    print("=====================================")

    # ============================================================
    # MOVE THE ROBOT AND SCAN
    # ============================================================

    print("\n========== EXECUTE PATH ==========")

    print("Beginning path execution...")

    # Current robot position starts at the estimated isocenter
    current_position: np.ndarray = est_isocenter.copy()

    # Real implementation:
    # start_data_recording()
    # move.execute_path(path, grav_test_light_data, grav_test_position_data)
    # end_data_recording()

    # Simulation of execute_path()
    for i in range(len(path)):

        movement_path: list = path[i][0]
        scan: bool = path[i][1]

        print(f"\n--- Executing Path {i + 1} ---")

        if scan:

            print("Action: MOVE + SCAN")

            for j in range(len(movement_path)):

                movement: np.ndarray = movement_path[j]

                # Simulate incremental robot movement
                new_position: np.ndarray = current_position + movement

                print(f"\n  Move {j + 1}")
                print(f"    Movement: "
                      f"{np.array2string(movement, precision=3)}")
                print(f"    From:     "
                      f"{np.array2string(current_position, precision=3)}")
                print(f"    To:       "
                      f"{np.array2string(new_position, precision=3)}")

                # Update current robot position
                current_position = new_position

                # ====================================================
                # SIMULATE LIGHT SENSOR
                # ====================================================

                light_intensity: float = np.random.uniform(0, 1)

                print(f"    Light:    {light_intensity:.3f}")

                # Store light intensity
                grav_test_light_data.append(light_intensity)

                # Store ABSOLUTE robot position
                grav_test_position_data.append(current_position.copy())

                # Store position + light intensity together
                scan_data: tuple = (
                    current_position.copy(),
                    light_intensity
                )

                grav_test_scan_data.append(scan_data)
                print("    Data stored.")

        else:

            print("Action: MOVE ONLY")

            for j in range(len(movement_path)):

                movement: np.ndarray = movement_path[j]

                # Simulate incremental robot movement
                new_position: np.ndarray = current_position + movement

                print(f"\n  Move {j + 1}")
                print(f"    Movement: "
                      f"{np.array2string(movement, precision=3)}")
                print(f"    From:     "
                      f"{np.array2string(current_position, precision=3)}")
                print(f"    To:       "
                      f"{np.array2string(new_position, precision=3)}")

                # Update current robot position
                current_position = new_position

    print("\nPath execution complete.")

    print("===================================")

    # ============================================================
    # DISPLAY COLLECTED DATA
    # ============================================================

    print("\n========== COLLECTED DATA ==========")

    print(f"Number of scans: {len(grav_test_light_data)}")

    print("\nLight data:")

    for i in range(len(grav_test_light_data)):
        print(f"  Scan {i + 1}: "
              f"{grav_test_light_data[i]:.3f}")

    print("\nPosition data:")

    for i in range(len(grav_test_position_data)):
        print(f"  Scan {i + 1}: "
              f"{np.array2string(grav_test_position_data[i], precision=3)}")

    print("====================================")

    # ============================================================
    # DATA PROCESSING
    # ============================================================

    print("\n========== DATA PROCESSING ==========")

    # ------------------------------------------------------------
    # Process light intensity data
    # ------------------------------------------------------------

    mean_light: float = DataProcessing.calculate_mean(
        grav_test_light_data
    )

    max_light: float = DataProcessing.find_max(
        grav_test_light_data
    )

    min_light: float = DataProcessing.find_min(
        grav_test_light_data
    )

    print(f"Mean light intensity: {mean_light:.3f}")
    print(f"Maximum light intensity: {max_light:.3f}")
    print(f"Minimum light intensity: {min_light:.3f}")


    # ------------------------------------------------------------
    # Process scan data
    # ------------------------------------------------------------

    print("\nScan data:")

    for i in range(len(grav_test_scan_data)):

        position: np.ndarray = grav_test_scan_data[i][0]
        light_intensity: float = grav_test_scan_data[i][1]

        print(f"  Scan {i + 1}")
        print(f"    Position: {np.array2string(position, precision=3)}")
        print(f"    Light:   {light_intensity:.3f}")


    # ------------------------------------------------------------
    # Future data processing
    # ------------------------------------------------------------

    # center1 = DataProcessing.get_center_1(grav_test_scan_data)
    # center2 = DataProcessing.get_center_2(grav_test_scan_data)
    # offset = DataProcessing.get_offset(grav_test_scan_data)

    print("====================================")


# SELF-SIMULATION ONLY; FOR MARC'S SUBSYSTEM MEETING AND DOCUMENTATION
def main():

    gravity_test_automated_simulation()


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