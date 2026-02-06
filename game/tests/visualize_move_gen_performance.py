import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from matplotlib.ticker import MaxNLocator
from scipy.interpolate import PchipInterpolator

# --- CONFIG ---
JSON_FILE = "perft_results.json"
DARK_BG = True
ANIMATION_INTERVAL = 50
TESTS_TO_PLOT = None

AXIS_ALPHA = 0.4

# Camera tuning
ZOOM_X_RANGE = 2.0
ZOOM_Y_FACTOR = 1.6

ZOOM_OUT_SMOOTHING = 0.08
ZOOM_IN_SMOOTHING = 0.15

PRE_ZOOM_OUT_PAUSE_SECONDS = 1.0
PRE_ZOOM_OUT_FRAMES = int(PRE_ZOOM_OUT_PAUSE_SECONDS * 1000 / ANIMATION_INTERVAL)

PAUSE_SECONDS = 1.5
PAUSE_FRAMES = int(PAUSE_SECONDS * 1000 / ANIMATION_INTERVAL)


def load_tests(json_file, test_ids=None):
    with open(json_file, "r") as f:
        data = json.load(f)
    if not data:
        raise ValueError("No tests found in JSON file.")
    if test_ids is None:
        return data
    return [t for t in data if t["test_id"] in test_ids]


