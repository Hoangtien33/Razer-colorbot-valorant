# Razer Colorbot Valorant

External **Valorant Colorbot / Aimbot / Triggerbot** using **Razer driver input control**.

This project detects enemy outlines based on color and automatically moves the mouse or triggers shooting using Razer input APIs.

⚠️ Educational purposes only.

---

# Overview

This colorbot works by scanning a small region around the crosshair and detecting the enemy outline color used in Valorant.

When a matching color is found:

- the bot moves the mouse toward the target
- or automatically fires

Unlike memory-based cheats, colorbots operate by analyzing **screen pixels only**, without accessing the game process memory. :contentReference[oaicite:1]{index=1}

---

# Features

- 🎯 Color-based enemy detection
- 🔫 Triggerbot
- 🖱 Mouse control using Razer driver
- ⚡ Fast pixel scanning
- ⚙ Configurable parameters
- 🧠 Lightweight implementation
- 🎮 Designed for Valorant enemy outline detection

---

# How It Works

The bot follows these steps:

1. Capture screen pixels around crosshair
2. Convert captured image to HSV color space
3. Apply color threshold
4. Detect enemy outline color
5. Calculate pixel offset
6. Move mouse or fire automatically

Enemy outlines in Valorant are typically **purple or yellow**, which makes color detection easier.

---
