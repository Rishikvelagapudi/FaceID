from PIL import Image, ImageDraw
from pathlib import Path

def create_sample_image():
    input_dir = Path("data/input")
    input_dir.mkdir(parents=True, exist_ok=True)
    img_path = input_dir / "sample.jpg"
    
    # Create a 400x400 image with face-like feature shapes
    img = Image.new("RGB", (400, 400), color=(240, 220, 200))
    draw = ImageDraw.Draw(img)
    
    # Eyes
    draw.ellipse([120, 140, 160, 180], fill=(50, 50, 50))
    draw.ellipse([240, 140, 280, 180], fill=(50, 50, 50))
    
    # Nose
    draw.polygon([(200, 190), (185, 250), (215, 250)], fill=(200, 150, 130))
    
    # Mouth
    draw.arc([140, 260, 260, 310], start=0, end=180, fill=(180, 50, 50), width=8)
    
    img.save(img_path, quality=95)
    print(f"Sample image created at: {img_path.resolve()}")

if __name__ == "__main__":
    create_sample_image()
