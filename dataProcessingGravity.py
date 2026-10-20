"""
The arm will scan discrete steps every 0.5mm. 

The gravity test will be performed twice; once in the XZ plane and once in the YZ plane

It follows a set path:

XZ plane, Y constant, start at (0, 0):
  1. diagonal move up to (+W/2, +L/2)
  2. vertical scan DOWN  to (+W/2, -L/2)   <- used
  3. horizontal move LEFT to (-W/2, -L/2)
  4. vertical scan UP    to (-W/2, +L/2)   <- used

The laser is a horizontal line in the world frame. If the arm's Z axis is tilted
by theta from gravity (rotation about Y), the laser appears in the arm frame as a
line with slope tan(theta):

    z_arm_crossing(x_arm) = (z0 + x_arm*sin(theta)) / cos(theta)

so the two vertical scans see the beam at different heights:

    tan(theta) = (z_cross_down - z_cross_up) / (x_down - x_up)

Sign convention: theta > 0 means the beam appears to rise toward +X in the arm
frame 

The same idea applies in the YZ plane

The Data Processing Subsystem will receive Intensity and Position data for the entire scan
It will segment the Intensity data into 4, with each piece corresponding to a scan
It will utilize the vertical scans and determine theta
"""
import numpy as np
import matplotlib.pyplot as plt

def simulate_position(W,L,step):
    """
    Generate some 2D position data
    This can either be (X,Z) or (Y,Z) data, it's the same
    Define the W or L in cm. Then, return position data with points every 0.5mm
    """
    W_mm = W*10
    L_mm = L*10
    breakpoints = np.array([
            [0.0, 0.0],
            [W_mm / 2, L_mm / 2],     # diagonal up
            [W_mm / 2, -L_mm / 2],    # vertical down
            [-W_mm / 2, -L_mm / 2],   # horizontal left
            [-W_mm / 2, L_mm / 2],    # vertical up
        ])
    # step = 0.25; #mm
    position = []

    all_points = []

    for i in range(len(breakpoints) - 1):
        p1 = breakpoints[i]
        p2 = breakpoints[i+1]
        
        vector = p2 - p1
        distance = np.linalg.norm(vector)
        
        if distance == 0:
            continue
            
        direction = vector / distance
        
        distances = np.arange(0, distance, step)
        
        segment_points = p1 + distances[:, np.newaxis] * direction
        all_points.append(segment_points)

    all_points.append([breakpoints[-1]])
    position = np.vstack(all_points)

    return position

def beam_profile(dz, sigma):
    """Non-ideal impulse: narrow Gaussian core plus a broader, weaker tail (peak ~1)."""
    return (0.85 * np.exp(-0.5 * (dz / sigma) ** 2)
            + 0.15 * np.exp(-0.5 * (dz / (3 * sigma)) ** 2))

def simulate_intensity(position, tilt_deg, beam_z0=3.0, beam_sigma=1.0,
                       amp=1.0, baseline=0.02, noise_sd=0.02, rng=None):
    """
    Intensity sample for each row of 'position' ([x, z] in mm, arm frame).

    tilt_deg : misalignment of the arm's Z axis from gravity (rotation about Y)
    beam_z0  : beam height in the world frame (mm), relative to the start point
    beam_sigma : beam width (mm) along world z
    noise_sd : additive Gaussian noise (same units as amp)

    The beam is horizontal in the world frame, so the sensor sees it at
        z_world = -x*sin(theta) + z*cos(theta)
    and intensity depends only on z_world - beam_z0.
    """
    rng = np.random.default_rng() if rng is None else rng
    th = np.deg2rad(tilt_deg)
    x, z = position[:, 0], position[:, 1]
    z_world = -x * np.sin(th) + z * np.cos(th)

    intensity = amp * beam_profile(z_world - beam_z0, beam_sigma)
    intensity += baseline + rng.normal(0.0, noise_sd, len(position))
    return intensity,tilt_deg

def segment_scans(position):
    """
    Extract vertical scans taking the gradient of the position data
    Return indices of where the two vertical scans of interest occur
    """
    vx = np.gradient(position[:,0])
    vz = np.gradient(position[:,1])

    speed = np.hypot(vx, vz)
    v_nom = np.percentile(speed, 90)

    # Logical indexing to obtain vertical portions
    vertical = (np.abs(vx) < 0.1 * v_nom) & (np.abs(vz) > 0.8 * v_nom)
    up = vertical & (vz > 0)
    down = vertical & (vz < 0)
    # print(up)
    # print(down)
    # print(position[down])
    return up,down

