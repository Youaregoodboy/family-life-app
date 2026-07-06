from PIL import Image, ImageDraw, ImageFont
import os

def generate_icon(size, primary_color, output_path, icon_type='parent'):
    img = Image.new('RGBA', (size, size), primary_color)
    draw = ImageDraw.Draw(img)
    
    center = size // 2
    icon_size = size * 0.4
    
    if icon_type == 'parent':
        heart_color = (255, 255, 255, 230)
        r = int(icon_size * 0.4)
        cx, cy = center, int(center * 0.95)
        
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=heart_color)
        draw.ellipse([cx - r*1.2, cy - r*0.6, cx - r*0.2, cy + r*0.4], fill=heart_color)
        draw.ellipse([cx + r*0.2, cy - r*0.6, cx + r*1.2, cy + r*0.4], fill=heart_color)
        
        triangle_points = [
            (cx - r*1.3, cy),
            (cx + r*1.3, cy),
            (cx, cy + r*1.5)
        ]
        draw.polygon(triangle_points, fill=heart_color)
    else:
        smile_color = (255, 255, 255, 230)
        r = int(icon_size * 0.45)
        cx, cy = center, center
        
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=smile_color)
        
        eye_r = int(r * 0.12)
        draw.ellipse([cx - r*0.5 - eye_r, cy - r*0.3 - eye_r, cx - r*0.5 + eye_r, cy - r*0.3 + eye_r], fill=primary_color)
        draw.ellipse([cx + r*0.5 - eye_r, cy - r*0.3 - eye_r, cx + r*0.5 + eye_r, cy - r*0.3 + eye_r], fill=primary_color)
        
        draw.arc([cx - r*0.5, cy - r*0.2, cx + r*0.5, cy + r*0.5], start=0, end=180, fill=primary_color, width=int(size * 0.04))
    
    img.save(output_path, 'PNG')
    print(f"Generated: {output_path}")

parent_icon_dir = r'C:\Users\user\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\work-mode-projects\6a466d41e573994274042302\family-life-app\web\parent\icons'
child_icon_dir = r'C:\Users\user\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\work-mode-projects\6a466d41e573994274042302\family-life-app\web\child\icons'

os.makedirs(parent_icon_dir, exist_ok=True)
os.makedirs(child_icon_dir, exist_ok=True)

parent_color = (99, 102, 241, 255)
child_color = (236, 72, 153, 255)

for size in [192, 512]:
    generate_icon(size, parent_color, os.path.join(parent_icon_dir, f'icon-{size}.png'), 'parent')
    generate_icon(size, child_color, os.path.join(child_icon_dir, f'icon-{size}.png'), 'child')

print("All icons generated!")