def animate_tests_head_with_labels(tests):
    if DARK_BG:
        plt.style.use("dark_background")

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlabel("Depth", fontsize=12)
    ax.set_ylabel("Time (s)", fontsize=12)
    ax.set_title("Perft Depth vs Time (Cinematic Camera)", fontsize=14)

    # Axis style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_alpha(AXIS_ALPHA)
    ax.spines['bottom'].set_alpha(AXIS_ALPHA)
    ax.tick_params(axis='x', colors='gray')
    ax.tick_params(axis='y', colors='gray')

    colors = plt.cm.tab10.colors
    lines, markers, labels = [], [], []
    smooth_data = []

    max_depth = max(d["depth"] for t in tests for d in t["depths"])
    global_max_y = 0

    for idx, test in enumerate(tests):
        depths = np.array([d["depth"] for d in test["depths"]])
        times = np.array([d["time_seconds"] for d in test["depths"]])

        interp = PchipInterpolator(depths, times)
        x = np.linspace(depths.min(), depths.max(), 200)
        y = interp(x)

        line, = ax.plot([], [], color=colors[idx % len(colors)], linewidth=2)
        marker, = ax.plot([], [], 'o', color=colors[idx % len(colors)], markersize=6)

        label = ax.text(
            0, 0, test["test_name"],
            color=colors[idx % len(colors)],
            fontsize=10,
            weight="bold",
            va="bottom",
            ha="left",
            alpha=0.85,
            visible=False
        )

        lines.append(line)
        markers.append(marker)
        labels.append(label)

        smooth_data.append({
            "x": x,
            "y": y,
            "current_idx": -1
        })

    frames_per_test = [len(d["x"]) for d in smooth_data]

    # Camera state
    cam_xmin, cam_xmax = 1, max_depth
    cam_ymin, cam_ymax = 0, smooth_data[0]["y"][0] * ZOOM_Y_FACTOR

    def lerp(a, b, t):
        return a + (b - a) * t

    phase = "FOLLOW"
    pause_counter = 0
    pre_zoom_pause = 0
    test_index = 0
    frame_in_test = 0

    def update(_):
        nonlocal cam_xmin, cam_xmax, cam_ymin, cam_ymax
        nonlocal phase, pause_counter, pre_zoom_pause
        nonlocal test_index, frame_in_test, global_max_y

        # ---------------- FOLLOW ----------------
        if phase == "FOLLOW":
            data = smooth_data[test_index]
            i = frame_in_test
            data["current_idx"] = i

            xh = data["x"][i]
            yh = data["y"][i]

            global_max_y = max(global_max_y, yh)

            lines[test_index].set_data(data["x"][:i + 1], data["y"][:i + 1])
            markers[test_index].set_data([xh], [yh])

            labels[test_index].set_visible(True)
            labels[test_index].set_position((xh + 0.05, yh + 0.05 * yh))

            txmin = max(1, xh - ZOOM_X_RANGE / 2)
            txmax = min(max_depth + 0.5, xh + ZOOM_X_RANGE / 2)
            tymin = 0
            tymax = yh * ZOOM_Y_FACTOR

            cam_xmin = lerp(cam_xmin, txmin, ZOOM_IN_SMOOTHING)
            cam_xmax = lerp(cam_xmax, txmax, ZOOM_IN_SMOOTHING)
            cam_ymin = lerp(cam_ymin, tymin, ZOOM_IN_SMOOTHING)
            cam_ymax = lerp(cam_ymax, tymax, ZOOM_IN_SMOOTHING)

            frame_in_test += 1

            if frame_in_test >= frames_per_test[test_index]:
                phase = "PRE_ZOOM_OUT"
                pre_zoom_pause = 0
                frame_in_test = frames_per_test[test_index] - 1

        # ---------------- HOLD BEFORE ZOOM OUT ----------------
        elif phase == "PRE_ZOOM_OUT":
            pre_zoom_pause += 1
            if pre_zoom_pause >= PRE_ZOOM_OUT_FRAMES:
                phase = "ZOOM_OUT"

        # ---------------- ZOOM OUT ----------------
        elif phase == "ZOOM_OUT":
            txmin, txmax = 1, max_depth + 0.5
            tymin, tymax = 0, global_max_y * 1.15

            cam_xmin = lerp(cam_xmin, txmin, ZOOM_OUT_SMOOTHING)
            cam_xmax = lerp(cam_xmax, txmax, ZOOM_OUT_SMOOTHING)
            cam_ymin = lerp(cam_ymin, tymin, ZOOM_OUT_SMOOTHING)
            cam_ymax = lerp(cam_ymax, tymax, ZOOM_OUT_SMOOTHING)

            if abs(cam_xmin - txmin) < 0.01:
                phase = "PAUSE"
                pause_counter = 0

        # ---------------- PAUSE ----------------
        elif phase == "PAUSE":
            pause_counter += 1
            if pause_counter >= PAUSE_FRAMES:
                test_index += 1
                if test_index >= len(smooth_data):
                    return lines + markers + labels
                frame_in_test = 0
                phase = "ZOOM_IN"

        # ---------------- ZOOM IN ----------------
        elif phase == "ZOOM_IN":
            data = smooth_data[test_index]
            xh = data["x"][0]
            yh = data["y"][0]

            txmin = max(1, xh - ZOOM_X_RANGE / 2)
            txmax = min(max_depth + 0.5, xh + ZOOM_X_RANGE / 2)
            tymin = 0
            tymax = yh * ZOOM_Y_FACTOR

            cam_xmin = lerp(cam_xmin, txmin, ZOOM_IN_SMOOTHING)
            cam_xmax = lerp(cam_xmax, txmax, ZOOM_IN_SMOOTHING)
            cam_ymin = lerp(cam_ymin, tymin, ZOOM_IN_SMOOTHING)
            cam_ymax = lerp(cam_ymax, tymax, ZOOM_IN_SMOOTHING)

            if abs(cam_xmin - txmin) < 0.01:
                phase = "FOLLOW"

        ax.set_xlim(cam_xmin, cam_xmax)
        ax.set_ylim(cam_ymin, cam_ymax)

        return lines + markers + labels

    ani = animation.FuncAnimation(
        fig,
        update,
        interval=ANIMATION_INTERVAL,
        blit=False,
        repeat=False
    )

    plt.show()


if __name__ == "__main__":
    tests = load_tests(JSON_FILE, TESTS_TO_PLOT)
    animate_tests_head_with_labels(tests)
