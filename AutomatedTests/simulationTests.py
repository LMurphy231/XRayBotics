import numpy as np
import RobotCommunicator as com

import pathsRemade as paths

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
        print(f"  Movement: {movement}")
        print(f"  From:     {current_position}")
        print(f"  To:       {new_position}")

        current_position = new_position

    print("\nFinal position:")
    print(f"  Expected: {p2}")
    print(f"  Actual:   {current_position}")

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
        print(f"  Movement: {movement}")
        print(f"  From:     {current_position}")
        print(f"  To:       {new_position}")

        current_position = new_position

    print("\nFinal position:")
    print(f"  Expected: {p2}")
    print(f"  Actual:   {current_position}")

    if np.allclose(current_position, p2):
        print("  Result:   SUCCESS")
    else:
        print("  Result:   ERROR")

    print("\n============================================")


# SELF-SIMULATION ONLY; FOR MARC'S SUBSYSTEM MEETING AND DOCUMENTATION
def main():

    straight_path_simulation()


if __name__ == "__main__":
    main()