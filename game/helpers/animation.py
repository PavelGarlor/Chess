
class Animation:

    def __init__(self):
        pass


def animate_to_pos(start, end, elapsed, duration):
    if elapsed >= duration:
        return end

    t = max(0.0, min(elapsed / duration, 1.0))

    # ease-out
    t = 1 - (1 - t) ** 3

    x = start[0] + (end[0] - start[0]) * t
    y = start[1] + (end[1] - start[1]) * t

    return x, y



def ease_out_cubic(t):
    return 1 - (1 - t) ** 3
