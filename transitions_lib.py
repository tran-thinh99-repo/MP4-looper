import cv2
import numpy as np

# TRANSITION FUNCTIONS
def fade(seq, reverse=False):
    result = []
    for i, f in enumerate(seq):
        alpha = i / (len(seq)-1)
        blended = (
            cv2.addWeighted(f, 1 - alpha, np.zeros_like(f), alpha, 0)
            if reverse else
            cv2.addWeighted(np.zeros_like(f), 1 - alpha, f, alpha, 0)
        )
        result.append(blended)
    return result

def slide(seq, direction="left", reverse=False):
    height, width = seq[0].shape[:2]
    result = []
    for i, f in enumerate(seq):
        alpha = i / (len(seq) - 1)
        shift = int(width * (1 - alpha)) if not reverse else int(width * alpha)
        canvas = np.zeros_like(f)
        if direction == "left":
            x_src = 0 if reverse else shift
            x_dst = shift if reverse else 0
            w = width - shift
        elif direction == "right":
            x_src = shift if reverse else 0
            x_dst = 0 if reverse else shift
            w = width - shift
        if w > 0:
            canvas[:, x_dst:x_dst + w] = f[:, x_src:x_src + w]
        result.append(canvas)
    return result

def zoom(seq, intro=True):
    height, width = seq[0].shape[:2]
    result = []
    for i, f in enumerate(seq):
        alpha = i / (len(seq)-1)
        if not intro:
            alpha = 1 - alpha
        scale = 0.01 + 0.99 * alpha
        resized = cv2.resize(f, None, fx=scale, fy=scale)
        canvas = np.zeros_like(f)
        x = (width - resized.shape[1]) // 2
        y = (height - resized.shape[0]) // 2
        canvas[y:y+resized.shape[0], x:x+resized.shape[1]] = resized
        result.append(canvas)
    return result

def wipe(seq, direction="down", reverse=False):
    height, width = seq[0].shape[:2]
    result = []
    for i, f in enumerate(seq):
        offset = int(height * (i / (len(seq)-1)))
        if reverse:
            offset = height - offset
        canvas = np.zeros_like(f)
        if direction == "down":
            canvas[:offset, :] = f[:offset, :]
        elif direction == "up":
            canvas[height-offset:, :] = f[height-offset:, :]
        result.append(canvas)
    return result

def blinds(seq, reverse=False):
    height, width = seq[0].shape[:2]
    result = []
    strips = 10
    for i, f in enumerate(seq):
        alpha = i / (len(seq)-1)
        if reverse: alpha = 1 - alpha
        canvas = np.zeros_like(f)
        for s in range(strips):
            y0 = int((s / strips) * height)
            y1 = int(((s + 1) / strips) * height)
            block_h = y1 - y0
            h = int(block_h * alpha)
            canvas[y0:y0+h, :] = f[y0:y0+h, :]
        result.append(canvas)
    return result

def pixelate(seq, reverse=False):
    height, width = seq[0].shape[:2]
    result = []
    for i, f in enumerate(seq):
        alpha = i / (len(seq)-1)
        if reverse: alpha = 1 - alpha
        block_size = int(40 * (1 - alpha) + 1)
        small = cv2.resize(f, (width//block_size, height//block_size))
        pixelated = cv2.resize(small, (width, height), interpolation=cv2.INTER_NEAREST)
        result.append(pixelated)
    return result

def dissolve(seq, reverse=False):
    height, width = seq[0].shape[:2]
    result = []
    for i, f in enumerate(seq):
        alpha = i / (len(seq)-1)
        if reverse: alpha = 1 - alpha
        noise = (np.random.rand(height, width) < alpha).astype(np.uint8)
        mask = np.stack([noise]*3, axis=2)
        result.append((f * mask).astype(np.uint8))
    return result

def expand_line(seq, reverse=False):
    height, width = seq[0].shape[:2]
    result = []
    for i, f in enumerate(seq):
        alpha = i / (len(seq)-1)
        if reverse: alpha = 1 - alpha
        half_h = int((height * alpha) // 2)
        center = height // 2
        canvas = np.zeros_like(f)
        canvas[center - half_h:center + half_h, :] = f[center - half_h:center + half_h, :]
        result.append(canvas)
    return result

# SAVE FUNCTION
def save_video(frames, path, fps):
    height, width = frames[0].shape[:2]
    out = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    for f in frames:
        out.write(f)
    out.release()

# MAIN ENTRY POINT
def process_video(input_path, output_path, transition_name, transition_duration=1.5):
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    transition_frames = int(fps * transition_duration)

    frames = []
    while True:
        ret, f = cap.read()
        if not ret:
            break
        frames.append(f)
    cap.release()

    intro = frames[:transition_frames]
    middle = frames[transition_frames:-transition_frames]
    outro = frames[-transition_frames:]

    # Transition registry
    trans_funcs = {
        "fade": lambda: (fade(intro), fade(outro, True)),
        "slide_left": lambda: (slide(intro, "left"), slide(outro, "left", True)),
        "slide_right": lambda: (slide(intro, "right"), slide(outro, "right", True)),
        "zoom": lambda: (zoom(intro, True), zoom(outro, False)),
        "wipe_down": lambda: (wipe(intro, "down"), wipe(outro, "down", True)),
        "wipe_up": lambda: (wipe(intro, "up"), wipe(outro, "up", True)),
        "blinds": lambda: (blinds(intro), blinds(outro, True)),
        "pixelate": lambda: (pixelate(intro), pixelate(outro, True)),
        "dissolve": lambda: (dissolve(intro), dissolve(outro, True)),
        "expand_line": lambda: (expand_line(intro), expand_line(outro, True)),
    }

    if transition_name not in trans_funcs:
        raise ValueError(f"Unknown transition: {transition_name}")

    intro_frames, outro_frames = trans_funcs[transition_name]()
    full = intro_frames + middle + outro_frames
    save_video(full, output_path, fps)
