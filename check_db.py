import sqlite3
import os

def check_database():
    conn = sqlite3.connect('instance/gym.db')
    cursor = conn.cursor()
    
    # Listar todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("Tablas en la base de datos:")
    for table in tables:
        print(f"- {table[0]}")
    
    # Verificar datos de artículos
    cursor.execute("SELECT id, title, image_url FROM articles")
    articles = cursor.fetchall()
    
    print("\nArtículos:")
    for article in articles:
        print(f"ID: {article[0]}, Título: {article[1]}, Imagen: {article[2]}")
    
    # Verificar si existe la tabla media
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='media'")
    media_exists = cursor.fetchone() is not None
    
    print("\nTabla Media existe:", media_exists)
    
    if media_exists:
        cursor.execute("SELECT id, title, filepath, filetype FROM media")
        media_items = cursor.fetchall()
        
        print("\nElementos en Media:")
        for item in media_items:
            print(f"ID: {item[0]}, Título: {item[1]}, Ruta: {item[2]}, Tipo: {item[3]}")
    
    # Verificar archivos físicos en las carpetas
    images_dir = os.path.join('static', 'uploads', 'images')
    videos_dir = os.path.join('static', 'uploads', 'videos')
    
    print("\nArchivos en carpeta de imágenes:")
    if os.path.exists(images_dir):
        files = os.listdir(images_dir)
        if files:
            for file in files:
                print(f"- {file}")
        else:
            print("No hay archivos en la carpeta de imágenes")
    else:
        print("La carpeta de imágenes no existe")
    
    print("\nArchivos en carpeta de videos:")
    if os.path.exists(videos_dir):
        files = os.listdir(videos_dir)
        if files:
            for file in files:
                print(f"- {file}")
        else:
            print("No hay archivos en la carpeta de videos")
    else:
        print("La carpeta de videos no existe")
    
    conn.close()

if __name__ == "__main__":
    check_database() 