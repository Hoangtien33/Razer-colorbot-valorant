import numpy as np
from driver import RZCONTROL
from logger import logger

# Color detection conditions
color_conditions = {
    'yellow': lambda r, g, b, t: np.all([r >= 250 - t, r <= 255 + t,
                                         g >= 250 - t, g <= 255 + t,
                                         b >= 27 - t,  b <= 104 + t], axis=0),
    'red': lambda r, g, b, t: np.any([np.all([r >= 180 - t, r <= 255 + t,
                                              b >= 30 - t,  b <= 150 + t], axis=0),
                                      np.all([r >= 180 - t, r <= 255 + t,
                                              b >= 30 - t,  b <= 120 + t], axis=0)], axis=0),
    'purple': lambda r, g, b, t: np.all([
        abs(r - b) <= 30 + t,
        r - g >= 60 - t,
        b - g >= 60 - t,
        r >= 140 - t,
        b >= 170 - t,
        g < b
    ], axis=0)
}

def process_frame(frame, color, tol):
    r, g, b = frame[:, :, 2], frame[:, :, 1], frame[:, :, 0]
    if color not in color_conditions:
        raise ValueError(f"Unsupported color: {color}")
    return color_conditions[color](r, g, b, tol)

def aimbot_logic(frame, driver: RZCONTROL, cfg: dict):
    tolerance = int(cfg.get('tolerance', 0))
    fov = int(cfg.get('fov', 50))
    smoothing = max(int(cfg.get('smoothing', 1)), 1)
    speed = float(cfg.get('speed', 0.1)) * max(0.1, float(cfg.get('sensitivity', 1)) - 2)
    offsetX = int(cfg.get('offsetX', 0))
    offsetY = int(cfg.get('offsetY', 0))
    color = cfg.get('color_to_track', 'purple')

    h, w = frame.shape[:2]
    x1, y1 = w // 2 - fov // 2, h // 2 - fov // 2
    x2, y2 = w // 2 + fov // 2, h // 2 + fov // 2
    frame_crop = frame[y1:y2, x1:x2]

    if frame_crop.size == 0:
        return

    mask = process_frame(frame_crop, color, tolerance)
    if not np.any(mask):
        return

    coords = np.where(mask)
    if coords[0].size == 0:
        return

    mean_yx = np.mean([coords[1], coords[0]], axis=1).astype(int)
    center = np.array([w // 2, h // 2])
    offset = np.array([offsetX, offsetY])
    diff = mean_yx[::-1] + offset - center

    dx, dy = diff[0] / smoothing * speed, diff[1] / smoothing * speed
    driver.mouse_move(dx, dy, speed, True)
    logger.debug(f"Aim moved to Δx={dx:.2f}, Δy={dy:.2f}")
