import os
import sqlite3
from PIL import Image, ImageDraw, ImageFont
import shutil

def create_test_images():
    # Asegurarnos de que la carpeta existe
    images_dir = os.path.join('static', 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    # Obtener nombres de imágenes de la base de datos
    conn = sqlite3.connect('instance/gym.db')
    cursor = conn.cursor()
    cursor.execute("SELECT image_url FROM articles WHERE image_url IS NOT NULL")
    image_urls = cursor.fetchall()
    conn.close()
    
    print(f"Encontradas {len(image_urls)} URLs de imágenes en la base de datos")
    
    # Para cada URL, extraer nombre de archivo y crear imagen
    for url in image_urls:
        if not url[0]:
            continue
            
        # Extraer nombre de archivo
        filename = os.path.basename(url[0])
        image_path = os.path.join(images_dir, filename)
        
        print(f"Creando imagen: {image_path}")
        
        # Crear imagen de prueba
        img = Image.new('RGB', (800, 600), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        
        # Intentar usar una fuente, si falla usar el predeterminado
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except IOError:
            font = ImageFont.load_default()
            
        # Escribir texto en la imagen
        d.text((300, 200), filename, fill=(255, 255, 0), font=font)
        d.text((250, 300), "Imagen de prueba para Power Gym", fill=(255, 255, 0), font=font)
        
        # Guardar la imagen
        img.save(image_path)
        
    print("Proceso completado")

if __name__ == "__main__":
    create_test_images() 