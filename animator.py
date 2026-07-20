#!/usr/bin/env python3
import os
import subprocess
import zipfile
import time
import shutil
from PIL import Image, ImageDraw, ImageFont

# ====================================================
# 🔧 USER CONFIGURATION - TWEAK THESE
# ====================================================
INPUT_IMAGE = "logo.jpg"    # Your logo/stamp image (JPG, PNG, WEBP)
FPS = 30                          # Frames per second
DURATION_SECONDS = 8              # How long the bar takes to fill up
BAR_HEIGHT = 35                   # Thickness of the white bar
BAR_COLOR = (255, 255, 255)       # Pure white
TEXT_COLOR = (255, 255, 255)      # White text
SHOW_PERCENTAGE = True            # Show "Loading 45%" text?
FADE_IN_FRAMES = 10               # Frames to fade in from black
FADE_OUT_FRAMES = 10              # Frames to fade out to black
ADB_AUTO_PUSH = True              # Automatically push to phone after building?
REBOOT_AFTER_PUSH = True          # Reboot phone after pushing?
PADDING_PERCENT = 0.95            # 0.90-0.98: how much of screen the logo fills
BACKGROUND_COLOR = (0, 0, 0)      # Black background (use (255,255,255) for white)
CROP_TOLERANCE = 30               # How aggressive the auto-crop is (higher = more aggressive)
# ====================================================

def get_device_resolution():
    """Auto-detect phone resolution via ADB."""
    try:
        result = subprocess.check_output("adb shell wm size", shell=True, stderr=subprocess.DEVNULL).decode()
        resolution = result.split(":")[1].strip().split("x")
        if len(resolution) == 2:
            width, height = map(int, resolution)
            print(f"📱 Auto-detected resolution: {width}x{height}")
            return width, height
    except:
        pass
    print("⚠️  Could not auto-detect resolution. Using 1080x1920 (fallback).")
    return 1080, 1920

