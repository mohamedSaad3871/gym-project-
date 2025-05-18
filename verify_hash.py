import hashlib

# La misma sal utilizada en app.py
SALT = 'PowerGymSecureSalt123'

def secure_hash_password(password):
    """Genera un hash seguro con sal para una contraseña"""
    salted_password = password + SALT
    hash_obj = hashlib.sha256(salted_password.encode())
    return hash_obj.hexdigest()

# Verificar el hash para admin123
password = 'admin123'
hash_result = secure_hash_password(password)

print("=== Verificación de Hash ===")
print(f"Contraseña: {password}")
print(f"Hash generado: {hash_result}")
print("===========================") 