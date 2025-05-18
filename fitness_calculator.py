"""
Módulo para cálculos científicos relacionados con fitness y nutrición.
Incluye fórmulas para calcular requerimientos calóricos, ajustes según actividad,
y recomendaciones basadas en criterios de salud.
"""

def calculate_bmr(gender, weight, height, age):
    """
    Calcula la tasa metabólica basal (BMR) usando la fórmula Mifflin-St Jeor
    
    Args:
        gender (str): 'male' o 'female'
        weight (float): Peso en kilogramos
        height (float): Altura en centímetros
        age (int): Edad en años
        
    Returns:
        float: BMR en calorías por día
    """
    try:
        weight = float(weight)
        height = float(height)
        age = int(age)
        
        if gender == 'male':
            return (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:  # female
            return (10 * weight) + (6.25 * height) - (5 * age) - 161
    except (ValueError, TypeError):
        # Fallback to simpler calculation if inputs are invalid
        base = 1800 if gender == 'female' else 2000
        return base - (200 if age > 50 else 0)

def calculate_tdee(bmr, activity_level):
    """
    Calcula el Gasto Energético Total Diario (TDEE) basado en BMR y nivel de actividad
    
    Args:
        bmr (float): Tasa metabólica basal en calorías
        activity_level (str): Nivel de actividad
        
    Returns:
        float: TDEE en calorías por día
    """
    activity_multipliers = {
        'sedentary': 1.2,      # Poco o ningún ejercicio
        'light': 1.375,        # Ejercicio ligero 1-3 días/semana
        'moderate': 1.55,      # Ejercicio moderado 3-5 días/semana
        'active': 1.725,       # Ejercicio intenso 6-7 días/semana
        'very_active': 1.9     # Ejercicio muy intenso, trabajo físico o entrenamiento doble
    }
    
    return bmr * activity_multipliers.get(activity_level, 1.2)

def adjust_calories_for_goal(tdee, goal, intensity='moderate'):
    """
    Ajusta las calorías basadas en el objetivo
    
    Args:
        tdee (float): Gasto Energético Total Diario
        goal (str): 'muscle_gain', 'fat_loss', o 'maintenance'
        intensity (str): 'mild', 'moderate', o 'aggressive'
        
    Returns:
        float: Calorías diarias ajustadas
    """
    adjustment_factors = {
        'muscle_gain': {
            'mild': 0.1,        # +10% de calorías
            'moderate': 0.15,   # +15% de calorías
            'aggressive': 0.2   # +20% de calorías
        },
        'fat_loss': {
            'mild': -0.1,       # -10% de calorías
            'moderate': -0.2,   # -20% de calorías
            'aggressive': -0.25 # -25% de calorías
        },
        'maintenance': {
            'mild': 0,
            'moderate': 0,
            'aggressive': 0
        }
    }
    
    factor = adjustment_factors.get(goal, {}).get(intensity, 0)
    return tdee * (1 + factor)

def calculate_macros(calories, goal):
    """
    Calcula la distribución de macronutrientes basados en las calorías y el objetivo
    
    Args:
        calories (float): Calorías diarias
        goal (str): 'muscle_gain', 'fat_loss', o 'maintenance'
        
    Returns:
        dict: Contiene gramos y porcentajes de proteína, carbohidratos y grasas
    """
    macro_distribution = {
        'muscle_gain': {
            'protein_percent': 30,
            'carbs_percent': 45,
            'fat_percent': 25
        },
        'fat_loss': {
            'protein_percent': 40,
            'carbs_percent': 30,
            'fat_percent': 30
        },
        'maintenance': {
            'protein_percent': 30,
            'carbs_percent': 40,
            'fat_percent': 30
        }
    }
    
    distribution = macro_distribution.get(goal, macro_distribution['maintenance'])
    
    protein_percent = distribution['protein_percent']
    carbs_percent = distribution['carbs_percent'] 
    fat_percent = distribution['fat_percent']
    
    protein_grams = round((calories * (protein_percent/100)) / 4)  # 4 calorías por gramo
    carbs_grams = round((calories * (carbs_percent/100)) / 4)      # 4 calorías por gramo
    fat_grams = round((calories * (fat_percent/100)) / 9)          # 9 calorías por gramo
    
    return {
        'protein': protein_grams,
        'protein_percent': protein_percent,
        'carbs': carbs_grams,
        'carbs_percent': carbs_percent,
        'fat': fat_grams,
        'fat_percent': fat_percent
    }

def recommend_exercises_for_limitations(limitations):
    """
    Recomienda ejercicios adecuados y alternativas para personas con limitaciones físicas
    
    Args:
        limitations (str): Descripción de limitaciones físicas o condiciones médicas
        
    Returns:
        dict: Contiene ejercicios recomendados, ejercicios a evitar y alternativas
    """
    limitations = limitations.lower()
    recommendations = {
        'recommended': [],
        'avoid': [],
        'alternatives': []
    }
    
    # Problemas de rodilla
    if any(term in limitations for term in ['rodilla', 'knee', 'knees', 'artritis', 'arthritis']):
        recommendations['recommended'].extend([
            'natación', 'bicicleta estática', 'máquina elíptica', 'remo', 'ejercicios de la parte superior del cuerpo'
        ])
        recommendations['avoid'].extend([
            'sentadillas profundas', 'saltos', 'correr en superficies duras', 'zancadas profundas'
        ])
        recommendations['alternatives'].extend([
            'sentadillas parciales', 'elevaciones de piernas sentado', 'extensiones de pierna con poco peso'
        ])
    
    # Problemas de espalda
    if any(term in limitations for term in ['espalda', 'back', 'columna', 'spine', 'hernia', 'disc']):
        recommendations['recommended'].extend([
            'natación', 'caminar', 'yoga suave', 'pilates modificado', 'ejercicios de core isométricos'
        ])
        recommendations['avoid'].extend([
            'peso muerto tradicional', 'flexiones de espalda', 'ejercicios de torsión', 'sentadillas con peso pesado'
        ])
        recommendations['alternatives'].extend([
            'peso muerto con piernas rígidas', 'bird-dog', 'puentes de glúteos', 'planchas'
        ])
    
    # Problemas de hombro
    if any(term in limitations for term in ['hombro', 'shoulder', 'manguito rotador', 'rotator cuff']):
        recommendations['recommended'].extend([
            'ejercicios con banda elástica', 'elevaciones frontales con peso ligero', 'ejercicios de rotación externa'
        ])
        recommendations['avoid'].extend([
            'press militar por detrás de la cabeza', 'elevaciones laterales pesadas', 'flexiones declinadas'
        ])
        recommendations['alternatives'].extend([
            'press militar frontal', 'remo en posición neutral', 'elevaciones frontales y laterales con poco peso'
        ])
    
    # Problemas cardiovasculares
    if any(term in limitations for term in ['corazón', 'heart', 'presión', 'pressure', 'hipertensión', 'hypertension']):
        recommendations['recommended'].extend([
            'caminar', 'natación suave', 'ciclismo a baja intensidad', 'yoga', 'tai chi'
        ])
        recommendations['avoid'].extend([
            'ejercicios de alta intensidad', 'levantamiento de pesas muy pesadas', 'entrenamientos que involucren maniobra de Valsalva'
        ])
        recommendations['alternatives'].extend([
            'entrenamientos en circuito con pesos ligeros', 'ejercicios cardiovasculares de baja intensidad pero larga duración'
        ])
    
    # Si no hay recomendaciones específicas, dar generales
    if not recommendations['recommended']:
        recommendations['recommended'] = [
            'caminar', 'natación', 'ejercicios con bandas de resistencia', 'yoga suave', 'entrenamiento de fuerza con pesos ligeros'
        ]
    
    return recommendations 