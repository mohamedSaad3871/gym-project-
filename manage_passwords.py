import hashlib
import sys
import getpass

# La misma sal utilizada en app.py
SALT = 'PowerGymSecureSalt123'

def secure_hash_password(password, salt=SALT):
    """Genera un hash seguro con sal para una contraseña"""
    salted_password = password + salt
    hash_obj = hashlib.sha256(salted_password.encode())
    return hash_obj.hexdigest()

def generate_password_hash():
    """Solicita una contraseña al usuario y genera un hash seguro"""
    print("\n=== Generador de Hash para Contraseñas ===")
    print("La contraseña no se mostrará mientras la escribes.")
    password = getpass.getpass(prompt="Introduce la nueva contraseña: ")
    confirm = getpass.getpass(prompt="Confirma la contraseña: ")
    
    if password != confirm:
        print("ERROR: Las contraseñas no coinciden.")
        return
    
    if len(password) < 8:
        print("ADVERTENCIA: La contraseña es demasiado corta (menos de 8 caracteres).")
        proceed = input("¿Deseas continuar de todos modos? (s/n): ")
        if proceed.lower() != 's':
            return
    
    # Generar y mostrar el hash
    hash_result = secure_hash_password(password)
    print("\n=== Resultado ===")
    print(f"Hash SHA-256 con sal: {hash_result}")
    print("\nActualiza la variable ADMIN_PASSWORD_HASH en app.py con este valor.")

def verify_password():
    """Verifica si un hash corresponde a una contraseña dada"""
    print("\n=== Verificador de Contraseñas ===")
    password = getpass.getpass(prompt="Introduce la contraseña: ")
    hash_to_verify = input("Introduce el hash a verificar: ")
    
    calculated_hash = secure_hash_password(password)
    
    if calculated_hash == hash_to_verify:
        print("\n✅ ÉXITO: La contraseña coincide con el hash.")
    else:
        print("\n❌ ERROR: La contraseña no coincide con el hash.")

def show_menu():
    """Muestra el menú principal"""
    print("\n===== Administrador de Contraseñas Power Gym =====")
    print("1. Generar hash para una nueva contraseña")
    print("2. Verificar una contraseña contra un hash")
    print("3. Salir")
    
    choice = input("Selecciona una opción (1-3): ")
    
    if choice == '1':
        generate_password_hash()
    elif choice == '2':
        verify_password()
    elif choice == '3':
        print("Saliendo...")
        sys.exit(0)
    else:
        print("Opción no válida.")

if __name__ == "__main__":
    # Si se proporciona un argumento, generar hash directamente
    if len(sys.argv) > 1 and sys.argv[1] == '--generate':
        if len(sys.argv) > 2:
            # Si se proporciona la contraseña como argumento (no recomendado para uso diario)
            print(secure_hash_password(sys.argv[2]))
        else:
            generate_password_hash()
    else:
        # De lo contrario, mostrar el menú interactivo
        while True:
            show_menu()
            input("\nPresiona Enter para continuar...") 