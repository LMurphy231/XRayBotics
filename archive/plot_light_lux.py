import sys

import matplotlib.pyplot as plt
from labquest import LabQuest

RATE_HZ = 5000
PERIOD_MS = 0.2
CHUNK = 1000


def crossing(x1, y1, x2, y2, level):
    if y1 == y2:
        return x1
    return x1 + (level - y1) * (x2 - x1) / (y2 - y1)


def main():
    
    count = int(5 * RATE_HZ)
    lq = LabQuest()
    
    
    print(lq.open())
    lq.select_sensors(ch1="lq_sensor")
    lq.start(period=PERIOD_MS)
    lux = []
    started = False
    while count > 0:
        n = min(CHUNK, count)
        part = lq.read_multi_pt("ch1", n)
        print(part[0])
        if not started:
            print("measurement start")
            started = True
        lux.extend(part)
        count -= n
    print("measurement end")
    times = [i / RATE_HZ for i in range(len(lux))]

    lq.stop()
    lq.close()

    threshold = (max(lux) + min(lux)) / 2
    peak = lux.index(max(lux))
    left_edge = None
    right_edge = None

    for i in range(peak, 0, -1):
        if (lux[i - 1] - threshold) * (lux[i] - threshold) <= 0:
            left_edge = crossing(times[i - 1], lux[i - 1], times[i], lux[i], threshold)
            break

    for i in range(peak, len(lux) - 1):
        if (lux[i] - threshold) * (lux[i + 1] - threshold) <= 0:
            right_edge = crossing(times[i], lux[i], times[i + 1], lux[i + 1], threshold)
            break

    if left_edge is None or right_edge is None:
        raise RuntimeError("No two threshold crossings found.")

    center = (left_edge + right_edge) / 2

    print("threshold =", threshold)
    print("center =", center)

    plt.plot(times, lux)
    plt.axhline(threshold, color="g", linestyle="--")
    plt.axvline(center, color="k")
    plt.xlabel("Time (s)")
    plt.ylabel("Lux")
    plt.show()


if __name__ == "__main__":
    main()
