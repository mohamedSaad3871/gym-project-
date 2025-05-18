"""
Módulo para manejar recomendaciones basadas en restricciones de salud.
Proporciona funciones para ajustar planes de entrenamiento y nutrición
según condiciones médicas y limitaciones físicas del usuario.
"""

def analyze_health_restrictions(health_info):
    """
    Analiza la información de salud proporcionada y devuelve recomendaciones
    
    Args:
        health_info (dict): Diccionario con información de salud del usuario
        
    Returns:
        dict: Recomendaciones específicas basadas en las restricciones
    """
    restrictions = {
        'workout_modifications': [],
        'nutrition_recommendations': [],
        'general_advice': []
    }
    
    # Extraer información
    age = health_info.get('age', 30)
    conditions = health_info.get('conditions', [])
    injuries = health_info.get('injuries', [])
    medications = health_info.get('medications', [])
    diet_restrictions = health_info.get('diet_restrictions', [])
    
    # Recomendaciones basadas en la edad
    age = int(age) if isinstance(age, str) and age.isdigit() else age
    if age > 50:
        restrictions['workout_modifications'].extend([
            'Aumentar el tiempo de calentamiento a 10-15 minutos',
            'Enfocarse más en la técnica que en el peso máximo',
            'Incluir 2-3 días de recuperación entre entrenamientos intensos',
            'Incluir ejercicios específicos para mejorar la movilidad articular'
        ])
        restrictions['nutrition_recommendations'].extend([
            'Aumentar la ingesta de proteínas a 1.5-2g por kg de peso corporal',
            'Suplementar con vitamina D3 y calcio para la salud ósea',
            'Asegurar adecuada hidratación antes, durante y después del ejercicio'
        ])
    
    # Recomendaciones basadas en condiciones médicas
    if 'diabetes' in conditions or 'prediabetes' in conditions:
        restrictions['workout_modifications'].extend([
            'Evitar largas sesiones de cardio de alta intensidad en ayunas',
            'Monitorear los niveles de glucosa antes y después del ejercicio',
            'Llevar siempre una fuente de carbohidratos rápidos (jugo, gel) durante el entrenamiento'
        ])
        restrictions['nutrition_recommendations'].extend([
            'Distribuir los carbohidratos uniformemente a lo largo del día',
            'Priorizar carbohidratos complejos de bajo índice glucémico',
            'Combinar siempre carbohidratos con proteínas o grasas saludables'
        ])
    
    if 'hipertensión' in conditions or 'hipertension' in conditions or 'presión alta' in conditions:
        restrictions['workout_modifications'].extend([
            'Evitar el levantamiento de pesas muy pesadas',
            'Enfocarse en volumen (más repeticiones con menos peso)',
            'Evitar maniobras de Valsalva durante el entrenamiento',
            'Incorporar técnicas de respiración consciente'
        ])
        restrictions['nutrition_recommendations'].extend([
            'Limitar la ingesta de sodio a menos de 2300mg por día',
            'Aumentar el consumo de potasio a través de frutas y verduras',
            'Moderar o eliminar el consumo de alcohol',
            'Considerar la dieta DASH para la hipertensión'
        ])
    
    # Recomendaciones basadas en lesiones
    if any(i in injuries for i in ['rodilla', 'knee']):
        restrictions['workout_modifications'].extend([
            'Evitar ejercicios de alto impacto como saltos y carreras en superficies duras',
            'Sustituir sentadillas profundas por sentadillas parciales o con soportes',
            'Utilizar máquinas de extensión y curl de piernas con poco peso y muchas repeticiones',
            'Incorporar natación o ciclismo como cardio principal'
        ])
    
    if any(i in injuries for i in ['espalda', 'back', 'lumbar', 'cervical']):
        restrictions['workout_modifications'].extend([
            'Evitar peso muerto tradicional y flexiones de espalda',
            'Adaptar ejercicios para mantener la columna neutral',
            'Usar cinturón de soporte para ejercicios de carga',
            'Fortalecer el core con ejercicios isométricos como planchas'
        ])
    
    if any(i in injuries for i in ['hombro', 'shoulder']):
        restrictions['workout_modifications'].extend([
            'Evitar press por encima de la cabeza o detrás del cuello',
            'Sustituir press de banca por press con mancuernas que permitan rotación natural',
            'Usar agarre neutro (palmas enfrentadas) en ejercicios de jalón',
            'Incorporar ejercicios de movilidad y fortalecimiento del manguito rotador'
        ])
    
    # Recomendaciones basadas en medicamentos
    if 'anticoagulantes' in medications or 'blood thinners' in medications:
        restrictions['workout_modifications'].extend([
            'Evitar deportes de contacto y actividades con alto riesgo de caídas',
            'Limitar ejercicios de alta intensidad que puedan causar microtraumas'
        ])
        restrictions['general_advice'].extend([
            'Informar a entrenadores sobre el uso de anticoagulantes',
            'Usar equipo de protección adicional durante el entrenamiento'
        ])
    
    if 'beta bloqueadores' in medications or 'beta blockers' in medications:
        restrictions['workout_modifications'].extend([
            'No usar la frecuencia cardíaca como indicador de intensidad',
            'Utilizar la escala de esfuerzo percibido (RPE) para medir intensidad',
            'Evitar cambios bruscos de posición para prevenir mareos'
        ])
    
    # Recomendaciones basadas en restricciones dietéticas
    if 'vegetariano' in diet_restrictions or 'vegetarian' in diet_restrictions:
        restrictions['nutrition_recommendations'].extend([
            'Combinar diferentes fuentes de proteína vegetal para asegurar todos los aminoácidos esenciales',
            'Suplementar con vitamina B12, hierro y zinc',
            'Consumir proteína de suero (si lacto-vegetariano) o proteína vegetal después del entrenamiento'
        ])
    
    if 'vegano' in diet_restrictions or 'vegan' in diet_restrictions:
        restrictions['nutrition_recommendations'].extend([
            'Suplementar con vitamina B12, D3, hierro, zinc y posiblemente omega-3',
            'Consumir proteínas vegetales completas o combinaciones adecuadas',
            'Asegurar suficiente ingesta calórica para soportar el entrenamiento'
        ])
    
    if 'celíaco' in diet_restrictions or 'celiaco' in diet_restrictions or 'celiac' in diet_restrictions:
        restrictions['nutrition_recommendations'].extend([
            'Verificar que suplementos y batidos proteicos sean libres de gluten',
            'Utilizar pseudocereales como quinoa y amaranto para carbohidratos pre/post entrenamiento',
            'Obtener fibra de frutas, verduras y legumbres en lugar de granos con gluten'
        ])
    
    if 'intolerancia a la lactosa' in diet_restrictions or 'lactose intolerance' in diet_restrictions:
        restrictions['nutrition_recommendations'].extend([
            'Utilizar proteínas alternativas como aislado de proteína de suero, proteína vegetal o clara de huevo',
            'Considerar suplementos de calcio y vitamina D',
            'Elegir alternativas sin lactosa para las recetas que requieran lácteos'
        ])
    
    # Recomendaciones generales si no hay restricciones específicas
    if not any([restrictions['workout_modifications'], restrictions['nutrition_recommendations']]):
        restrictions['general_advice'].extend([
            'Realizar un calentamiento adecuado de 5-10 minutos antes de cada sesión',
            'Mantenerse hidratado antes, durante y después del ejercicio',
            'Priorizar una buena técnica sobre el peso levantado',
            'Incluir días de recuperación en el plan de entrenamiento',
            'Consumir una comida con proteínas y carbohidratos dentro de los 60 minutos post-entrenamiento'
        ])
    
    return restrictions

