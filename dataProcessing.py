import numpy as np

# Half-width (mm along the scan) of the window used for the local line fit around each 50% decrement.
# If the samples are spaced further apart than this (e.g. 1 mm collimator scans) the window only holds
# the two bracketing samples and the fit reduces to plain two-point linear interpolation.
FIT_HALF_WIDTH = 0.75

# Sanity check that a beam is present: (max - min) of the scan must be at least this many times the
# sample-to-sample noise. Gravity beams are a narrow bright spike (>100 in the data so far); the dimmer, wider
# collimator beams come out at about 7-14, so they need a lower threshold.
MIN_SNR = {"gravity": 15.0, "collimator": 6.0, "gantry": 6.0}


def unpack_side(side):
    """side: list of [[x, y, z], d, I]  ->  pos (N, 3) array and intensity (N,) array."""
    pos = np.array([s[0] for s in side], dtype=float)
    intensity = np.array([s[2] for s in side], dtype=float)
    return pos, intensity


def find_test_axis(pos_all):
    """
    Which two of x / y / z does the test occur on
    The gradient of each position column is nonzero only along the axes that actually move;
    two of x / y / z moves between the two scans and the other one stays constant.
    Returns two of: 0 for x, 1 for y, 2 for z
    """
    motion = np.abs(np.gradient(pos_all, axis=0)).sum(axis=0)
    if motion[:3].max() < 1e-6:
        raise RuntimeError("No movement detected")
    min_idx = int(np.argmin(motion[:3]))
    if min_idx == 0:
        return 1,2
    elif min_idx == 1:
        return 0,2
    else:
        return 0,1


def _arc_length(pos):
    """Distance travelled along the scan at each sample (works for scans along any direction)."""
    return np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(pos, axis=0), axis=1))])


def _crossing(pos, s, intensity, a, b, decrement):
    """
    Absolute position [x, y, z] where the intensity crosses the 50% decrement between adjacent samples a and b.
    Local line fit: a straight line is fitted (least squares) through the samples within FIT_HALF_WIDTH of the
    two-point crossing (always including a and b) and solved for the decrement. Falls back to the two-point
    linear interpolation if the window holds only a and b, or if the fit is flat / reversed / lands outside
    the bracket.
    """
    sc = s[a] + (decrement - intensity[a]) / (intensity[b] - intensity[a]) * (s[b] - s[a])
    idx = np.union1d(np.flatnonzero(np.abs(s - sc) <= FIT_HALF_WIDTH), [a, b])
    if idx.size > 2:
        m, c = np.polyfit(s[idx], intensity[idx], 1)
        if np.sign(m) == np.sign(intensity[b] - intensity[a]):
            root = (decrement - c) / m
            if s[a] - FIT_HALF_WIDTH <= root <= s[b] + FIT_HALF_WIDTH:
                sc = root
    return np.array([np.interp(sc, s, pos[:, k]) for k in range(pos.shape[1])])


def _has_beam(intensity, min_snr):
    """
    True if the scan range (max - min) is well above the sample-to-sample noise.
    The noise comes from the differences between neighbouring samples, so it is not thrown off by how much of
    the scan the beam occupies (a wide collimator beam fills most of it).
    """
    noise = 1.4826 * np.median(np.abs(np.diff(intensity))) / np.sqrt(2)
    return intensity.max() - intensity.min() >= min_snr * max(noise, 1e-12)


def _split_index(intensity, test):
    """
    Index at which the scan is split into the half holding the rising edge and the half holding the falling edge.
    gravity            : centroid of the samples at (within 2% of the range of) the maximum. For a saturated
                         sensor that is the middle of the plateau; for an unsaturated peak it is the peak.
    collimator, gantry : the crosshair dip, i.e. the lowest (3-sample smoothed) intensity within the central
                         half of the beam, found between the first and last samples above the overall 50% level.
    """
    lo, hi = intensity.min(), intensity.max()
    if test == "gravity":
        near_max = np.flatnonzero(intensity >= hi - 0.02 * (hi - lo))
        return int(round(near_max.mean()))
    if test in ("collimator", "gantry"):
        above = np.flatnonzero(intensity >= 0.5 * (lo + hi))
        a, b = above[0], above[-1]
        margin = int(round(0.25 * (b - a)))
        lo_i, hi_i = a + margin, b - margin
        if hi_i <= lo_i:
            return int((a + b) // 2)
        smooth = np.convolve(intensity, np.ones(3) / 3, mode="same")
        return lo_i + int(np.argmin(smooth[lo_i:hi_i + 1]))
    raise ValueError("test must be 'gravity', 'collimator' or 'gantry'")


def locate_center(pos, intensity, test="gravity"):
    """
    Beam center [x, y, z] of one scan using the 50% decrement.
    The scan is split in two (see _split_index). In each half the 50% decrement comes from that half's own
    max and min: decrement = (max + min) / 2. The first half gives the rising edge, the second half the falling
    edge, each located by the local line fit in _crossing. The center is the midpoint of the two crossings.
    Returns (center, rise, fall), each an absolute position [x, y, z].
    """
    n = len(intensity)
    if test not in MIN_SNR:
        raise ValueError("test must be 'gravity', 'collimator' or 'gantry'")
    if not _has_beam(intensity, MIN_SNR[test]):
        raise RuntimeError("Beam not found in scan (no clear peak above the noise).")
    s = _arc_length(pos)
    split = _split_index(intensity, test)

    # rising edge: first sample at/above the first half's 50% decrement
    half1 = intensity[:split + 1]
    decrement1 = 0.5 * (half1.max() + half1.min())
    i = np.flatnonzero(half1 >= decrement1)[0]
    if i == 0:
        raise RuntimeError("Scan starts above the 50% decrement")

    # falling edge: last sample at/above the second half's 50% decrement
    half2 = intensity[split:]
    decrement2 = 0.5 * (half2.max() + half2.min())
    j = np.flatnonzero(half2 >= decrement2)[-1] + split
    if j == n - 1:
        raise RuntimeError("Scan ends above the 50% decrement")

    rise = _crossing(pos, s, intensity, i - 1, i, decrement1)
    fall = _crossing(pos, s, intensity, j, j + 1, decrement2)
    return 0.5 * (rise + fall), rise, fall


def calculate_angle(data, test="gravity"):
    """
    data : [side1, side2]
    test : 'gravity', 'collimator' or 'gantry' (selects how each scan is split, see _split_index)
    Returns (theta_deg, [[left50,right50,center],[left50,right50,center]]),
    where each 50% decrement and center is the absolute position [x, y, z]
    """
    pos1, I1 = unpack_side(data[0])
    pos2, I2 = unpack_side(data[1])

    axis1, axis2 = find_test_axis(np.vstack([pos1, pos2]))
    c1, rise1, fall1 = locate_center(pos1, I1, test)
    c2, rise2, fall2 = locate_center(pos2, I2, test)

    theta = np.rad2deg(np.arctan((c1[axis2] - c2[axis2]) / (c1[axis1] - c2[axis1])))
    return theta, ([rise1,fall1,c1],[rise2,fall2,c2])
