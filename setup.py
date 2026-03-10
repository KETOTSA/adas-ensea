#!/usr/bin/env python3
"""
Script pour générer les icônes PWA et initialiser la base de données.
Lancez ce script UNE FOIS après installation : python setup.py
"""
import os
import sys

def create_icons():
    """Create simple PWA icons without PIL if not available."""
    icons_dir = os.path.join(os.path.dirname(__file__), 'static', 'images')
    os.makedirs(icons_dir, exist_ok=True)
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        for size in [192, 512]:
            img = Image.new('RGB', (size, size), '#0a2342')
            draw = ImageDraw.Draw(img)
            # Gold circle
            margin = size // 6
            draw.ellipse([margin, margin, size - margin, size - margin], fill='#e8a027')
            # Sigma letter approximation (just a text)
            try:
                font_size = size // 3
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()
            text = "Σ"
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text(((size - tw) // 2, (size - th) // 2 - size//20), text, fill='#0a2342', font=font)
            path = os.path.join(icons_dir, f'icon-{size}.png')
            img.save(path)
            print(f"✅ Icône {size}x{size} créée : {path}")
    except ImportError:
        # Create minimal 1x1 PNG without PIL
        import base64
        # Minimal valid PNG (navy blue 1x1)
        png_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        )
        for size in [192, 512]:
            path = os.path.join(icons_dir, f'icon-{size}.png')
            with open(path, 'wb') as f:
                f.write(png_data)
        print("⚠️  Icônes placeholder créées (installez Pillow pour des vraies icônes)")

def init_db():
    """Initialize the database."""
    sys.path.insert(0, os.path.dirname(__file__))
    from app import create_app
    app = create_app()
    with app.app_context():
        from models import db
        db.create_all()
        print("✅ Base de données initialisée")
        
        # Check admin
        from models import User
        admin = User.query.filter_by(role='admin').first()
        if admin:
            print(f"✅ Admin existant : {admin.username}")
        else:
            print("⚠️  Aucun admin trouvé — il sera créé au premier lancement")

if __name__ == '__main__':
    print("=== Setup ADAS — Division Statistique ===\n")
    create_icons()
    try:
        init_db()
    except Exception as e:
        print(f"⚠️  DB init reportée au premier lancement : {e}")
    print("\n✅ Setup terminé ! Lancez : python app.py")