def get_exercise_substitutions(exercise_name):
    """
    Proporciona sustituciones para ejercicios específicos basados en restricciones comunes
    
    Args:
        exercise_name (str): Nombre del ejercicio original
        
    Returns:
        dict: Sustituciones para diferentes restricciones
    """
    substitutions = {
        'squat': {  # Sentadilla
            'knee_issues': ['Box squat', 'Partial squats', 'Leg press', 'Wall sits'],
            'back_issues': ['Front squat', 'Goblet squat', 'Leg press', 'Machine hack squat'],
            'shoulder_issues': ['Goblet squat', 'Safety bar squat', 'Belt squat'],
            'beginner': ['Bodyweight squat', 'TRX squat', 'Wall sit']
        },
        'deadlift': {  # Peso muerto
            'knee_issues': ['Romanian deadlift', 'Good morning', 'Back extension', 'Hip thrust'],
            'back_issues': ['Trap bar deadlift', 'Cable pull-through', 'Hip thrust', 'Kettlebell swing'],
            'beginner': ['Dumbbell Romanian deadlift', 'Bodyweight good morning', 'Glute bridge']
        },
        'bench press': {  # Press de banca
            'shoulder_issues': ['Floor press', 'Incline dumbbell press', 'Machine chest press', 'Cable chest press'],
            'wrist_issues': ['Push-ups', 'Machine chest press', 'Floor press with neutral grip'],
            'beginner': ['Push-ups', 'Incline push-ups', 'Machine chest press']
        },
        'overhead press': {  # Press militar
            'shoulder_issues': ['Landmine press', 'High incline press', 'Cable face pull', 'Lateral raises'],
            'back_issues': ['Seated overhead press', 'Landmine press', 'Machine shoulder press'],
            'beginner': ['Seated dumbbell press', 'Lateral raises', 'Front raises']
        },
        'pull-up': {  # Dominadas
            'shoulder_issues': ['Lat pulldown with neutral grip', 'Chest supported row', 'Machine pullover'],
            'elbow_issues': ['Lat pulldown', 'Straight arm pulldown', 'Cable row'],
            'beginner': ['Lat pulldown', 'Assisted pull-up machine', 'Inverted row', 'Band-assisted pull-up']
        },
        'running': {  # Correr
            'knee_issues': ['Cycling', 'Elliptical', 'Swimming', 'Rowing', 'Walking on incline'],
            'back_issues': ['Swimming', 'Walking', 'Recumbent bike', 'Elliptical'],
            'ankle_issues': ['Cycling', 'Swimming', 'Rowing', 'Upper body ergometer'],
            'beginner': ['Walking', 'Elliptical', 'Recumbent bike']
        }
    }
    
    # Normalizar nombre del ejercicio
    exercise_name = exercise_name.lower()
    
    # Buscar coincidencias exactas o parciales
    for key in substitutions:
        if key in exercise_name or exercise_name in key:
            return substitutions[key]
    
    # Si no hay coincidencias, devolver recomendaciones generales
    return {
        'general': [
            'Consultar con un profesional para encontrar una alternativa adecuada',
            'Considerar usar máquinas en lugar de pesos libres para mayor estabilidad',
            'Reducir el rango de movimiento o la carga del ejercicio original'
        ]
    } 