
import numpy as np
import AutomatedTests.pathsRemade as paths
#import dataProcessingGravity as dp
#from XRBPlotter import Rx, Ry, Rz

import logging

atl_logger = logging.getLogger('Automated Test Logic Results')
atl_logger.setLevel(logging.INFO-10) # debug, info, warning, critical, error ---> low to high
logging.INFO # 20 is level for info; above is recorded
#atl_logger.propagate = False

# Low to High Levels
#atl_logger.debug('Debug message') # 10
#atl_logger.info('Application started') # 20
#atl_logger.warning('Disk space running low') # 30
#atl_logger.error('Failed to connect to database') # 40
#atl_logger.critical('System shutting down') # 50

def simulate_straight_path_displacement(
    p1: np.ndarray,
    p2: np.ndarray
):
    print("\n========== STRAIGHT PATH DISPLACEMENT ==========")

    path: list = paths.straight_path_displacement(p1, p2)

    print(f"Start:  {p1}")
    print(f"Target: {p2}")
    print(f"Number of movements: {len(path)}")

    current_position: np.ndarray = p1.copy()

    for i, displacement in enumerate(path):
        print(f"\nMove {i + 1}")
        print(f"Displacement: {displacement}")
        print(f"From:         {current_position}")

        current_position = current_position + displacement

        print(f"To:           {current_position}")

    print(f"\nExpected final position: {p2}")
    print(f"Actual final position:   {current_position}")
    print(f"Result: {'SUCCESS' if np.allclose(current_position, p2) else 'ERROR'}")

def simulate_straight_path_absolute(
    start_position: np.ndarray,
    end_position: np.ndarray
):
    print("\n========== STRAIGHT PATH ABSOLUTE ==========")

    path: list = paths.straight_path_absolute(end_position)

    print(f"Start:  {start_position}")
    print(f"Target: {end_position}")

    current_position: np.ndarray = start_position.copy()

    for i, destination in enumerate(path):
        print(f"\nMove {i + 1}")
        print(f"From:        {current_position}")
        print(f"Destination: {destination}")

        # Simulate an absolute move to the destination.
        current_position = destination.copy()

        print(f"To:          {current_position}")

    print(f"\nExpected final position: {end_position}")
    print(f"Actual final position:   {current_position}")
    print(f"Result: {'SUCCESS' if np.allclose(current_position, end_position) else 'ERROR'}")

def simulate_basis_plane(
    isocenter: np.ndarray,
    length: float,
    width: float
):
    print("\n========== BASIS PLANE POINTS ==========")

    points: list = paths.basis_plane_calculate_four_points(
        isocenter,
        length,
        width
    )

    print(f"Isocenter: {isocenter}")
    print(f"Length: {length}")
    print(f"Width:  {width}")

    for i, point in enumerate(points):
        print(f"P{i + 1}: {point}")

    calculated_center: np.ndarray = (points[0] + points[2]) / 2.0

    print(f"\nExpected center:   {isocenter}")
    print(f"Calculated center: {calculated_center}")
    print(f"Result: {'SUCCESS' if np.allclose(calculated_center, isocenter) else 'ERROR'}")

def simulate_rectangle_path(
    isocenter: np.ndarray,
    points: list
):
    print("\n========== RECTANGLE PATH ==========")

    rectangle_paths: list = paths.rectangle_path(isocenter, points)

    current_position: np.ndarray = isocenter.copy()

    for i, path_entry in enumerate(rectangle_paths):
        movement_path: list = path_entry[0]
        scan: bool = path_entry[1]
        start_position: np.ndarray = path_entry[2]

        print(f"\nPath {i + 1}")
        print(f"Scan enabled: {scan}")
        print(f"Starting position: {start_position}")

        if scan:
            # Entries are displacement vectors.
            for displacement in movement_path:
                print(f"Displacement: {displacement}")
                current_position = current_position + displacement
                print(f"New position: {current_position}")
        else:
            # Entries are absolute destination positions.
            for destination in movement_path:
                print(f"Destination: {destination}")
                current_position = destination.copy()
                print(f"New position: {current_position}")

    print("\nRectangle path simulation complete.")

def simulate_rotate_basis_plane(
    isocenter: np.ndarray,
    points: list,
    axis: str,
    angle: float,
    offset: float = 0.0
):
    print("\n========== ROTATE BASIS PLANE ==========")

    rotation_matrix: np.ndarray = paths.get_rotation_matrix(
        axis,
        angle,
        offset
    )

    rotated_points: list = paths.rotate_basis_plane_points(
        isocenter,
        points,
        rotation_matrix
    )

    print(f"Axis:   {axis}")
    print(f"Angle:  {angle}")
    print(f"Offset: {offset}")
    print(f"\nRotation matrix:\n{rotation_matrix}")

    print("\nOriginal points:")
    for i, point in enumerate(points):
        print(f"P{i + 1}: {point}")

    print("\nRotated points:")
    for i, point in enumerate(rotated_points):
        print(f"P{i + 1}: {point}")

    original_center: np.ndarray = (points[0] + points[2]) / 2.0
    rotated_center: np.ndarray = (
        rotated_points[0] + rotated_points[2]
    ) / 2.0

    print(f"\nExpected center:   {isocenter}")
    print(f"Calculated center: {rotated_center}")
    print(f"Result: {'SUCCESS' if np.allclose(rotated_center, isocenter) else 'ERROR'}")

