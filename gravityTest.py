"""
Gravity-angle processing for real scan data.

Input (pre-segmented, one entry per vertical scan):
    data = [side1, side2]
    side = [ [[x, y, z], d, I], ... ]        # d (displacement) is ignored

The laser is horizontal in the world frame, so if the arm's Z axis is tilted by theta from
gravity, the beam appears at a different height in the two vertical scans:

    tan(theta) = (z_beam_1 - z_beam_2) / (h_1 - h_2)

where h is the horizontal coordinate of the test plane (x for the XZ test, y for the YZ test).
Positive theta means the beam appears to rise toward +h in the arm frame.

The beam centre of each scan comes from the 50% method, which works on a saturated sensor:
the scan is split in half, the rising edge (first half) and falling edge (second half) are each
located where the intensity crosses the 50% level, by linear interpolation between the two
samples that straddle it, and the centre is the midpoint of the two crossings.
"""
import numpy as np

def unpack_side(side):
    """side: list of [[x, y, z], d, I]  ->  pos (N, 3) array and intensity (N,) array."""
    pos = np.array([s[0] for s in side], dtype=float)
    intensity = np.array([s[2] for s in side], dtype=float)
    return pos, intensity


def find_horizontal_axis(pos_all):
    """
    Which of x / y is the horizontal axis of the test plane (z is always vertical).
    The gradient of each position column is nonzero only along the axes that actually move;
    x or y moves between the two scans and the other one stays constant.
    Returns 0 for the XZ test, 1 for the YZ test.
    """
    motion = np.abs(np.gradient(pos_all, axis=0)).sum(axis=0)
    if motion[:2].max() < 1e-6:
        raise RuntimeError("No horizontal separation between the two scans in x or y.")
    return int(np.argmax(motion[:2]))


def _crossing(pos, intensity, a, b, level):
    """Position where the intensity crosses `level`, interpolated between samples a and b."""
    t = (level - intensity[a]) / (intensity[b] - intensity[a])
    return pos[a] + t * (pos[b] - pos[a])


def locate_center(pos, intensity):
    """
    Beam centre [x, y, z] of one vertical scan using the 50% method.
    level = min + (max - min) / 2
    """
    n = len(intensity)
    lo, hi = intensity.min(), intensity.max()
    med = np.median(intensity)
    noise = 1.4826 * np.median(np.abs(intensity - med))
    if hi - med < 8 * max(noise, 1e-12):
        raise RuntimeError("Beam not found in scan (no clear peak above the noise).")

    level = lo + 0.5 * (hi - lo)
    above = intensity >= level
    half = n // 2

    # rising edge: first sample at/above the level in the first half
    first = np.flatnonzero(above[:half])
    if first.size == 0:
        raise RuntimeError("No rising edge in the first half of the scan; beam not centred in scan.")
    i = first[0]
    if i == 0:
        raise RuntimeError("Scan starts above the 50% level; lengthen the scan.")

    # falling edge: last sample at/above the level in the second half
    last = np.flatnonzero(above[half:])
    if last.size == 0:
        raise RuntimeError("No falling edge in the second half of the scan; beam not centred in scan.")
    j = last[-1] + half
    if j == n - 1:
        raise RuntimeError("Scan ends above the 50% level; lengthen the scan.")

    rise = _crossing(pos, intensity, i - 1, i, level)
    fall = _crossing(pos, intensity, j, j + 1, level)
    return 0.5 * (rise + fall)


def calculate_gravity_angle(data):
    """
    data : [side1, side2] as described at the top of the file.
    Returns (theta_deg, center1, center2), where each center is the absolute [x, y, z]
    of the beam centre in that scan.
    """
    pos1, I1 = unpack_side(data[0])
    pos2, I2 = unpack_side(data[1])

    axis = find_horizontal_axis(np.vstack([pos1, pos2]))
    c1 = locate_center(pos1, I1)
    c2 = locate_center(pos2, I2)

    theta = np.rad2deg(np.arctan((c1[2] - c2[2]) / (c1[axis] - c2[axis])))
    return theta, c1, c2