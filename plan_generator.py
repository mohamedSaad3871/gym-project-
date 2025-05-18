import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")

# Check if API key is set and valid
if not api_key or api_key == "your_openai_api_key_here":
    print("Warning: OpenAI API key is not set or is using default value. AI features will not work.")

# Initialize client even if key is invalid (will handle errors later)
client = OpenAI(api_key=api_key)

def generate_ai_workout_plan(goal, level, days_per_week, gender=None, age=None, weight=None, limitations=None, language="ar"):
    """
    Generate a personalized workout plan using OpenAI API
    
    Args:
        goal (str): User's fitness goal (muscle_gain, fat_loss, etc.)
        level (str): User's fitness level (beginner, intermediate, advanced)
        days_per_week (int): Number of workout days per week
        gender (str, optional): User's gender (male, female)
        age (str, optional): User's age range
        weight (str, optional): User's weight in kg
        limitations (str, optional): Any health limitations or injuries
        language (str): Language for the response (default: Arabic)
    
    Returns:
        dict: Workout plan data
    """
    # Check if API key is valid
    if not api_key or api_key == "your_openai_api_key_here":
        # Return a default workout plan if no valid API key
        print("Using default workout plan generator - API key not configured")
        return generate_default_workout_plan(goal, level, days_per_week)
        
    try:
        # Convert parameters to Arabic for better context
        goal_ar = {
            'muscle_gain': 'بناء العضلات',
            'fat_loss': 'حرق الدهون',
            'maintenance': 'المحافظة على الوزن',
            'fitness': 'اللياقة العامة',
            'strength': 'القوة'
        }.get(goal, goal)
        
        level_ar = {
            'beginner': 'مبتدئ',
            'intermediate': 'متوسط',
            'advanced': 'متقدم'
        }.get(level, level)
        
        # Create prompt for OpenAI - Enhanced with more details
        prompt = f"""
        أنشئ خطة تمارين رياضية مخصصة ودقيقة علمياً بناءً على المعلومات التالية:
        - الهدف: {goal_ar}
        - المستوى: {level_ar}
        - عدد أيام التمرين في الأسبوع: {days_per_week}
        """        
        
        # Add personal information if available
        if gender:
            gender_ar = "ذكر" if gender == "male" else "أنثى"
            prompt += f"\n- الجنس: {gender_ar}"
            
        if age:
            prompt += f"\n- العمر: {age}"
            
        if weight:
            prompt += f"\n- الوزن: {weight} كجم"
            
        if limitations:
            prompt += f"\n- قيود صحية أو إصابات: {limitations}"
            
        prompt += f"""
        
        يجب أن تكون الخطة شاملة ومصممة على أسس علمية، وتتضمن:
        1. تقسيم الأيام حسب مجموعات العضلات مع مراعاة وقت الراحة المناسب بين التمارين المتشابهة
        2. التمارين المناسبة لكل يوم (4-6 تمارين) مع تفاصيل حول التقنية الصحيحة لكل تمرين
        3. عدد المجموعات والتكرارات والوزن النسبي (خفيف/متوسط/ثقيل) وفترة الراحة بين المجموعات
        4. تمارين الإحماء المناسبة قبل التمرين وتمارين الإطالة بعده
        5. توصيات للتقدم في البرنامج أسبوعياً (زيادة الوزن، التكرارات، الكثافة)
        6. نصائح مخصصة تراعي الظروف الصحية والقيود إن وجدت
        7. مؤشرات للتقدم وكيفية تتبع النتائج
        
        قم بإعادة البيانات بتنسيق JSON فقط بالشكل التالي:
        {{
            "plan": [
                {{
                    "day": 1,
                    "focus": "اسم تركيز اليوم",
                    "warmup": ["تمارين الإحماء"],
                    "exercises": [
                        {{
                            "name": "اسم التمرين",
                            "sets": "عدد المجموعات",
                            "reps": "عدد التكرارات",
                            "rest": "فترة الراحة بالثواني",
                            "intensity": "شدة التمرين (خفيف/متوسط/ثقيل)",
                            "technique": "وصف مختصر للتقنية الصحيحة",
                            "icon": "رمز Bootstrap (مثل: activity, heart, etc.)"
                        }}
                    ],
                    "cooldown": ["تمارين التهدئة"],
                    "tip": "نصيحة اليوم"
                }}
            ],
            "progression": "نصائح للتقدم في البرنامج أسبوعياً",
            "tips": ["نصائح عامة للبرنامج"],
            "nutrition_advice": "نصائح غذائية مناسبة للهدف"
        }}
        """
        
        # Call OpenAI API with enhanced model and parameters
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",  # Using a more capable model
            messages=[
                {"role": "system", "content": "أنت مدرب لياقة بدنية محترف مع خبرة 15 عاماً وشهادات معتمدة. تقوم بتصميم برامج تمارين مخصصة بناءً على أسس علمية وفسيولوجية دقيقة. أنت تراعي الفروق الفردية، والقيود الصحية، ومستويات اللياقة المختلفة. قدم الخطط بتفاصيل دقيقة تضمن السلامة والفعالية."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,  # More focused and consistent output
            max_tokens=2000,  # Increased from 1500
            response_format={ "type": "json_object" }  # Enforce JSON formatting
        )
        
        # Parse the response
        plan_text = response.choices[0].message.content.strip()
        
        # Process the JSON response
        try:
            # Parse the JSON response
            plan_data = json.loads(plan_text)
            
            # Validate and ensure all expected fields exist
            if "plan" not in plan_data:
                plan_data["plan"] = generate_default_workout_plan(goal, level, days_per_week)["plan"]
            
            if "tips" not in plan_data:
                plan_data["tips"] = ["تناول كمية كافية من البروتين بعد التمرين", "تأكد من شرب الماء بكمية كافية قبل وأثناء وبعد التمرين"]
                
            return plan_data
        except json.JSONDecodeError:
            # Fallback to a simple structure if JSON parsing fails
            return {"error": "Could not parse the AI response", "raw_response": plan_text}
            
    except Exception as e:
        print(f"Error generating workout plan: {str(e)}")
        # Return default plan on error
        return generate_default_workout_plan(goal, level, days_per_week)


def generate_default_workout_plan(goal, level, days_per_week):
    """Generate a default workout plan when API is not available"""
    
    # Basic workout plans based on goals
    if goal == 'muscle_gain':
        focus_areas = ['الصدر والترايسبس', 'الظهر والبايسبس', 'الأكتاف والبطن', 'الأرجل']
        tips = [
            'تأكد من تناول كمية كافية من البروتين بعد التمرين',
            'ركز على الوزن والتقنية الصحيحة أكثر من عدد التكرارات',
            'خذ قسطاً كافياً من الراحة بين المجموعات (1-2 دقيقة)',
            'زد الوزن تدريجياً كل أسبوع لتحفيز نمو العضلات'
        ]
    elif goal == 'fat_loss':
        focus_areas = ['تمارين الجسم كامل', 'تمارين هوائية وقلب', 'تمارين الجزء العلوي', 'تمارين الجزء السفلي']
        tips = [
            'حافظ على معدل ضربات قلب مرتفع خلال التمرين',
            'قلل فترات الراحة بين التمارين لزيادة حرق السعرات',
            'دمج تمارين الكارديو مع تمارين القوة لأفضل النتائج',
            'تناول وجبة خفيفة قبل التمرين بساعة للحصول على الطاقة اللازمة'
        ]
    else:  # general fitness or other goals
        focus_areas = ['تمارين الجسم كامل', 'تمارين القلب واللياقة', 'تمارين القوة', 'تمارين المرونة والتوازن']
        tips = [
            'تنويع التمارين يساعد على تحسين اللياقة الشاملة',
            'اهتم بالإحماء الجيد قبل التمرين والتهدئة بعده',
            'حافظ على شرب الماء بكميات كافية خلال التمرين',
            'استمع لجسمك وتوقف إذا شعرت بألم غير طبيعي'
        ]
    
    # Adjust sets and reps based on level
    if level == 'beginner':
        sets = '3'
        reps = '10-12'
    elif level == 'intermediate':
        sets = '4'
        reps = '8-10'
    else:  # advanced
        sets = '5'
        reps = '6-8'
    
    # Create plan based on number of days
    days = min(int(days_per_week), len(focus_areas))
    plan = []
    
    for i in range(days):
        day_index = i % len(focus_areas)
        
        # Create exercises based on focus area
        if 'صدر' in focus_areas[day_index]:
            exercises = [
                {"name": "بنش برس", "sets": sets, "reps": reps, "icon": "arrow-up-circle"},
                {"name": "تمرين الضغط", "sets": sets, "reps": reps, "icon": "arrow-down-circle"},
                {"name": "فلاي بالدمبل", "sets": sets, "reps": reps, "icon": "arrow-left-right"},
                {"name": "تمارين الترايسبس", "sets": sets, "reps": reps, "icon": "lightning"}
            ]
        elif 'ظهر' in focus_areas[day_index]:
            exercises = [
                {"name": "سحب بار", "sets": sets, "reps": reps, "icon": "arrow-up"},
                {"name": "سحب دمبل", "sets": sets, "reps": reps, "icon": "arrow-down"},
                {"name": "تمرين الظهر العلوي", "sets": sets, "reps": reps, "icon": "arrow-bar-up"},
                {"name": "تمارين البايسبس", "sets": sets, "reps": reps, "icon": "lightning"}
            ]
        elif 'أرجل' in focus_areas[day_index]:
            exercises = [
                {"name": "سكوات", "sets": sets, "reps": reps, "icon": "arrow-down-up"},
                {"name": "ديدليفت", "sets": sets, "reps": reps, "icon": "arrow-up-square"},
                {"name": "تمرين الرجل الأمامية", "sets": sets, "reps": reps, "icon": "arrow-right-circle"},
                {"name": "تمرين الرجل الخلفية", "sets": sets, "reps": reps, "icon": "arrow-left-circle"}
            ]
        elif 'أكتاف' in focus_areas[day_index]:
            exercises = [
                {"name": "ضغط عسكري", "sets": sets, "reps": reps, "icon": "arrow-up-square"},
                {"name": "رفع جانبي", "sets": sets, "reps": reps, "icon": "arrow-left-right"},
                {"name": "رفع أمامي", "sets": sets, "reps": reps, "icon": "arrow-up-right"},
                {"name": "تمارين البطن", "sets": sets, "reps": reps, "icon": "lightning"}
            ]
        elif 'هوائية' in focus_areas[day_index] or 'قلب' in focus_areas[day_index]:
            exercises = [
                {"name": "جري", "sets": "1", "reps": "20 دقيقة", "icon": "stopwatch"},
                {"name": "تمارين القفز", "sets": "3", "reps": "45 ثانية", "icon": "arrow-up-square"},
                {"name": "تمارين البيربي", "sets": "3", "reps": "10", "icon": "lightning"},
                {"name": "الدراجة الثابتة", "sets": "1", "reps": "15 دقيقة", "icon": "bicycle"}
            ]
        else:  # general or full body
            exercises = [
                {"name": "سكوات", "sets": sets, "reps": reps, "icon": "arrow-down-up"},
                {"name": "ضغط", "sets": sets, "reps": reps, "icon": "arrow-down-circle"},
                {"name": "سحب", "sets": sets, "reps": reps, "icon": "arrow-up-circle"},
                {"name": "تمارين البطن", "sets": sets, "reps": reps, "icon": "lightning"}
            ]
        
        # Add day to plan
        plan.append({
            "day": i + 1,
            "focus": focus_areas[day_index],
            "exercises": exercises,
            "tip": tips[i % len(tips)]
        })
    
    return {"plan": plan}

def generate_ai_meal_plan(goal, gender, age, activity_level, weight=None, height=None, diet_type=None, meals_per_day=None, food_allergies=None, language="ar"):
    """
    Generate a personalized meal plan using OpenAI API
    
    Args:
        goal (str): User's fitness goal (muscle_gain, fat_loss, etc.)
        gender (str): User's gender (male, female)
        age (int): User's age
        activity_level (str): User's activity level (sedentary, moderate, active)
        weight (str, optional): User's weight in kg
        height (str, optional): User's height in cm
        diet_type (str, optional): User's dietary preferences (keto, vegan, etc.)
        meals_per_day (int, optional): Number of meals per day
        food_allergies (str, optional): Food allergies or intolerances
        language (str): Language for the response (default: Arabic)
    
    Returns:
        dict: Meal plan data
    """
    # Check if API key is valid
    if not api_key or api_key == "your_openai_api_key_here":
        # Return a default meal plan if no valid API key
        print("Using default meal plan generator - API key not configured")
        return generate_default_meal_plan(goal, gender, age, activity_level)
    
    try:
        # Convert parameters to Arabic for better context
        goal_ar = {
            'muscle_gain': 'بناء العضلات',
            'fat_loss': 'حرق الدهون',
            'weight_loss': 'إنقاص الوزن',
            'maintenance': 'المحافظة على الوزن',
            'health': 'تحسين الصحة العامة',
            'energy': 'زيادة الطاقة'
        }.get(goal, goal)
        
        gender_ar = "ذكر" if gender == "male" else "أنثى"
        
        activity_level_ar = {
            'sedentary': 'قليل الحركة',
            'moderate': 'نشاط معتدل',
            'active': 'نشط',
            'very_active': 'نشط جداً',
            'beginner': 'مبتدئ',
            'intermediate': 'متوسط',
            'advanced': 'متقدم'
        }.get(activity_level, activity_level)
        
        # Create enhanced prompt for OpenAI
        prompt = f"""
        أنشئ خطة غذائية متكاملة بناءً على المعلومات التالية:
        - الهدف: {goal_ar}
        - الجنس: {gender_ar}
        - العمر: {age}
        - مستوى النشاط البدني: {activity_level_ar}
        """
        
        if weight:
            prompt += f"\n- الوزن: {weight} كجم"
            
        if height:
            prompt += f"\n- الطول: {height} سم"
            
        if diet_type and diet_type != "any":
            diet_type_ar = {
                'low_carb': 'قليل الكربوهيدرات',
                'high_protein': 'عالي البروتين',
                'keto': 'كيتو',
                'vegetarian': 'نباتي',
                'vegan': 'نباتي صرف',
                'balanced': 'متوازن'
            }.get(diet_type, diet_type)
            prompt += f"\n- نوع النظام الغذائي: {diet_type_ar}"
        
        if meals_per_day:
            prompt += f"\n- عدد الوجبات يومياً: {meals_per_day}"
            
        if food_allergies:
            prompt += f"\n- حساسية طعام: {food_allergies}"
        
        prompt += f"""
        
        يجب أن تكون الخطة شاملة ومصممة على أسس علمية، وتتضمن:
        1. حساب السعرات الحرارية والماكروز (البروتين، الكربوهيدرات، الدهون) بدقة وبشكل يناسب الهدف والمعلومات المقدمة
        2. توزيع الوجبات على مدار اليوم مع مراعاة توقيت تناول العناصر الغذائية
        3. قائمة مقترحة لكل وجبة مع كميات محددة ومقدار السعرات والعناصر الغذائية
        4. بدائل غذائية لكل وجبة لتنويع الخيارات
        5. نصائح تتعلق بالترطيب وكمية الماء اليومية
        6. مكملات غذائية موصى بها إن لزم الأمر (اختياري)
        7. نصائح خاصة تناسب الهدف والحالة الصحية
        
        أعد البيانات بصيغة JSON فقط بالشكل التالي:
        {{
            "calories": الحد اليومي للسعرات,
            "protein": كمية البروتين اليومية بالجرام,
            "proteinPercent": نسبة البروتين من إجمالي السعرات,
            "carbs": كمية الكربوهيدرات اليومية بالجرام,
            "carbsPercent": نسبة الكربوهيدرات من إجمالي السعرات,
            "fat": كمية الدهون اليومية بالجرام,
            "fatPercent": نسبة الدهون من إجمالي السعرات,
            "water": كمية الماء اليومية باللتر,
            "meals": [
                {{
                    "name": "اسم الوجبة",
                    "timing": "وقت تناول الوجبة المفضل",
                    "foods": [
                        {{
                            "name": "اسم الطعام",
                            "portion": "حجم الحصة",
                            "calories": "السعرات الحرارية",
                            "protein": "كمية البروتين",
                            "carbs": "كمية الكربوهيدرات",
                            "fat": "كمية الدهون"
                        }}
                    ],
                    "alternatives": ["بدائل غذائية للوجبة"],
                    "tip": "نصيحة خاصة بالوجبة"
                }}
            ],
            "supplements": ["المكملات الغذائية الموصى بها (اختياري)"],
            "tips": ["نصائح عامة للنظام الغذائي"],
            "health_notes": "ملاحظات صحية مهمة"
        }}
        """
        
        # Call OpenAI API with enhanced model and parameters
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",  # Using a more capable model
            messages=[
                {"role": "system", "content": "أنت خبير تغذية محترف حاصل على شهادات معتمدة من أفضل المؤسسات العلمية، مع خبرة 15 عاماً في تخطيط وتصميم الأنظمة الغذائية. تستند توصياتك إلى أحدث الأبحاث العلمية في مجال التغذية والفسيولوجيا. أنت تراعي الاحتياجات الفردية المختلفة، وتقدم خططاً دقيقة ومخصصة تماماً."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,  # More focused and consistent output
            max_tokens=2000,  # Increased for detailed response
            response_format={ "type": "json_object" }  # Enforce JSON formatting
        )
        
        # Parse the response
        meal_plan_text = response.choices[0].message.content.strip()
        
        try:
            # Parse the JSON response
            meal_plan_data = json.loads(meal_plan_text)
            
            # Validate and ensure all expected fields exist
            if "meals" not in meal_plan_data:
                default_plan = generate_default_meal_plan(goal, gender, age, activity_level)
                meal_plan_data["meals"] = default_plan["meals"]
            
            if "calories" not in meal_plan_data:
                # Calculate basic calories if not provided
                if gender == "male":
                    base_calories = 2200
                else:
                    base_calories = 1800
                    
                meal_plan_data["calories"] = base_calories
                
                if "protein" not in meal_plan_data:
                    meal_plan_data["protein"] = round(base_calories * 0.3 / 4)  # 30% protein
                if "carbs" not in meal_plan_data:
                    meal_plan_data["carbs"] = round(base_calories * 0.4 / 4)  # 40% carbs
                if "fat" not in meal_plan_data:
                    meal_plan_data["fat"] = round(base_calories * 0.3 / 9)  # 30% fat
                    
            if "tips" not in meal_plan_data:
                meal_plan_data["tips"] = ["تناول الوجبات في مواعيد منتظمة", "شرب الماء بكميات كافية يومياً"]
                
            # Ensure proteinPercent, carbsPercent, fatPercent exist
            if "proteinPercent" not in meal_plan_data and "protein" in meal_plan_data:
                calories_from_protein = meal_plan_data["protein"] * 4
                meal_plan_data["proteinPercent"] = round((calories_from_protein / meal_plan_data["calories"]) * 100)
                
            if "carbsPercent" not in meal_plan_data and "carbs" in meal_plan_data:
                calories_from_carbs = meal_plan_data["carbs"] * 4
                meal_plan_data["carbsPercent"] = round((calories_from_carbs / meal_plan_data["calories"]) * 100)
                
            if "fatPercent" not in meal_plan_data and "fat" in meal_plan_data:
                calories_from_fat = meal_plan_data["fat"] * 9
                meal_plan_data["fatPercent"] = round((calories_from_fat / meal_plan_data["calories"]) * 100)
                
            return meal_plan_data
            
        except json.JSONDecodeError:
            # Fallback to default if JSON parsing fails
            print(f"Error parsing meal plan JSON: {meal_plan_text[:100]}...")
            return generate_default_meal_plan(goal, gender, age, activity_level)
            
    except Exception as e:
        print(f"Error generating meal plan: {str(e)}")
        # Return default plan on error
        return generate_default_meal_plan(goal, gender, age, activity_level)


def generate_default_meal_plan(goal, gender, age, activity_level):
    """Generate a default meal plan when API is not available"""
    
    # Calculate base calories (simplified formula)
    base_calories = 0
    if gender == 'male':
        base_calories = 2000 - (200 if int(age) > 50 else 0)
    else:
        base_calories = 1800 - (200 if int(age) > 50 else 0)
        
    # Adjust for activity level
    activity_multipliers = {
        'sedentary': 1.0,
        'light': 1.1,
        'moderate': 1.2,
        'active': 1.3,
        'very_active': 1.4
    }
    adjusted_calories = base_calories * activity_multipliers.get(activity_level, 1.0)
    
    # Adjust for goal
    if goal == 'muscle_gain':
        adjusted_calories += 300
        protein_percent = 35
        carbs_percent = 45
        fat_percent = 20
    elif goal == 'fat_loss':
        adjusted_calories -= 300
        protein_percent = 40
        carbs_percent = 30
        fat_percent = 30
    else:  # maintenance or general fitness
        protein_percent = 30
        carbs_percent = 40
        fat_percent = 30
    
    # Round calories to nearest 50
    calories = round(adjusted_calories / 50) * 50
    
    # Calculate macros
    protein = round((calories * (protein_percent/100)) / 4)  # 4 calories per gram of protein
    carbs = round((calories * (carbs_percent/100)) / 4)      # 4 calories per gram of carbs
    fat = round((calories * (fat_percent/100)) / 9)          # 9 calories per gram of fat
    
    # Create meal plan based on goal
    meals = []
    
    # Breakfast
    breakfast = {
        "name": "وجبة الإفطار",
        "icon": "sunrise",
        "foods": [
            {"name": "شوفان بالحليب", "portion": "كوب واحد", "calories": "300"}
        ],
        "tip": "تناول الإفطار خلال ساعة من الاستيقاظ لتعزيز التمثيل الغذائي"
    }
    
    # Morning snack
    morning_snack = {
        "name": "وجبة خفيفة صباحية",
        "icon": "cup",
        "foods": [
            {"name": "مكسرات غير مملحة", "portion": "30 غرام", "calories": "180"}
        ],
        "tip": "المكسرات مصدر جيد للدهون الصحية والبروتين"
    }
    
    # Lunch
    lunch = {
        "name": "وجبة الغداء",
        "icon": "sun",
        "foods": [
            {"name": "صدر دجاج مشوي", "portion": "150 غرام", "calories": "250"}
        ],
        "tip": "تناول البروتين مع الكربوهيدرات المعقدة للحصول على طاقة مستدامة"
    }
    
    # Afternoon snack
    afternoon_snack = {
        "name": "وجبة خفيفة مسائية",
        "icon": "cup",
        "foods": [
            {"name": "زبادي يوناني", "portion": "علبة صغيرة", "calories": "150"}
        ],
        "tip": "وجبة خفيفة مثالية قبل التمرين بساعة أو ساعتين"
    }
    
    # Dinner
    dinner = {
        "name": "وجبة العشاء",
        "icon": "moon",
        "foods": [
            {"name": "سمك مشوي", "portion": "150 غرام", "calories": "200"}
        ],
        "tip": "تناول العشاء قبل النوم بثلاث ساعات على الأقل"
    }
    
    # Customize breakfast based on goal
    if goal == 'muscle_gain':
        breakfast["foods"].append({"name": "موز", "portion": "حبة واحدة", "calories": "100"})
        breakfast["foods"].append({"name": "بيض مسلوق", "portion": "2 حبة", "calories": "140"})
    elif goal == 'fat_loss':
        breakfast["foods"] = [
            {"name": "بيض مسلوق", "portion": "2 حبة", "calories": "140"},
            {"name": "خضار مشكلة", "portion": "كوب واحد", "calories": "50"}
        ]
    else:
        breakfast["foods"].append({"name": "توست أسمر", "portion": "2 شرائح", "calories": "120"})
    
    # Customize lunch based on goal
    if goal == 'muscle_gain':
        lunch["foods"].append({"name": "أرز بني", "portion": "كوب واحد", "calories": "200"})
        lunch["foods"].append({"name": "سلطة خضراء", "portion": "طبق متوسط", "calories": "50"})
        lunch["foods"].append({"name": "أفوكادو", "portion": "نصف حبة", "calories": "120"})
    elif goal == 'fat_loss':
        lunch["foods"].append({"name": "سلطة خضراء كبيرة", "portion": "طبق كبير", "calories": "70"})
        lunch["foods"].append({"name": "كينوا", "portion": "نصف كوب", "calories": "120"})
    else:
        lunch["foods"].append({"name": "أرز بني", "portion": "نصف كوب", "calories": "100"})
        lunch["foods"].append({"name": "سلطة خضراء", "portion": "طبق متوسط", "calories": "50"})
    
    # Customize dinner based on goal
    if goal == 'muscle_gain':
        dinner["foods"].append({"name": "بطاطا حلوة", "portion": "حبة متوسطة", "calories": "100"})
        dinner["foods"].append({"name": "خضروات مشوية", "portion": "كوب واحد", "calories": "80"})
        dinner["foods"].append({"name": "جبن قليل الدسم", "portion": "30 غرام", "calories": "80"})
    elif goal == 'fat_loss':
        dinner["foods"].append({"name": "خضروات مشوية", "portion": "كوب ونصف", "calories": "120"})
    else:
        dinner["foods"].append({"name": "بطاطا مسلوقة", "portion": "حبة صغيرة", "calories": "100"})
        dinner["foods"].append({"name": "خضروات مشوية", "portion": "كوب واحد", "calories": "80"})
    
    # Add all meals to the plan
    meals.append(breakfast)
    meals.append(morning_snack)
    meals.append(lunch)
    
    # For muscle gain, add post-workout meal
    if goal == 'muscle_gain':
        post_workout = {
            "name": "وجبة ما بعد التمرين",
            "icon": "lightning",
            "foods": [
                {"name": "شيك بروتين", "portion": "كوب واحد", "calories": "150"},
                {"name": "موز", "portion": "حبة واحدة", "calories": "100"}
            ],
            "tip": "تناول البروتين والكربوهيدرات بعد التمرين مباشرة لتعزيز بناء العضلات"
        }
        meals.append(post_workout)
    else:
        meals.append(afternoon_snack)
    
    meals.append(dinner)
    
    # Return the complete meal plan
    return {
        "calories": calories,
        "protein": protein,
        "carbs": carbs,
        "fat": fat,
        "proteinPercent": protein_percent,
        "carbsPercent": carbs_percent,
        "fatPercent": fat_percent,
        "meals": meals
    }
