from app import app, db, Exercise, Nutrition, Supplement, TrainingProgram, Article

def init_db():
    with app.app_context():
        # Create tables
        db.create_all()

        # Sample exercises
        exercises = [
            Exercise(
                name="تمارين القوة الأساسية",
                category="beginners",
                description="مجموعة من التمارين الأساسية لبناء القوة تشمل الضغط والقرفصاء ورفع الأثقال",
                video_url="https://www.youtube.com/embed/IODxDxX7oi4",
                image_url="/static/images/strength_training.jpg"
            ),
            Exercise(
                name="تمارين الكارديو المكثفة",
                category="fat_loss",
                description="تمارين عالية الكثافة لحرق الدهون وتحسين اللياقة القلبية",
                video_url="https://www.youtube.com/embed/ml6cT4AZdqI",
                image_url="/static/images/cardio.jpg"
            ),
            Exercise(
                name="يوجا للمرونة",
                category="home",
                description="تمارين يوجا لتحسين المرونة والتوازن والتنفس",
                video_url="https://www.youtube.com/embed/v7AYKMP6rOE",
                image_url="/static/images/yoga.jpg"
            ),
            Exercise(
                name="تمارين بناء العضلات",
                category="muscle_gain",
                description="تمارين مركزة لبناء الكتلة العضلية وزيادة القوة",
                video_url="https://www.youtube.com/embed/gey73xiS8F4",
                image_url="/static/images/muscle_building.jpg"
            )
        ]

        # Sample nutrition plans
        nutrition_plans = [
            Nutrition(
                title="وجبة الإفطار الصحية",
                category="meals",
                calories=500,
                description="شوفان مع الموز والعسل، بيض مسلوق، وعصير برتقال طازج",
                image_url="/static/images/breakfast.jpg"
            ),
            Nutrition(
                title="وجبة ما بعد التمرين",
                category="pre_post_workout",
                calories=400,
                description="بروتين مصل اللبن مع الموز والمكسرات",
                image_url="/static/images/post_workout.jpg"
            ),
            Nutrition(
                title="وجبة الغداء المتوازنة",
                category="beginners_diet",
                calories=700,
                description="صدر دجاج مشوي مع الأرز البني والخضروات المشكلة",
                image_url="/static/images/lunch.jpg"
            ),
            Nutrition(
                title="وجبة خفيفة للتخسيس",
                category="weight_loss",
                calories=250,
                description="سلطة خضراء مع التونة وزيت الزيتون والليمون",
                image_url="/static/images/diet_snack.jpg"
            )
        ]

        # Sample supplements
        supplements = [
            Supplement(
                name="بروتين مصل اللبن",
                category="protein",
                benefits="يساعد في بناء العضلات وإصلاح أنسجة الجسم بعد التمرين",
                side_effects="قد يسبب انتفاخ المعدة لدى بعض الأشخاص",
                recommended_dosage="20-30 غرام بعد التمرين"
            ),
            Supplement(
                name="كرياتين",
                category="performance",
                benefits="يزيد من القوة والأداء خلال التمارين عالية الكثافة",
                side_effects="قد يسبب احتباس الماء في الجسم",
                recommended_dosage="5 غرام يومياً"
            ),
            Supplement(
                name="أحماض أمينية متفرعة السلسلة (BCAA)",
                category="recovery",
                benefits="تساعد في تقليل التعب العضلي وتحسين التعافي",
                side_effects="نادراً ما تسبب آثاراً جانبية",
                recommended_dosage="5-10 غرام قبل أو أثناء التمرين"
            )
        ]

        # Sample training programs
        programs = [
            TrainingProgram(
                name="برنامج المبتدئين 3 أيام",
                category="beginner_3day",
                description="برنامج تدريبي للمبتدئين يركز على التمارين الأساسية لمدة 3 أيام في الأسبوع",
                schedule="اليوم 1: تمارين الصدر والكتف والترايسبس\nاليوم 2: تمارين الظهر والبايسبس\nاليوم 3: تمارين الأرجل والبطن"
            ),
            TrainingProgram(
                name="برنامج الضخامة 5 أيام",
                category="bulk",
                description="برنامج تدريبي مكثف لزيادة الكتلة العضلية والقوة",
                schedule="اليوم 1: الصدر\nاليوم 2: الظهر\nاليوم 3: الأكتاف\nاليوم 4: الأرجل\nاليوم 5: الذراعين"
            ),
            TrainingProgram(
                name="برنامج التنشيف",
                category="cutting",
                description="برنامج تدريبي لحرق الدهون والحفاظ على الكتلة العضلية",
                schedule="اليوم 1: تمارين الصدر والكارديو\nاليوم 2: تمارين الظهر والكارديو\nاليوم 3: تمارين الأرجل والكارديو\nاليوم 4: تمارين الأكتاف والذراعين والكارديو"
            ),
            TrainingProgram(
                name="تمارين منزلية بدون معدات",
                category="home",
                description="برنامج تدريبي يمكن تنفيذه في المنزل بدون الحاجة لمعدات رياضية",
                schedule="اليوم 1: تمارين الجزء العلوي من الجسم\nاليوم 2: تمارين الجزء السفلي من الجسم\nاليوم 3: تمارين القلب والأوعية الدموية\nاليوم 4: تمارين كامل الجسم"
            )
        ]

        # Sample articles
        articles = [
            Article(
                title="أخطاء شائعة يرتكبها المبتدئون في الجيم",
                category="common_mistakes",
                content="هناك العديد من الأخطاء الشائعة التي يرتكبها المبتدئون في صالة الألعاب الرياضية، منها: عدم الإحماء بشكل كافٍ قبل التمرين، استخدام أوزان ثقيلة جداً في البداية، عدم الاهتمام بالتقنية الصحيحة للتمارين، وعدم الالتزام بنظام غذائي مناسب. من المهم تجنب هذه الأخطاء لتحقيق أفضل النتائج وتجنب الإصابات.",
                image_url="/static/images/mistakes.jpg"
            ),
            Article(
                title="كيف تبني عادة ممارسة الرياضة بانتظام",
                category="habits",
                content="لبناء عادة ممارسة الرياضة بانتظام، يجب عليك: تحديد أهداف واقعية، اختيار تمارين تستمتع بها، تخصيص وقت محدد للتمرين في جدولك اليومي، البدء تدريجياً وزيادة الشدة مع الوقت، الاستعانة بصديق أو مدرب للتحفيز، والاحتفال بالإنجازات الصغيرة. استمر على هذا النهج لمدة 21 يوماً على الأقل لتصبح عادة راسخة.",
                image_url="/static/images/habits.jpg"
            ),
            Article(
                title="نصائح للحفاظ على الحافز الرياضي",
                category="motivation",
                content="للحفاظ على الحافز الرياضي، جرب هذه النصائح: تنويع التمارين لتجنب الملل، وضع أهداف قصيرة وطويلة المدى، تتبع تقدمك، الانضمام إلى مجموعة رياضية، الاستماع إلى الموسيقى المحفزة أثناء التمرين، مشاهدة مقاطع فيديو ملهمة، وتذكر سبب بدء رحلتك الرياضية. من المهم أيضاً أخذ فترات راحة مناسبة لتجنب الإرهاق والحفاظ على الحماس.",
                image_url="/static/images/motivation.jpg"
            )
        ]

        # Add sample data to database
        db.session.add_all(exercises)
        db.session.add_all(nutrition_plans)
        db.session.add_all(supplements)
        db.session.add_all(programs)
        db.session.add_all(articles)
        db.session.commit()

if __name__ == '__main__':
    init_db()