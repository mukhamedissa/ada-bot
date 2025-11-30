def lerp(start: float, end: float, t: float) -> float:
    return start + (end - start) * t

def ease_in_out(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)