def trim_background(image, tolerance=30):
    """
    Removes solid-color padding around your logo (e.g., white/black borders).
    This makes the CIRCLE fill the screen instead of staying tiny inside a square.
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    bg_color = image.getpixel((0, 0))
    pixels = image.load()
    w, h = image.size
    
    left, right, top, bottom = w, 0, h, 0
    found = False
    
    # Scan all pixels to find the bounding box of non-background content
    for y in range(h):
        for x in range(w):
            p = pixels[x, y]
            # Check if pixel is significantly different from background
            if (abs(p[0] - bg_color[0]) > tolerance or
                abs(p[1] - bg_color[1]) > tolerance or
                abs(p[2] - bg_color[2]) > tolerance):
                if x < left: left = x
                if x > right: right = x
                if y < top: top = y
                if y > bottom: bottom = y
                found = True
    
    if found and left < right and top < bottom:
        cropped = image.crop((left, top, right + 1, bottom + 1))
        print(f"✂️  Auto-cropped padding: {w}x{h} → {cropped.width}x{cropped.height}")
        return cropped
    
    print("ℹ️  No padding detected — using image as-is.")
    return image

def create_bootanimation():
    # Auto-detect resolution
    WIDTH, HEIGHT = get_device_resolution()
    
    num_frames = FPS * DURATION_SECONDS
    total_frames = num_frames + FADE_IN_FRAMES + FADE_OUT_FRAMES
    
    # 1. Load and prepare the logo (stamp)
    if not os.path.exists(INPUT_IMAGE):
        print(f"❌ Error: '{INPUT_IMAGE}' not found in the same folder!")
        return
    
    logo_img = Image.open(INPUT_IMAGE)
    orig_width, orig_height = logo_img.size
    print(f"🖼️  Loaded image: {orig_width}x{orig_height}")
    
    # 🔥 AUTO-CROP: Remove empty padding around the circle
    logo_img = trim_background(logo_img, tolerance=CROP_TOLERANCE)
    
    # Create a solid background canvas
    base_img = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND_COLOR)
    
    # --- RESIZE THE LOGO TO FIT WITHIN THE PADDING ---
    max_width = int(WIDTH * PADDING_PERCENT)
    max_height = int(HEIGHT * PADDING_PERCENT)
    
    # Calculate scale to fit inside the max box (preserves aspect ratio)
    scale_w = max_width / logo_img.width
    scale_h = max_height / logo_img.height
    scale = min(scale_w, scale_h)  # Use the smaller ratio to fully contain
    
    new_width = int(logo_img.width * scale)
    new_height = int(logo_img.height * scale)
    
    # Force resize (this WILL enlarge if needed)
    logo_resized = logo_img.resize((new_width, new_height), Image.LANCZOS)
    
    # Center the resized logo on the canvas
    x = (WIDTH - logo_resized.width) // 2
    y = (HEIGHT - logo_resized.height) // 2
    base_img.paste(logo_resized, (x, y))
    
    print(f"✅ Logo resized from {orig_width}x{orig_height} to {new_width}x{new_height}")
    print(f"   Centered on {WIDTH}x{HEIGHT} canvas with {BACKGROUND_COLOR} background")
    
    # 2. Create folders
    os.makedirs("part0", exist_ok=True)
    os.makedirs("part1", exist_ok=True)
    
    print(f"⏳ Generating {total_frames} frames for part0...")
    
    # 3. Generate Part 0 frames (filling bar — NO GLITCHES)
    for i in range(total_frames):
        # Calculate progress (0.0 to 1.0) and fade alpha
        if i < FADE_IN_FRAMES:
            progress = 0.0
            fade_alpha = i / FADE_IN_FRAMES
        elif i < num_frames + FADE_IN_FRAMES:
            progress = (i - FADE_IN_FRAMES) / num_frames
            fade_alpha = 1.0
        else:
            progress = 1.0
            fade_alpha = 1.0 - ((i - num_frames - FADE_IN_FRAMES) / FADE_OUT_FRAMES)
        
        bar_width = int(WIDTH * progress)
        
        # Copy the base canvas (with logo) for this frame
        frame = base_img.copy()
        draw = ImageDraw.Draw(frame)
        
        # Draw the progress bar
        y0 = HEIGHT - BAR_HEIGHT
        y1 = HEIGHT
        draw.rectangle([(0, y0), (bar_width, y1)], fill=BAR_COLOR)
        
        # Draw percentage text
        if SHOW_PERCENTAGE:
            text = f"{int(progress * 100)}%"
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
            except:
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (WIDTH - text_width) // 2
            y = HEIGHT - BAR_HEIGHT - text_height - 15
            draw.text((x, y), text, fill=TEXT_COLOR, font=font)
        
        # Apply fade-in/out
        if fade_alpha < 1.0:
            black_overlay = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
            frame = Image.blend(black_overlay, frame, fade_alpha)
        
        # Save frame
        frame.save(f"part0/frame_{i:04d}.png")
        
        if (i + 1) % 10 == 0:
            print(f"  Rendered {i+1}/{total_frames} frames")

    # 4. Generate Part 1 (Infinite loop - full bar, NO GLITCHES, NO "KALI" text)
    print("⏳ Generating 30 loop frames for part1...")
    for i in range(30):
        frame = base_img.copy()
        draw = ImageDraw.Draw(frame)
        
        # Full white bar
        draw.rectangle([(0, HEIGHT - BAR_HEIGHT), (WIDTH, HEIGHT)], fill=BAR_COLOR)
        
        # Subtle pulse glow (optional - keep it clean)
        pulse = int(15 * abs((i / 30) * 2 - 1))  # 0 to 15 and back
        if pulse > 0:
            glow_color = (255, 255, 255, pulse)
            draw.rectangle([(0, HEIGHT - BAR_HEIGHT - pulse//2), (WIDTH, HEIGHT + pulse//2)], 
                          outline=(255, 255, 255), width=2)
        
        # 👈 "KALI" text REMOVED as requested
        
        frame.save(f"part1/frame_{i:04d}.png")
    
    print("✅ All frames rendered.")
    
    # 5. Write desc.txt
    with open("desc.txt", "w") as f:
        f.write(f"{WIDTH} {HEIGHT} {FPS}\n")
        f.write(f"p 1 0 part0\n")   # Play part0 once (fill bar)
        f.write(f"p 0 0 part1\n")   # Loop part1 forever (pulsing full bar)
    print("✅ desc.txt created.")
    
    # 6. Pack into ZIP (STORE compression - critical for bootanimation)
    output_zip = "bootanimation.zip"
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_STORED) as zipf:
        zipf.write("desc.txt")
        for i in range(total_frames):
            zipf.write(f"part0/frame_{i:04d}.png")
        for i in range(30):
            zipf.write(f"part1/frame_{i:04d}.png")
    
    print(f"✅ SUCCESS! '{output_zip}' created ({total_frames + 30} frames total).")
    
    # 7. Clean up temporary folders and files
    shutil.rmtree("part0")
    shutil.rmtree("part1")
    os.remove("desc.txt")
    
    # 8. Auto-ADB push & reboot
    if ADB_AUTO_PUSH:
        print("\n📱 Pushing to phone via ADB...")
        try:
            subprocess.run(f"adb push {output_zip} /data/local/tmp/bootanimation.zip", shell=True, check=True)
            print("✅ File pushed to /data/local/tmp/")
            
            print("🔄 Updating Magisk module...")
            subprocess.run("adb shell su -c \"cp /data/local/tmp/bootanimation.zip /data/adb/modules/custom_bootanim/system/product/media/bootanimation.zip\"", shell=True, check=True)
            subprocess.run("adb shell su -c \"chmod 644 /data/adb/modules/custom_bootanim/system/product/media/bootanimation.zip\"", shell=True, check=True)
            print("✅ Magisk module updated!")
            
            if REBOOT_AFTER_PUSH:
                print("🔄 Rebooting device in 5 seconds... (press Ctrl+C to cancel)")
                for i in range(5, 0, -1):
                    print(f"   {i}...")
                    time.sleep(1)
                subprocess.run("adb shell reboot", shell=True)
                print("✅ Device rebooting. Your new boot animation will play on startup!")
        
        except subprocess.CalledProcessError as e:
            print(f"⚠️  ADB push failed: {e}")
            print("   You can manually push the file using:")
            print("   adb push bootanimation.zip /data/local/tmp/")
            print("   adb shell su -c \"cp /data/local/tmp/bootanimation.zip /data/adb/modules/custom_bootanim/system/product/media/bootanimation.zip\"")
            print("   adb shell reboot")
    
    print("\n🎉 All done! Enjoy your clean custom boot animation.")

if __name__ == "__main__":
    create_bootanimation()