def simulate_gravity_test(
    isocenter: np.ndarray,
    side: str,
    length: float,
    width: float,
    step_length: float,
    Navg: int
):
    print("\n========== GRAVITY TEST SIMULATION ==========")

    print(f"Isocenter:  {isocenter}")
    print(f"Side:       {side}")
    print(f"Length:     {length}")
    print(f"Width:      {width}")
    print(f"Step:       {step_length}")
    print(f"Navg:       {Navg}")

    # Create the base rectangle.
    points: list = paths.basis_plane_calculate_four_points(
        isocenter,
        length,
        width
    )

    # Rotate the rectangle according to the selected side.
    if side == "left":
        angle: float = 90.0
    elif side == "right":
        angle = -90.0
    elif side == "front":
        angle = 0.0
    else:
        raise ValueError("side must be 'left', 'right', or 'front'.")

    if angle != 0:
        rotation_matrix: np.ndarray = paths.get_rotation_matrix(
            "z", angle
        )

        points = paths.rotate_basis_plane_points(
            isocenter,
            points,
            rotation_matrix
        )

    # Build the movement path.
    rectangle_paths: list = paths.rectangle_path(isocenter, points)

    print("\nGenerated rectangle points:")
    for i, point in enumerate(points):
        print(f"P{i + 1}: {point}")

    print("\nGenerated movement paths:")
    for i, (movement_path, scan, start_position) in enumerate(rectangle_paths):
        print(f"Path {i + 1}: scan={scan}, entries={len(movement_path)}")

    print("\nSimulated execution:")
    current_position: np.ndarray = isocenter.copy()
    scan_data: list = []

    for i, (movement_path, scan, start_position) in enumerate(rectangle_paths):
        print(f"\nPath {i + 1}")

        if scan:
            for displacement in movement_path:
                magnitude: float = np.linalg.norm(displacement)

                if magnitude == 0:
                    continue

                n_steps: int = int(np.ceil(magnitude / step_length))
                movement_vector: np.ndarray = displacement / n_steps

                for _ in range(n_steps):
                    current_position = current_position + movement_vector

                    # Placeholder sensor value for simulation only.
                    light_intensity: float = float(np.random.uniform(0, 1))

                    scan_data.append(
                        (current_position.copy(), light_intensity)
                    )

                    print(f"  Position: {current_position}, Light: {light_intensity:.3f}")
        else:
            for destination in movement_path:
                current_position = destination.copy()
                print(f"  Absolute destination: {current_position}")

    print(f"\nTotal simulated scans: {len(scan_data)}")
    #print("No physical robot or real sensor was used.")
    
    #dr_offset: float
    #dr_offset = dp.calculate_gravity_angle(scan_data[0], scan_data[1])
    #print(f"\nOffset Angle Calculated: {dr_offset}")
    # Giving: 
        # scan_data[0] = [(x1,y1,z1), (x2,y2,z3), ...] # List of np.ndarray
        # scan_data[1] = [l1, l2, l3, ...] # List of floats
    

def main():

    # ============================================================
    # SHARED PARAMETERS
    # ============================================================

    p1: np.ndarray = np.array([10.0, 20.0, 30.0])
    p2: np.ndarray = np.array([20.0, 40.0, 60.0])

    isocenter: np.ndarray = np.array([0.0, 0.0, 0.0])
    length: float = 10.0
    width: float = 5.0

    axis: str = "z"
    angle: float = 0.0
    offset: float = 0.0

    side: str = "front"
    step_length: float = 2.5
    Navg: int = 4

    # ============================================================
    # RUN INDIVIDUAL FUNCTION SIMULATIONS
    # ============================================================

    #simulate_straight_path_displacement(p1, p2)
    #simulate_straight_path_absolute(p1, p2)
    #simulate_basis_plane(isocenter, length, width)

    #points: list = paths.basis_plane_calculate_four_points(isocenter, length, width)
    #simulate_rectangle_path(isocenter, points)
    #simulate_rotate_basis_plane(isocenter, points, axis, angle, offset)

    # ============================================================
    # RUN FULL GRAVITY SIMULATION
    # ============================================================
    #simulate_gravity_test(isocenter, side, length, width, step_length, Navg)
    
    atl_logger.debug('Debug message') # 10
    atl_logger.info('Application started') # 20
    atl_logger.warning('Disk space running low') # 30
    atl_logger.error('Failed to connect to database') # 40
    atl_logger.critical('System shutting down') # 50
  


if __name__ == "__main__":
    main()
