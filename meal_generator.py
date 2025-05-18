import os
import json
import random
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")

# Check if API key is set and valid
if not api_key or api_key == "your_openai_api_key_here":
    print("Warning: OpenAI API key is not set for meal_generator. Fallback functions will be used.")

# Initialize client even if key is invalid (will handle errors later)
client = OpenAI(api_key=api_key)

def generate_meal_with_ingredients(ingredients, meal_type="any", diet_type="any", goal="any", health_conditions="none"):
    """
    Generate a meal based on specified ingredients using AI
    
    Args:
        ingredients (list): List of ingredients to include
        meal_type (str): Type of meal (breakfast, lunch, dinner, snack, etc.)
        diet_type (str): Type of diet (keto, vegetarian, etc.)
        goal (str): Nutritional goal (muscle_gain, fat_loss, etc.)
        health_conditions (str): Health conditions to consider
        
    Returns:
        dict: Meal data
    """
    # Check if API key is valid
    if not api_key or api_key == "your_openai_api_key_here":
        print("Using fallback meal generator - API key not configured")
        return create_default_meal(meal_type, ingredients, diet_type, goal)
    
    try:
        # Translate parameters to Arabic for better context
        meal_type_ar = {
            'any': 'أي وجبة',
            'breakfast': 'فطور',
            'lunch': 'غداء',
            'dinner': 'عشاء',
            'snack': 'وجبة خفيفة',
            'pre_workout': 'وجبة ما قبل التمرين',
            'post_workout': 'وجبة ما بعد التمرين'
        }.get(meal_type, meal_type)
        
        diet_type_ar = {
            'any': 'عادي',
            'low_carb': 'قليل الكربوهيدرات',
            'high_protein': 'عالي البروتين',
            'keto': 'كيتو',
            'vegetarian': 'نباتي',
            'vegan': 'نباتي صرف'
        }.get(diet_type, diet_type)
        
        goal_ar = {
            'any': 'عام',
            'muscle_gain': 'بناء العضلات',
            'fat_loss': 'حرق الدهون',
            'health': 'تحسين الصحة',
            'energy': 'زيادة الطاقة'
        }.get(goal, goal)
        
        health_condition_ar = {
            'none': 'لا يوجد',
            'diabetes': 'مرض السكري',
            'hypertension': 'ارتفاع ضغط الدم',
            'heart_disease': 'أمراض القلب',
            'lactose_intolerance': 'عدم تحمل اللاكتوز',
            'gluten_intolerance': 'حساسية الجلوتين'
        }.get(health_conditions, health_conditions)
        
        # Format ingredients list
        ingredients_list = ', '.join(ingredients)
        
        # Create prompt for OpenAI
        prompt = f"""
        إنشاء وصفة {meal_type_ar} صحية متكاملة بناءً على المكونات التالية:
        
        المكونات المتاحة: {ingredients_list}
        
        الهدف الغذائي: {goal_ar}
        نوع النظام الغذائي: {diet_type_ar}
        حالات صحية خاصة: {health_condition_ar}
        
        يجب أن تتضمن الوصفة:
        1. اسم جذاب للوجبة
        2. قائمة المكونات المحددة مع الكميات
        3. طريقة التحضير البسيطة
        4. القيم الغذائية التقريبية (السعرات، البروتين، الكربوهيدرات، الدهون)
        5. نصيحة صحية متعلقة بالوجبة
        
        أعد البيانات بصيغة JSON فقط بالشكل التالي:
        {{
            "meals": [
                {{
                    "name": "اسم الوجبة",
                    "description": "وصف قصير للوجبة",
                    "ingredients": ["المكون الأول مع الكمية", "المكون الثاني مع الكمية"],
                    "instructions": "طريقة تحضير الوجبة",
                    "calories": القيمة الرقمية للسعرات,
                    "protein": القيمة الرقمية للبروتين بالجرام,
                    "carbs": القيمة الرقمية للكربوهيدرات بالجرام,
                    "fat": القيمة الرقمية للدهون بالجرام,
                    "tips": "نصيحة غذائية متعلقة بالوجبة"
                }}
            ]
        }}
        """
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",  # Using a capable model
            messages=[
                {"role": "system", "content": "أنت خبير تغذية متخصص في إعداد وصفات صحية مبتكرة. تقدم وصفات دقيقة مع مراعاة الأهداف الغذائية والحالات الصحية المختلفة. تلتزم بالمكونات المتاحة مع إضافة توابل أساسية عند الحاجة."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500,
            response_format={ "type": "json_object" }  # Enforce JSON formatting
        )
        
        # Parse the response
        meal_json = response.choices[0].message.content.strip()
        
        try:
            # Parse JSON response
            meal_data = json.loads(meal_json)
            
            # Add image placeholder if not already included
            if "meals" in meal_data and len(meal_data["meals"]) > 0:
                for meal in meal_data["meals"]:
                    if "image" not in meal:
                        # Add placeholder image based on meal type
                        if meal_type == "breakfast":
                            meal["image"] = "/static/images/breakfast.jpg"
                        elif meal_type == "lunch":
                            meal["image"] = "/static/images/lunch.jpg"
                        elif meal_type == "dinner":
                            meal["image"] = "/static/images/dinner.jpg"
                        elif meal_type == "snack":
                            meal["image"] = "/static/images/snack.jpg"
                        elif meal_type == "pre_workout":
                            meal["image"] = "/static/images/pre_workout.jpg"
                        elif meal_type == "post_workout":
                            meal["image"] = "/static/images/post_workout.jpg"
                        else:
                            meal["image"] = "/static/images/healthy_meal.jpg"
            
            return meal_data
        except json.JSONDecodeError as e:
            print(f"Error parsing meal JSON: {e}")
            print(f"Raw response: {meal_json[:200]}...")
            # Fallback to default if JSON parsing fails
            return create_default_meal(meal_type, ingredients, diet_type, goal)
    
    except Exception as e:
        print(f"Error generating meal: {str(e)}")
        # Return default meal on error
        return create_default_meal(meal_type, ingredients, diet_type, goal)

def create_default_meal(meal_type, ingredients=None, diet_type="any", goal="any"):
    """
    Create a default meal when API is not available or fails
    
    Args:
        meal_type (str): Type of meal (breakfast, lunch, dinner, snack)
        ingredients (list): List of available ingredients
        diet_type (str): Type of diet (keto, vegetarian, etc.)
        goal (str): Nutritional goal (muscle_gain, fat_loss, etc.)
        
    Returns:
        dict: Default meal data
    """
    # Initialize result structure
    meal_data = {"meals": []}
    
    # Categorize ingredients if available
    proteins = []
    carbs = []
    vegetables = []
    fruits = []
    dairy = []
    fats = []
    
    protein_foods = ["دجاج", "chicken", "لحم", "beef", "سمك", "fish", "بيض", "egg", "eggs", "تونة", "tuna", "بروتين", "protein", "عدس", "lentils"]
    carb_foods = ["أرز", "rice", "معكرونة", "pasta", "خبز", "bread", "شوفان", "oats", "بطاطا", "potato", "كينوا", "quinoa", "برغل", "bulgur"]
    vegetable_foods = ["خضروات", "طماطم", "tomato", "خيار", "cucumber", "خس", "lettuce", "جزر", "carrot", "بصل", "onion", "فلفل", "pepper", "broccoli", "بروكلي"]
    fruit_foods = ["موز", "banana", "تفاح", "apple", "برتقال", "orange", "فراولة", "strawberry", "توت", "berries", "أفوكادو", "avocado"]
    dairy_foods = ["حليب", "milk", "جبن", "cheese", "زبادي", "yogurt", "لبن", "زبدة", "butter"]
    fat_foods = ["زيت", "oil", "زيت زيتون", "olive oil", "زبدة اللوز", "almond butter", "مكسرات", "nuts", "بذور", "seeds"]
    
    if ingredients:
        for ing in ingredients:
            ing_lower = ing.lower()
            
            # Check categories - add only if the ingredient exists in the provided list
            if any(p in ing_lower for p in protein_foods):
                proteins.append(ing)
            elif any(c in ing_lower for c in carb_foods):
                carbs.append(ing)
            elif any(v in ing_lower for v in vegetable_foods):
                vegetables.append(ing)
            elif any(f in ing_lower for f in fruit_foods):
                fruits.append(ing)
            elif any(d in ing_lower for d in dairy_foods):
                dairy.append(ing)
            elif any(f in ing_lower for f in fat_foods):
                fats.append(ing)
    
    # Create meal based on type
    meal = {}
    
    # Set meal name based on type
    if meal_type == "breakfast":
        meal["name"] = "وجبة فطور صحية"
        meal["image"] = "/static/images/breakfast.jpg" 
        
        # Breakfast recipe based on available ingredients
        if "eggs" in ingredients or "بيض" in ingredients:
            meal["name"] = "أومليت بالخضروات"
            meal["description"] = "وجبة فطور غنية بالبروتين مع الخضروات المغذية"
            meal["ingredients"] = ["بيض (2-3 حبات)", "خضروات مقطعة (حسب المتاح)", "قليل من زيت الزيتون", "ملح وفلفل للتتبيل"]
            meal["instructions"] = "اخفق البيض في وعاء، أضف الخضروات المقطعة، سخن زيت الزيتون في مقلاة، اسكب خليط البيض واطهُ حتى ينضج."
            meal["calories"] = 300
            meal["protein"] = 18
            meal["carbs"] = 6
            meal["fat"] = 22
            
        elif "oats" in ingredients or "شوفان" in ingredients:
            meal["name"] = "شوفان مع الفواكه"
            meal["description"] = "وجبة فطور صحية غنية بالألياف لبداية يوم نشط"
            meal["ingredients"] = ["شوفان (نصف كوب)", "حليب أو ماء (كوب)", "فواكه طازجة أو مجففة", "عسل أو قرفة للتحلية (اختياري)"]
            meal["instructions"] = "اطهِ الشوفان مع الحليب أو الماء لمدة 3-5 دقائق، أضف الفواكه المقطعة والتحلية حسب الرغبة."
            meal["calories"] = 350
            meal["protein"] = 12
            meal["carbs"] = 60
            meal["fat"] = 6
            
        else:
            meal["name"] = "توست محمص مع إضافات صحية"
            meal["description"] = "وجبة فطور سريعة ومغذية"
            default_ingredients = ["خبز محمص (2 شريحة)", "إضافات متنوعة حسب المتاح (جبن/أفوكادو/بيض)"]
            meal["ingredients"] = default_ingredients
            meal["instructions"] = "حمص الخبز، أضف الإضافات المفضلة عليه وقدمه دافئاً."
            meal["calories"] = 250
            meal["protein"] = 10
            meal["carbs"] = 30
            meal["fat"] = 8
            
    elif meal_type == "lunch" or meal_type == "dinner":
        meal["name"] = "وجبة رئيسية متوازنة"
        meal["image"] = "/static/images/lunch.jpg" if meal_type == "lunch" else "/static/images/dinner.jpg"
        
        # Lunch/Dinner recipe based on available ingredients
        if proteins and vegetables:
            protein_item = proteins[0]
            veg_items = ", ".join(vegetables[:3])
            
            carb_text = ""
            if carbs:
                carb_text = f" مع {carbs[0]}"
            
            meal["name"] = f"{protein_item} مشوي{carb_text} والخضروات"
            meal["description"] = "وجبة صحية متكاملة غنية بالبروتين والعناصر الغذائية"
            meal["ingredients"] = [
                f"{protein_item} (150-200 جرام)",
                f"خضروات ({veg_items})",
                "زيت زيتون (ملعقة كبيرة)",
                "أعشاب وتوابل للنكهة"
            ]
            
            if carbs:
                meal["ingredients"].append(f"{carbs[0]} (كمية مناسبة)")
            
            meal["instructions"] = f"تتبيل {protein_item} بالتوابل المفضلة، شويه أو طهيه بطريقة صحية. طهي الخضروات على البخار أو مشوية. تقديم الجميع معًا في طبق متوازن."
            meal["calories"] = 450
            meal["protein"] = 35
            meal["carbs"] = 30
            meal["fat"] = 15
            
        else:
            meal["name"] = "طبق رئيسي متوازن"
            meal["description"] = "وجبة متكاملة تجمع بين البروتين والكربوهيدرات والخضروات"
            meal["ingredients"] = ["مصدر بروتين (150 جرام)", "خضروات موسمية (كوب)", "كربوهيدرات صحية (نصف كوب)", "زيت زيتون (ملعقة كبيرة)"]
            meal["instructions"] = "طهي مصدر البروتين بطريقة صحية، تحضير الخضروات المقطعة وطهيها، إضافة الكربوهيدرات المختارة وتقديم الجميع معًا."
            meal["calories"] = 500
            meal["protein"] = 30
            meal["carbs"] = 40
            meal["fat"] = 18
            
    elif meal_type == "snack":
        meal["name"] = "وجبة خفيفة صحية"
        meal["image"] = "/static/images/snack.jpg"
        
        # Snack recipe based on available ingredients
        if fruits:
            meal["name"] = f"سلطة فواكه طازجة"
            meal["description"] = "وجبة خفيفة منعشة غنية بالفيتامينات والمعادن"
            meal["ingredients"] = [f"فواكه متنوعة ({', '.join(fruits[:3])})", "قليل من العسل (اختياري)", "قليل من المكسرات (اختياري)"]
            meal["instructions"] = "قطّع الفواكه إلى قطع متوسطة، أضف العسل والمكسرات حسب الرغبة، قدمها باردة."
            meal["calories"] = 150
            meal["protein"] = 2
            meal["carbs"] = 30
            meal["fat"] = 2
            
        elif dairy:
            meal["name"] = f"{dairy[0]} مع إضافات صحية"
            meal["description"] = "وجبة خفيفة غنية بالبروتين والكالسيوم"
            meal["ingredients"] = [f"{dairy[0]} (كوب واحد)", "قليل من العسل أو الفواكه (اختياري)", "رشة قرفة أو فانيليا (اختياري)"]
            meal["instructions"] = f"ضع {dairy[0]} في وعاء، أضف التحلية والنكهات حسب الرغبة، يمكن إضافة حفنة من المكسرات أو بذور الشيا."
            meal["calories"] = 180
            meal["protein"] = 12
            meal["carbs"] = 15
            meal["fat"] = 6
            
        else:
            meal["name"] = "سناك صحي منزلي"
            meal["description"] = "وجبة خفيفة مغذية للطاقة بين الوجبات الرئيسية"
            meal["ingredients"] = ["مكسرات غير مملحة (حفنة)", "فواكه مجففة (قليل)", "زبادي (اختياري)"]
            meal["instructions"] = "امزج المكونات في وعاء صغير وتناولها كوجبة خفيفة بين الوجبات الرئيسية."
            meal["calories"] = 200
            meal["protein"] = 8
            meal["carbs"] = 20
            meal["fat"] = 10
            
    elif meal_type == "pre_workout":
        meal["name"] = "وجبة ما قبل التمرين"
        meal["image"] = "/static/images/pre_workout.jpg"
        meal["description"] = "وجبة خفيفة توفر الطاقة اللازمة للتمرين"
        meal["ingredients"] = ["موز (حبة واحدة)", "خبز محمص (شريحة)", "زبدة فول سوداني (ملعقة صغيرة)", "ماء (كوب)"]
        meal["instructions"] = "تناول الخبز المحمص مع زبدة الفول السوداني والموز قبل التمرين بساعة، مع شرب كمية كافية من الماء."
        meal["calories"] = 220
        meal["protein"] = 6
        meal["carbs"] = 35
        meal["fat"] = 6
        
    elif meal_type == "post_workout":
        meal["name"] = "وجبة ما بعد التمرين"
        meal["image"] = "/static/images/post_workout.jpg"
        meal["description"] = "وجبة غنية بالبروتين والكربوهيدرات لتعزيز التعافي العضلي"
        meal["ingredients"] = ["صدر دجاج مشوي (100 جرام)", "أرز بني (نصف كوب)", "خضروات مشوية (كوب)", "ماء (كوب)"]
        meal["instructions"] = "تناول هذه الوجبة خلال ساعة بعد التمرين لتحقيق أقصى استفادة في بناء العضلات والتعافي."
        meal["calories"] = 300
        meal["protein"] = 25
        meal["carbs"] = 30
        meal["fat"] = 5
        
    else:  # any or unknown meal type
        meal["name"] = "وجبة صحية متوازنة"
        meal["image"] = "/static/images/healthy_meal.jpg"
        meal["description"] = "وجبة متكاملة العناصر الغذائية"
        meal["ingredients"] = ["مكونات متوازنة من البروتين والكربوهيدرات والدهون الصحية"]
        meal["instructions"] = "مزج المكونات معاً بطريقة صحية وتقديمها في وجبة متوازنة."
        meal["calories"] = 400
        meal["protein"] = 20
        meal["carbs"] = 40
        meal["fat"] = 15
    
    # Add tips based on goal if specified
    if goal == "muscle_gain":
        meal["tips"] = "للاستفادة القصوى من هذه الوجبة لبناء العضلات، تأكد من تناول بروتين إضافي خلال اليوم وشرب كمية كافية من الماء."
    elif goal == "fat_loss":
        meal["tips"] = "لتعزيز حرق الدهون، يمكن تقليل كمية الكربوهيدرات في هذه الوجبة واستبدالها بخضروات إضافية."
    elif goal == "health":
        meal["tips"] = "هذه الوجبة غنية بمضادات الأكسدة والفيتامينات الضرورية لتعزيز الصحة العامة للجسم."
    elif goal == "energy":
        meal["tips"] = "للحصول على المزيد من الطاقة، يمكن إضافة قليل من الفواكه المجففة أو العسل الطبيعي لهذه الوجبة."
    else:
        meal["tips"] = "تناول هذه الوجبة ببطء والاستمتاع بمذاقها، مع شرب كمية كافية من الماء خلال اليوم."
    
    # Add meal to results
    meal_data["meals"].append(meal)
    
    # Add basic nutritional information
    meal_data["calories"] = meal["calories"]
    meal_data["protein"] = meal["protein"]
    meal_data["carbs"] = meal["carbs"]
    meal_data["fat"] = meal["fat"]
    
    return meal_data 