def locate_peak(intensity, up, down, min_snr=8.0):
    """
    Find the beam peak along each of the two vertical scans.
    Returns (peak_idx_up, peak_idx_down): indices into the full
    position/intensity arrays, in the same order as segment_scans.
    """
    # print(intensity[up])
    peaks = []
    for mask in (up, down):
        scan_idx = np.flatnonzero(mask)      # full-array indices of this scan
        y = intensity[scan_idx]
        y = y - np.median(y)                 # baseline from this scan only
        noise = 1.4826 * np.median(np.abs(y))
        if y.max() < min_snr * max(noise, 1e-12):
            raise RuntimeError("Peak not found in scan")
        above = y >= 0.5 * y.max()
        if above[0] or above[-1]:
            raise RuntimeError("Peak touches the scan edge; lengthen the vertical scan.")
        # intensity-weighted centroid of the above-half-max samples, as a full-array index
        # centroid = np.sum(scan_idx[above] * y[above]) / np.sum(y[above])
        # peaks.append(int(round(centroid)))
        peaks.append(scan_idx[np.argmax(intensity[mask])])
    return tuple(peaks)

# given: two arrays: position and intensity which contain both of the vertical scans
def calculate_gravity_angle(position,intensity):
    """
    Calculate gravity angle, return it and the peak indices for plotting
    """
    up, down = segment_scans(position)
    peaks = locate_peak(intensity, up, down)
    z_up, z_down = position[peaks[0], 1], position[peaks[1], 1]
    x_up, x_down = position[peaks[0], 0], position[peaks[1], 0]
    theta = np.rad2deg(np.arctan((z_down - z_up) / (x_down - x_up)))
    return theta, peaks



W = 10
L = 10
experimental = np.zeros(10)
actual = np.zeros(10)
# for angle in range(1,16):
#     position = simulate_position(W,L,0.5)
#     intensity,tilt_deg = simulate_intensity(position,angle/10)
#     theta, peaks = calculate_gravity_angle(position,intensity)
#     experimental[angle]=theta
#     actual[angle]=angle/10
trials = [0.1000,0.1500,0.2000,0.2500,0.3000,0.3500,0.4000,0.4500,0.5000]
i = 0
for step in trials:
    position = simulate_position(W,L,step)
    intensity,tilt_deg = simulate_intensity(position,0.1)
    theta, peaks = calculate_gravity_angle(position,intensity)
    experimental[i]=theta
    actual[i]=0.1
    i=i+1

pct_error = np.abs((actual - experimental) / actual) * 100
print(experimental)
print(actual)
print(pct_error)

# plt.figure(figsize=(8,6))
# plt.scatter(np.arange(len(intensity)),intensity,s=4)
# plt.title('Generated Light Intensity for Self Leveling Laser')
# plt.xlabel('Sample Number (1 = 0.5mm)')
# plt.ylabel('Intensity')

# plt.scatter(peaks[0],intensity[peaks[0]],s=4, color='orange',label='Max Intensity Scanning Down')
# plt.scatter(peaks[1],intensity[peaks[1]],s=4, color='red',label='Max Intensity Scanning Up')

# plt.figure(figsize=(12, 6))
# plt.scatter(position[:, 0], position[:, 1], 
#             color='royalblue', s=4, label='Generated Points (0.5mm steps)')
# plt.title(f"Generated Scan Path with 0.5 mm Increments, Angle Offset: {tilt_deg}, Measured Angle Offset: {theta}")
# plt.xlabel('X Position (mm)')
# plt.ylabel('Z Position (mm)')
# plt.grid(True, which='both', linestyle=':', alpha=0.6)
# plt.axis('equal')  # Ensures 1cm on X-axis equals 1cm on Y-axis

# plt.scatter(position[peaks[0],0],position[peaks[0],1],color='red',label='Position of Max Intensity Scanning Up')
# plt.scatter(position[peaks[1],0],position[peaks[1],1],color='orange',label='Position of Max Intensity Scanning Down')

# plt.legend()
# plt.show()