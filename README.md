# Kali Nethunter Boot Animation Generator

This script turns **any image** (logo, stamp, wallpaper) into a fully functional `bootanimation.zip` for Kali NetHunter.  
It automatically crops empty padding, resizes your image to fit the screen, and adds a sleek white progress bar that fills up during boot—just like the official Kali Nethunter boot animation, but cleaner and fully customizable.

---

## ✨ Features

- 📱 **Auto-detects** your phone's screen resolution (via ADB)
- ✂️ **Auto-crops** invisible padding around logos/emblems
- 🖼️ **Forces scaling** to fill the screen (no more tiny stamps!)
- 🚀 **Auto-pushes** to your device and updates the Magisk module
- 🔄 **Optional auto-reboot** after installation
- 🎨 Fully configurable: bar thickness, colors, background, fade effects, percentage text
- 🧹 **No glitches, no extra text** (clean and minimal)

---

## 📋 Prerequisites

- Python 3.6+
- [Pillow](https://pypi.org/project/Pillow/) (`pip install Pillow`)
- [ADB](https://developer.android.com/studio/command-line/adb) installed and in `PATH`
- **Rooted Android** with **Magisk** (required for persistent installation)
- USB Debugging enabled on your device

---

## 🚀 Quick Start

1. **Clone this repo** or download `animator.py`.

2. **Place your image** in the same folder and rename it to `logo.jpg`  
   *(or change `INPUT_IMAGE` in the script)*.

3. **Connect your phone** via USB (with ADB debugging enabled).

4. **Run the script**:
   ```bash
   python3 animator.py
