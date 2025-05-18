from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from datetime import timedelta
import secrets
import json
from plan_generator import generate_ai_workout_plan, generate_ai_meal_plan
from article_generator import generate_ai_article
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import uuid
from werkzeug.utils import secure_filename
import hashlib
import base64
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gym.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuraciones de seguridad adicionales
app.config['SESSION_COOKIE_SECURE'] = False  # Cambiar a True en producción con HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # Sesión dura 1 día

db = SQLAlchemy(app)

# Configuración de contraseña segura
ADMIN_USERNAME = 'admin'
# Sal para el hash (en producción, esto debería estar en una variable de entorno o un archivo de configuración)
SALT = 'PowerGymSecureSalt123'
# Hash con sal para 'admin123'
ADMIN_PASSWORD_HASH = '8e5afd38bdf737442c6176a0bd26356a4317cf85b16d1531401793a7cc62b1c3'  # Hash con sal de 'admin123'

# Función para generar hash seguro con sal
def secure_hash_password(password, salt=SALT):
    # Combinar contraseña y sal
    salted_password = password + salt
    # Generar hash SHA-256
    hash_obj = hashlib.sha256(salted_password.encode())
    # Devolver el hash en formato hexadecimal
    return hash_obj.hexdigest()

# Función para generar un nuevo hash (usar en consola para crear nuevas contraseñas)
def generate_password_hash(password):
    return secure_hash_password(password)

# El modelo se cargará desde ai_helper.py cuando sea necesario
def load_model():
    from ai_helper import load_model as load_ai_model
    load_ai_model()

# Models
class Exercise(db.Model):
    __tablename__ = 'exercises'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # beginners, muscle_gain, fat_loss, home
    description = db.Column(db.Text)
    video_url = db.Column(db.String(200))
    image_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Nutrition(db.Model):
    __tablename__ = 'nutrition'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # meals, beginners_diet, weight_loss, pre_post_workout
    calories = db.Column(db.Integer)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Supplement(db.Model):
    __tablename__ = 'supplements'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    benefits = db.Column(db.Text)
    side_effects = db.Column(db.Text)
    recommended_dosage = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TrainingProgram(db.Model):
    __tablename__ = 'training_programs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # beginner_3day, bulk, cutting, home
    description = db.Column(db.Text)
    schedule = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # common_mistakes, habits, motivation
    content = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    video_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# New Media model for storing uploaded files
class Media(db.Model):
    __tablename__ = 'media'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(255), nullable=False, unique=True)
    filepath = db.Column(db.String(255), nullable=False)
    filetype = db.Column(db.String(20)) # image, video, etc.
    filesize = db.Column(db.Integer)    # size in bytes
    category = db.Column(db.String(50)) # exercises, nutrition, articles, etc.
    alt_text = db.Column(db.String(255))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Alias para compatibilidad con init_db.py
Workout = Exercise

# Create the database tables
def init_db():
    with app.app_context():
        db.create_all()

# Configure upload directories
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
IMAGE_UPLOADS = os.path.join(UPLOAD_FOLDER, 'images')
VIDEO_UPLOADS = os.path.join(UPLOAD_FOLDER, 'videos')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov', 'avi'}

# Create upload directories if they don't exist
for directory in [UPLOAD_FOLDER, IMAGE_UPLOADS, VIDEO_UPLOADS]:
    os.makedirs(directory, exist_ok=True)

# Helper function to check allowed file extensions
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# API endpoints para acceso por AJAX
@app.route('/api/exercises')
def api_exercises():
    category = request.args.get('category', 'all')
    if category == 'all':
        exercises = Exercise.query.all()
    else:
        exercises = Exercise.query.filter_by(category=category).all()

    result = [{
        'id': ex.id,
        'name': ex.name,
        'category': ex.category,
        'description': ex.description,
        'video_url': ex.video_url,
        'image_url': ex.image_url
    } for ex in exercises]

    return jsonify(result)

@app.route('/api/nutrition')
def api_nutrition():
    category = request.args.get('category', 'all')
    if category == 'all':
        items = Nutrition.query.all()
    else:
        items = Nutrition.query.filter_by(category=category).all()

    result = [{
        'id': item.id,
        'title': item.title,
        'category': item.category,
        'calories': item.calories,
        'description': item.description,
        'image_url': item.image_url
    } for item in items]

    return jsonify(result)

# Admin authentication
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.cookies.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Crear hash de la contraseña proporcionada
        hashed_password = secure_hash_password(password)
        
        if username == ADMIN_USERNAME and hashed_password == ADMIN_PASSWORD_HASH:  
            response = redirect(url_for('admin_dashboard'))
            response.set_cookie('admin_logged_in', 'true', httponly=True)
            return response
        flash('بيانات الدخول غير صحيحة', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    response = redirect(url_for('admin_login'))
    response.delete_cookie('admin_logged_in')
    # Limpiar también la sesión de Flask si se utiliza
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return response

@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/articles')
@admin_required
def admin_articles():
    articles = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('admin/articles.html', articles=articles)

@app.route('/admin/article/new', methods=['GET', 'POST'])
@admin_required
def admin_article_new():
    if request.method == 'POST':
        # Initialize image_url and video_url
        image_url = None
        video_url = None
        
        # Handle image upload
        if 'image_file' in request.files and request.files['image_file'].filename:
            image_file = request.files['image_file']
            if allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                # Generate unique filename
                image_filename = f"{uuid.uuid4().hex}.{image_file.filename.rsplit('.', 1)[1].lower()}"
                image_filepath = os.path.join(IMAGE_UPLOADS, image_filename)
                image_file.save(image_filepath)
                image_url = f'/static/uploads/images/{image_filename}'
                
                # Save to media library
                media = Media(
                    title=f"Image for article: {request.form['title']}",
                    filename=image_filename,
                    filepath=image_url,
                    filetype='image',
                    filesize=os.path.getsize(image_filepath),
                    category='articles'
                )
                db.session.add(media)
        elif request.form.get('image_url'):
            image_url = request.form['image_url']
        
        # Handle video upload
        if 'video_file' in request.files and request.files['video_file'].filename:
            video_file = request.files['video_file']
            if allowed_file(video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
                # Generate unique filename
                video_filename = f"{uuid.uuid4().hex}.{video_file.filename.rsplit('.', 1)[1].lower()}"
                video_filepath = os.path.join(VIDEO_UPLOADS, video_filename)
                video_file.save(video_filepath)
                video_url = f'/static/uploads/videos/{video_filename}'
                
                # Save to media library
                media = Media(
                    title=f"Video for article: {request.form['title']}",
                    filename=video_filename,
                    filepath=video_url,
                    filetype='video',
                    filesize=os.path.getsize(video_filepath),
                    category='articles'
                )
                db.session.add(media)
        elif request.form.get('video_url'):
            video_url = request.form['video_url']
        
        article = Article(
            title=request.form['title'],
            category=request.form['category'],
            content=request.form['content'],
            image_url=image_url,
            video_url=video_url
        )
        db.session.add(article)
        db.session.commit()
        flash('تم إضافة المقال بنجاح', 'success')
        return redirect(url_for('admin_articles'))
    return render_template('admin/article_form.html')

@app.route('/admin/article/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_article_edit(id):
    article = Article.query.get_or_404(id)
    if request.method == 'POST':
        article.title = request.form['title']
        article.category = request.form['category']
        article.content = request.form['content']
        
        # Handle image upload
        if 'image_file' in request.files and request.files['image_file'].filename:
            image_file = request.files['image_file']
            if allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                # Generate unique filename
                image_filename = f"{uuid.uuid4().hex}.{image_file.filename.rsplit('.', 1)[1].lower()}"
                image_filepath = os.path.join(IMAGE_UPLOADS, image_filename)
                image_file.save(image_filepath)
                article.image_url = f'/static/uploads/images/{image_filename}'
                
                # Save to media library
                media = Media(
                    title=f"Image for article: {article.title}",
                    filename=image_filename,
                    filepath=article.image_url,
                    filetype='image',
                    filesize=os.path.getsize(image_filepath),
                    category='articles'
                )
                db.session.add(media)
        elif request.form.get('image_url'):
            article.image_url = request.form['image_url']
        
        # Handle video upload
        if 'video_file' in request.files and request.files['video_file'].filename:
            video_file = request.files['video_file']
            if allowed_file(video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
                # Generate unique filename
                video_filename = f"{uuid.uuid4().hex}.{video_file.filename.rsplit('.', 1)[1].lower()}"
                video_filepath = os.path.join(VIDEO_UPLOADS, video_filename)
                video_file.save(video_filepath)
                article.video_url = f'/static/uploads/videos/{video_filename}'
                
                # Save to media library
                media = Media(
                    title=f"Video for article: {article.title}",
                    filename=video_filename,
                    filepath=article.video_url,
                    filetype='video',
                    filesize=os.path.getsize(video_filepath),
                    category='articles'
                )
                db.session.add(media)
        elif request.form.get('video_url'):
            article.video_url = request.form['video_url']
        
        db.session.commit()
        flash('تم تحديث المقال بنجاح', 'success')
        return redirect(url_for('admin_articles'))
    return render_template('admin/article_form.html', article=article)

@app.route('/admin/article/delete/<int:id>')
@admin_required
def admin_article_delete(id):
    article = Article.query.get_or_404(id)
    db.session.delete(article)
    db.session.commit()
    flash('Article deleted successfully', 'success')
    return redirect(url_for('admin_articles'))

# إدارة التمارين
@app.route('/admin/exercises')
@admin_required
def admin_exercises():
    exercises = Exercise.query.order_by(Exercise.created_at.desc()).all()
    return render_template('admin/exercises.html', exercises=exercises)

@app.route('/admin/exercise/new', methods=['GET', 'POST'])
@admin_required
def admin_exercise_new():
    if request.method == 'POST':
        # Process the form data
        name = request.form['name']
        category = request.form['category']
        description = request.form['description']
        
        # Initialize image_url and video_url to None
        image_url = None
        video_url = None
        
        # Handle image upload or URL
        if 'image_file' in request.files and request.files['image_file'].filename:
            image_file = request.files['image_file']
            if allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                # Generate unique filename
                image_filename = f"{uuid.uuid4().hex}.{image_file.filename.rsplit('.', 1)[1].lower()}"
                image_filepath = os.path.join(IMAGE_UPLOADS, image_filename)
                image_file.save(image_filepath)
                image_url = f'/static/uploads/images/{image_filename}'
                
                # Save to media library
                media = Media(
                    title=f"Image for {name}",
                    filename=image_filename,
                    filepath=image_url,
                    filetype='image',
                    filesize=os.path.getsize(image_filepath),
                    category='exercises'
                )
                db.session.add(media)
        elif 'use_image_url' in request.form and request.form.get('image_url'):
            image_url = request.form['image_url']
        
        # Handle video upload or URL
        if 'video_file' in request.files and request.files['video_file'].filename:
            video_file = request.files['video_file']
            if allowed_file(video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
                # Generate unique filename
                video_filename = f"{uuid.uuid4().hex}.{video_file.filename.rsplit('.', 1)[1].lower()}"
                video_filepath = os.path.join(VIDEO_UPLOADS, video_filename)
                video_file.save(video_filepath)
                video_url = f'/static/uploads/videos/{video_filename}'
                
                # Save to media library
                media = Media(
                    title=f"Video for {name}",
                    filename=video_filename,
                    filepath=video_url,
                    filetype='video',
                    filesize=os.path.getsize(video_filepath),
                    category='exercises'
                )
                db.session.add(media)
        elif 'use_video_url' in request.form and request.form.get('video_url'):
            video_url = request.form['video_url']
        
        # Create and save the exercise
        exercise = Exercise(
            name=name,
            category=category,
            description=description,
            video_url=video_url,
            image_url=image_url
        )
        db.session.add(exercise)
        db.session.commit()
        
        flash('تم إضافة التمرين بنجاح', 'success')
        return redirect(url_for('admin_exercises'))
    
    return render_template('admin/exercise_form.html')

@app.route('/admin/exercise/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_exercise_edit(id):
    exercise = Exercise.query.get_or_404(id)
    
    if request.method == 'POST':
        exercise.name = request.form['name']
        exercise.category = request.form['category']
        exercise.description = request.form['description']
        
        # Handle image upload or URL
        if 'image_file' in request.files and request.files['image_file'].filename:
            image_file = request.files['image_file']
            if allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                # Generate unique filename
                image_filename = f"{uuid.uuid4().hex}.{image_file.filename.rsplit('.', 1)[1].lower()}"
                image_filepath = os.path.join(IMAGE_UPLOADS, image_filename)
                image_file.save(image_filepath)
                exercise.image_url = f'/static/uploads/images/{image_filename}'
                
                # Save to media library
                media = Media(
                    title=f"Image for {exercise.name}",
                    filename=image_filename,
                    filepath=exercise.image_url,
                    filetype='image',
                    filesize=os.path.getsize(image_filepath),
                    category='exercises'
                )
                db.session.add(media)
        elif 'use_image_url' in request.form and request.form.get('image_url'):
            exercise.image_url = request.form['image_url']
        
        # Handle video upload or URL
        if 'video_file' in request.files and request.files['video_file'].filename:
            video_file = request.files['video_file']
            if allowed_file(video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
                # Generate unique filename
                video_filename = f"{uuid.uuid4().hex}.{video_file.filename.rsplit('.', 1)[1].lower()}"
                video_filepath = os.path.join(VIDEO_UPLOADS, video_filename)
                video_file.save(video_filepath)
                exercise.video_url = f'/static/uploads/videos/{video_filename}'
                
                # Save to media library
                media = Media(
                    title=f"Video for {exercise.name}",
                    filename=video_filename,
                    filepath=exercise.video_url,
                    filetype='video',
                    filesize=os.path.getsize(video_filepath),
                    category='exercises'
                )
                db.session.add(media)
        elif 'use_video_url' in request.form and request.form.get('video_url'):
            exercise.video_url = request.form['video_url']
        
        db.session.commit()
        flash('تم تحديث التمرين بنجاح', 'success')
        return redirect(url_for('admin_exercises'))
        
    return render_template('admin/exercise_form.html', exercise=exercise)

@app.route('/admin/exercise/delete/<int:id>')
@admin_required
def admin_exercise_delete(id):
    exercise = Exercise.query.get_or_404(id)
    db.session.delete(exercise)
    db.session.commit()
    flash('تم حذف التمرين بنجاح', 'success')
    return redirect(url_for('admin_exercises'))

# إدارة التغذية
@app.route('/admin/nutrition')
@admin_required
def admin_nutrition():
    nutrition_items = Nutrition.query.order_by(Nutrition.created_at.desc()).all()
    return render_template('admin/nutrition.html', nutrition_items=nutrition_items)

@app.route('/admin/nutrition/new', methods=['GET', 'POST'])
@admin_required
def admin_nutrition_new():
    if request.method == 'POST':
        nutrition = Nutrition(
            title=request.form['title'],
            category=request.form['category'],
            calories=request.form['calories'],
            description=request.form['description'],
            image_url=request.form['image_url']
        )
        db.session.add(nutrition)
        db.session.commit()
        flash('تم إضافة خطة التغذية بنجاح', 'success')
        return redirect(url_for('admin_nutrition'))
    return render_template('admin/nutrition_form.html')

@app.route('/admin/nutrition/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_nutrition_edit(id):
    nutrition = Nutrition.query.get_or_404(id)
    if request.method == 'POST':
        nutrition.title = request.form['title']
        nutrition.category = request.form['category']
        nutrition.calories = request.form['calories']
        nutrition.description = request.form['description']
        nutrition.image_url = request.form['image_url']
        db.session.commit()
        flash('تم تحديث خطة التغذية بنجاح', 'success')
        return redirect(url_for('admin_nutrition'))
    return render_template('admin/nutrition_form.html', nutrition=nutrition)

@app.route('/admin/nutrition/delete/<int:id>')
@admin_required
def admin_nutrition_delete(id):
    nutrition = Nutrition.query.get_or_404(id)
    db.session.delete(nutrition)
    db.session.commit()
    flash('تم حذف خطة التغذية بنجاح', 'success')
    return redirect(url_for('admin_nutrition'))

# إدارة المكملات الغذائية
@app.route('/admin/supplements')
@admin_required
def admin_supplements():
    supplements = Supplement.query.order_by(Supplement.created_at.desc()).all()
    return render_template('admin/supplements.html', supplements=supplements)

@app.route('/admin/supplement/new', methods=['GET', 'POST'])
@admin_required
def admin_supplement_new():
    if request.method == 'POST':
        supplement = Supplement(
            name=request.form['name'],
            category=request.form['category'],
            benefits=request.form['benefits'],
            side_effects=request.form['side_effects'],
            recommended_dosage=request.form['recommended_dosage']
        )
        db.session.add(supplement)
        db.session.commit()
        flash('تم إضافة المكمل الغذائي بنجاح', 'success')
        return redirect(url_for('admin_supplements'))
    return render_template('admin/supplement_form.html')

@app.route('/admin/supplement/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_supplement_edit(id):
    supplement = Supplement.query.get_or_404(id)
    if request.method == 'POST':
        supplement.name = request.form['name']
        supplement.category = request.form['category']
        supplement.benefits = request.form['benefits']
        supplement.side_effects = request.form['side_effects']
        supplement.recommended_dosage = request.form['recommended_dosage']
        db.session.commit()
        flash('تم تحديث المكمل الغذائي بنجاح', 'success')
        return redirect(url_for('admin_supplements'))
    return render_template('admin/supplement_form.html', supplement=supplement)

@app.route('/admin/supplement/delete/<int:id>')
@admin_required
def admin_supplement_delete(id):
    supplement = Supplement.query.get_or_404(id)
    db.session.delete(supplement)
    db.session.commit()
    flash('تم حذف المكمل الغذائي بنجاح', 'success')
    return redirect(url_for('admin_supplements'))

# إدارة برامج التدريب
@app.route('/admin/programs')
@admin_required
def admin_programs():
    programs = TrainingProgram.query.order_by(TrainingProgram.created_at.desc()).all()
    return render_template('admin/programs.html', programs=programs)

@app.route('/admin/program/new', methods=['GET', 'POST'])
@admin_required
def admin_program_new():
    if request.method == 'POST':
        program = TrainingProgram(
            name=request.form['name'],
            category=request.form['category'],
            description=request.form['description'],
            schedule=request.form['schedule']
        )
        db.session.add(program)
        db.session.commit()
        flash('تم إضافة برنامج التدريب بنجاح', 'success')
        return redirect(url_for('admin_programs'))
    return render_template('admin/program_form.html')

@app.route('/admin/program/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_program_edit(id):
    program = TrainingProgram.query.get_or_404(id)
    if request.method == 'POST':
        program.name = request.form['name']
        program.category = request.form['category']
        program.description = request.form['description']
        program.schedule = request.form['schedule']
        db.session.commit()
        flash('تم تحديث برنامج التدريب بنجاح', 'success')
        return redirect(url_for('admin_programs'))
    return render_template('admin/program_form.html', program=program)

@app.route('/admin/program/delete/<int:id>')
@admin_required
def admin_program_delete(id):
    program = TrainingProgram.query.get_or_404(id)
    db.session.delete(program)
    db.session.commit()
    flash('تم حذف برنامج التدريب بنجاح', 'success')
    return redirect(url_for('admin_programs'))

# إعدادات الموقع
@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    # يمكن إضافة نموذج لإعدادات الموقع هنا
    if request.method == 'POST':
        # حفظ الإعدادات
        flash('تم حفظ الإعدادات بنجاح', 'success')
    return render_template('admin/settings.html')

# Biblioteca de medios
@app.route('/admin/media')
@admin_required
def admin_media():
    page = request.args.get('page', 1, type=int)
    per_page = 24
    media_query = Media.query.order_by(Media.created_at.desc())
    
    # Aplicar filtros si existen
    filetype = request.args.get('filetype')
    category = request.args.get('category')
    search = request.args.get('search')
    
    if filetype:
        media_query = media_query.filter(Media.filetype == filetype)
    if category:
        media_query = media_query.filter(Media.category == category)
    if search:
        media_query = media_query.filter(Media.title.ilike(f'%{search}%'))
    
    media_items = media_query.paginate(page=page, per_page=per_page)
    
    return render_template('admin/media.html', media_items=media_items)

# Ruta para cargar archivos
@app.route('/admin/media/upload', methods=['POST'])
@admin_required
def admin_media_upload():
    try:
        # Check if folder exists otherwise create it
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            os.makedirs(IMAGE_UPLOADS)
            os.makedirs(VIDEO_UPLOADS)
            
        if 'files[]' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400
            
        files = request.files.getlist('files[]')
        category = request.form.get('category', 'other')
        
        uploaded_files = []
        
        for file in files:
            if file.filename == '':
                continue
                
            original_filename = secure_filename(file.filename)
            file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            
            # Generate unique filename
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            
            # Determine file type and appropriate directory
            if allowed_file(original_filename, ALLOWED_IMAGE_EXTENSIONS):
                filetype = 'image'
                filepath = os.path.join(IMAGE_UPLOADS, unique_filename)
                relative_path = f'/static/uploads/images/{unique_filename}'
            elif allowed_file(original_filename, ALLOWED_VIDEO_EXTENSIONS):
                filetype = 'video'
                filepath = os.path.join(VIDEO_UPLOADS, unique_filename)
                relative_path = f'/static/uploads/videos/{unique_filename}'
            else:
                continue  # Skip unsupported files
            
            # Save file
            file.save(filepath)
            
            # Get file size
            filesize = os.path.getsize(filepath)
            
            # Save to database
            media = Media(
                title=original_filename.rsplit('.', 1)[0].replace('-', ' ').replace('_', ' ').title(),
                filename=unique_filename,
                filepath=relative_path,
                filetype=filetype,
                filesize=filesize,
                category=category
            )
            
            db.session.add(media)
            uploaded_files.append({
                'id': media.id,
                'title': media.title,
                'filepath': media.filepath,
                'filetype': media.filetype,
                'filesize': media.filesize
            })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{len(uploaded_files)} ملفات تم رفعها بنجاح',
            'files': uploaded_files
        })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API Endpoint to get media items
@app.route('/api/media')
@admin_required
def api_media():
    filetype = request.args.get('filetype')
    category = request.args.get('category')
    search = request.args.get('search')
    
    query = Media.query
    
    if filetype:
        query = query.filter(Media.filetype == filetype)
    if category:
        query = query.filter(Media.category == category)
    if search:
        query = query.filter(Media.title.ilike(f'%{search}%'))
    
    media_items = query.order_by(Media.created_at.desc()).all()
    
    result = [{
        'id': item.id,
        'title': item.title,
        'filepath': item.filepath,
        'filetype': item.filetype,
        'filesize': item.filesize,
        'category': item.category,
        'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for item in media_items]
    
    return jsonify(result)

# Delete media
@app.route('/admin/media/delete/<int:id>', methods=['POST'])
@admin_required
def admin_media_delete(id):
    media = Media.query.get_or_404(id)
    
    # Delete file from filesystem
    try:
        os.remove(os.path.join(app.static_folder, media.filepath.replace('/static/', '')))
    except (FileNotFoundError, OSError):
        pass
    
    # Delete from database
    db.session.delete(media)
    db.session.commit()
    
    return jsonify({'success': True})

# Edit media metadata
@app.route('/admin/media/edit/<int:id>', methods=['POST'])
@admin_required
def admin_media_edit(id):
    media = Media.query.get_or_404(id)
    
    media.title = request.form.get('title', media.title)
    media.alt_text = request.form.get('alt_text', media.alt_text)
    media.description = request.form.get('description', media.description)
    media.category = request.form.get('category', media.category)
    
    db.session.commit()
    
    return jsonify({'success': True})

# Routes
@app.route('/')
def home():
    featured_exercises = Exercise.query.limit(3).all()
    featured_nutrition = Nutrition.query.limit(3).all()
    featured_articles = Article.query.limit(3).all()
    
    # Create a sample prompt to display on the home page
    sample_workout_prompt = build_prompt(
        plan_type="workout",
        goal="muscle_gain",
        level="intermediate",
        gender="male",
        age="30",
        weight="75",
        days="4"
    )
    
    sample_nutrition_prompt = build_prompt(
        plan_type="nutrition",
        goal="fat_loss",
        level="intermediate",
        gender="male",
        age="30", 
        weight="75",
        days="4"
    )
    
    return render_template('index.html', 
                           featured_exercises=featured_exercises,
                           featured_nutrition=featured_nutrition,
                           featured_articles=featured_articles,
                           workout_prompt=sample_workout_prompt,
                           nutrition_prompt=sample_nutrition_prompt)

@app.route('/exercises/<category>')
def exercises(category):
    exercises = Exercise.query.filter_by(category=category).all()
    return render_template('exercises.html', exercises=exercises, category=category)

@app.route('/exercise/<int:id>')
def exercise_detail(id):
    exercise = Exercise.query.get_or_404(id)
    related = Exercise.query.filter_by(category=exercise.category).filter(Exercise.id != id).limit(3).all()
    return render_template('exercise_detail.html', exercise=exercise, related=related)

@app.route('/nutrition/<category>')
def nutrition(category):
    nutrition_items = Nutrition.query.filter_by(category=category).all()
    return render_template('nutrition.html', nutrition_plans=nutrition_items, category=category)

@app.route('/nutrition/item/<int:id>')
def nutrition_detail(id):
    item = Nutrition.query.get_or_404(id)
    related = Nutrition.query.filter_by(category=item.category).filter(Nutrition.id != id).limit(3).all()
    return render_template('nutrition_detail.html', plan=item, related=related)

@app.route('/programs/<category>')
def training_programs(category):
    programs = TrainingProgram.query.filter_by(category=category).all()
    return render_template('programs.html', programs=programs, category=category)

@app.route('/program/<int:id>')
def program_detail(id):
    program = TrainingProgram.query.get_or_404(id)
    related = TrainingProgram.query.filter_by(category=program.category).filter(TrainingProgram.id != id).limit(3).all()
    return render_template('program_detail.html', program=program, related=related)

@app.route('/supplements')
def supplements():
    supplements = Supplement.query.all()
    return render_template('supplements.html', supplements=supplements)

@app.route('/articles/<category>')
def articles(category):
    articles = Article.query.filter_by(category=category).order_by(Article.created_at.desc()).all()
    return render_template('articles.html', articles=articles, category=category)

@app.route('/article/<int:id>')
def article_detail(id):
    article = Article.query.get_or_404(id)
    related = Article.query.filter_by(category=article.category).filter(Article.id != id).limit(3).all()
    return render_template('article_detail.html', article=article, related=related)

@app.route('/calculators')
def calculators():
    return render_template('calculators.html')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return render_template('search.html', results=None)

    exercises = Exercise.query.filter(Exercise.name.ilike(f'%{query}%') | 
                                     Exercise.description.ilike(f'%{query}%')).all()
    nutrition = Nutrition.query.filter(Nutrition.title.ilike(f'%{query}%') | 
                                      Nutrition.description.ilike(f'%{query}%')).all()
    articles = Article.query.filter(Article.title.ilike(f'%{query}%') | 
                                   Article.content.ilike(f'%{query}%')).all()

    return render_template('search.html', 
                           query=query,
                           exercises=exercises,
                           nutrition=nutrition,
                           articles=articles)

@app.route('/videos')
def videos():
    exercises_with_videos = Exercise.query.filter(Exercise.video_url.isnot(None)).all()
    return render_template('videos.html', exercises=exercises_with_videos)

@app.route('/custom-plan-generator')
def custom_plan_generator():
    return render_template('custom_plan_generator.html')

@app.route('/generate-custom-plan', methods=['POST'])
def generate_custom_plan():
    plan_type = request.form.get('plan_type')
    goal = request.form.get('goal')
    level = request.form.get('level')
    gender = request.form.get('gender')
    age = request.form.get('age')
    weight = request.form.get('weight')
    days = request.form.get('days')
    height = request.form.get('height')
    health_limitations = request.form.get('health_limitations')
    
    # Store data in session for persistence
    session['plan_data'] = {
        'plan_type': plan_type,
        'goal': goal,
        'level': level,
        'gender': gender,
        'age': age,
        'weight': weight,
        'height': height,
        'days': days,
        'health_limitations': health_limitations
    }
    
    # Debug info
    print(f"Received form data: plan_type={plan_type}, goal={goal}, level={level}, gender={gender}, age={age}, weight={weight}, height={height}, days={days}")
    
    # Get display names for goal and level
    goal_name = {
        'muscle_gain': 'بناء العضلات',
        'fat_loss': 'حرق الدهون',
        'fitness': 'تحسين اللياقة',
        'strength': 'زيادة القوة'
    }.get(goal, goal)
    
    level_name = {
        'beginner': 'مبتدئ',
        'intermediate': 'متوسط',
        'advanced': 'متقدم'
    }.get(level, level)
    
    try:
        # Importar funciones de cálculo científico
        from fitness_calculator import calculate_bmr, calculate_tdee, adjust_calories_for_goal, calculate_macros
        from health_restrictions import analyze_health_restrictions
        
        # Variable to store generated data
        plan_data = {}
        
        # Analizar restricciones de salud
        health_info = {
            'age': age,
            'conditions': [],
            'injuries': [],
            'medications': [],
            'diet_restrictions': []
        }
        
        if health_limitations:
            # Extraer palabras clave de las limitaciones
            keywords = health_limitations.lower().split()
            
            # Clasificar en categorías
            for kw in keywords:
                if kw in ['rodilla', 'knee', 'espalda', 'back', 'hombro', 'shoulder']:
                    health_info['injuries'].append(kw)
                elif kw in ['diabetes', 'hipertensión', 'hypertension', 'asma', 'asthma', 'thyroid']:
                    health_info['conditions'].append(kw)
                elif kw in ['vegetariano', 'vegetarian', 'vegano', 'vegan', 'celiaco', 'celiac']:
                    health_info['diet_restrictions'].append(kw)
        
        health_recommendations = analyze_health_restrictions(health_info)
        
        if plan_type == 'workout':
            if not days:
                days = "3"  # default value
            
            # Incluir recomendaciones de salud en el plan
            workout_modifications = None
            if health_recommendations and 'workout_modifications' in health_recommendations:
                workout_modifications = health_recommendations['workout_modifications']
                
            plan_data = generate_ai_workout_plan(
                goal=goal,
                level=level,
                days_per_week=int(days),
                gender=gender,
                age=age,
                weight=weight,
                limitations=health_limitations
            )
            
            # إذا كان هناك خطأ في البيانات المستلمة
            if not isinstance(plan_data.get('plan'), (list, dict)):
                plan_data = generate_default_workout_plan(goal, level, int(days))
                flash('تم إنشاء خطة افتراضية لك.', 'info')
            
            # Añadir recomendaciones de salud al plan
            if workout_modifications and isinstance(plan_data, dict):
                if 'tips' not in plan_data:
                    plan_data['tips'] = []
                plan_data['health_recommendations'] = workout_modifications
            
            # Format output for better display
            formatted_plan = format_workout_plan(plan_data, goal_name, level_name, gender, age, weight, days)
            plan_data = formatted_plan
            
        elif plan_type == 'nutrition':  # Changed from else to explicit check
            try:
                if not days:
                    days = "4"  # default value for nutrition plan
                
                # Calculate calories using scientific formula if we have height and weight
                calories = None
                macros = None
                if weight and height and age:
                    try:
                        weight_float = float(weight)
                        height_float = float(height)
                        age_int = int(age)
                        
                        bmr = calculate_bmr(gender, weight_float, height_float, age_int)
                        activity_level = 'sedentary' if level == 'beginner' else 'moderate' if level == 'intermediate' else 'active'
                        tdee = calculate_tdee(bmr, activity_level)
                        calories = adjust_calories_for_goal(tdee, goal)
                        macros = calculate_macros(calories, goal)
                        
                        print(f"Calculated TDEE: {tdee}, Adjusted calories: {calories}")
                    except Exception as calc_error:
                        print(f"Error in calorie calculation: {str(calc_error)}")
                
                # Incluir recomendaciones nutricionales basadas en salud
                nutrition_recommendations = None
                if health_recommendations and 'nutrition_recommendations' in health_recommendations:
                    nutrition_recommendations = health_recommendations['nutrition_recommendations']
                
                print(f"Generating nutrition plan with days={days}")
                plan_data = generate_ai_meal_plan(
                    goal=goal,
                    gender=gender,
                    age=age,
                    activity_level=level,
                    weight=weight,
                    height=height
                )
                
                # Print debug info
                print(f"Nutrition plan data keys: {plan_data.keys() if isinstance(plan_data, dict) else 'Not a dict'}")
                
                # إذا كان هناك خطأ في البيانات المستلمة
                if not plan_data or (not isinstance(plan_data.get('plan'), (list, dict)) and not any(key in plan_data for key in ['calories', 'meals'])):
                    print("Using default meal plan")
                    plan_data = generate_default_meal_plan(goal, gender, age, level)
                    flash('تم إنشاء خطة غذائية افتراضية لك.', 'info')
                
                # Utilizar calorías calculadas si están disponibles
                if calories and macros and isinstance(plan_data, dict):
                    plan_data['calories'] = round(calories)
                    plan_data['protein'] = macros['protein']
                    plan_data['protein_percent'] = macros['protein_percent']
                    plan_data['carbs'] = macros['carbs']
                    plan_data['carbs_percent'] = macros['carbs_percent']
                    plan_data['fat'] = macros['fat']
                    plan_data['fat_percent'] = macros['fat_percent']
                
                # Añadir recomendaciones de salud al plan
                if nutrition_recommendations and isinstance(plan_data, dict):
                    if 'tips' not in plan_data:
                        plan_data['tips'] = []
                    plan_data['health_recommendations'] = nutrition_recommendations
                
                # Format output for better display
                formatted_plan = format_nutrition_plan(plan_data, goal_name, level_name, gender, age, weight, days)
                plan_data = formatted_plan
                
            except Exception as meal_error:
                print(f"Error in meal plan generation: {str(meal_error)}")
                plan_data = generate_default_meal_plan(goal, gender, age, level)
                flash('حدث خطأ أثناء إنشاء النظام الغذائي. تم إنشاء خطة افتراضية.', 'warning')
                
                # Format default plan too
                formatted_plan = format_nutrition_plan(plan_data, goal_name, level_name, gender, age, weight, days)
                plan_data = formatted_plan
                
        else:
            raise ValueError(f"نوع خطة غير معروف: {plan_type}")
        
        prompt = build_prompt(plan_type, goal, level, gender, age, weight, days)
        return render_template('hf_plan_result.html', plan=plan_data, plan_type=plan_type, prompt=prompt)
                             
    except Exception as e:
        print(f"Error generating plan: {str(e)}")
        flash(f'حدث خطأ أثناء إنشاء الخطة. الرجاء المحاولة مرة أخرى. السبب: {str(e)}', 'error')
        return redirect(url_for('custom_plan_generator'))

@app.route('/article-generator')
def article_generator():
    return render_template('article_generator.html')

@app.route('/api/generate-workout-plan', methods=['POST'])
def api_generate_workout_plan():
    """API endpoint to generate AI-powered workout plans"""
    try:
        data = request.get_json()
        goal = data.get('goal')
        level = data.get('level')
        days_per_week = int(data.get('days'))
        
        # Get additional personal information
        gender = data.get('gender')
        age = data.get('age')
        weight = data.get('weight')
        limitations = data.get('limitations')
        
        # Generate AI workout plan with personal information
        plan_data = generate_ai_workout_plan(
            goal=goal, 
            level=level, 
            days_per_week=days_per_week,
            gender=gender,
            age=age,
            weight=weight,
            limitations=limitations
        )
        
        return jsonify(plan_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/generate-meal-plan', methods=['POST'])
def api_generate_meal_plan():
    """API endpoint to generate AI-powered meal plans"""
    try:
        data = request.get_json()
        
        # Basic parameters
        goal = data.get('goal', 'any')
        diet_type = data.get('diet_type', 'any')
        meal_type = data.get('meal_type', 'any')
        health_conditions = data.get('health_conditions', 'none')
        
        # User info - default values if not provided
        gender = data.get('gender', 'male')
        age = data.get('age', 30)
        activity_level = data.get('activity_level', 'moderate') 
        weight = data.get('weight')
        height = data.get('height')
        
        # Ingredient lists
        all_ingredients = data.get('ingredients', [])
        proteins = data.get('proteins', [])
        carbs = data.get('carbs', [])
        vegetables = data.get('vegetables', [])
        extras = data.get('extras', [])
        
        # Enhanced parameters for personalization
        meals_per_day = data.get('meals_per_day', 3)
        food_allergies = health_conditions if health_conditions != 'none' else None
        
        print(f"Generating meal plan with goal={goal}, diet={diet_type}, meal_type={meal_type}")
        print(f"Ingredients: {', '.join(all_ingredients)}")

        # Logic to handle specific meal type requests
        single_meal_response = False
        specific_meal_name = None
        
        if meal_type != 'any':
            single_meal_response = True
            specific_meal_name = {
                'breakfast': 'وجبة الفطور',
                'lunch': 'وجبة الغداء',
                'dinner': 'وجبة العشاء',
                'snack': 'وجبة خفيفة',
                'pre_workout': 'وجبة ما قبل التمرين',
                'post_workout': 'وجبة ما بعد التمرين'
            }.get(meal_type, 'وجبة')
        
        # If this is a request for a single meal with ingredients
        if single_meal_response and all_ingredients:
            # Use custom function to generate specific meal
            from meal_generator import generate_meal_with_ingredients
            
            try:
                # Try to use specialized meal generator
                meal_data = generate_meal_with_ingredients(
                    ingredients=all_ingredients,
                    meal_type=meal_type,
                    diet_type=diet_type,
                    goal=goal,
                    health_conditions=health_conditions
                )
                return jsonify(meal_data)
            except (ImportError, Exception) as e:
                print(f"Error using specialized meal generator: {str(e)}")
                # Fall back to regular meal plan generation
                pass
        
        # Otherwise, generate a full meal plan
        meal_plan_data = generate_ai_meal_plan(
            goal=goal,
            gender=gender,
            age=age,
            activity_level=activity_level,
            weight=weight,
            height=height,
            diet_type=diet_type,
            meals_per_day=meals_per_day,
            food_allergies=food_allergies
        )
        
        # If it's a single meal request, extract just that meal type or create one
        if single_meal_response:
            # Try to find a meal of the requested type
            matching_meal = None
            if "meals" in meal_plan_data:
                for meal in meal_plan_data["meals"]:
                    meal_name = meal.get("name", "").lower()
                    if (meal_type in meal_name or
                        (meal_type == "breakfast" and "فطور" in meal_name) or
                        (meal_type == "lunch" and "غداء" in meal_name) or
                        (meal_type == "dinner" and "عشاء" in meal_name) or
                        (meal_type == "snack" and "خفيفة" in meal_name) or
                        (meal_type == "pre_workout" and "قبل التمرين" in meal_name) or
                        (meal_type == "post_workout" and "بعد التمرين" in meal_name)):
                        matching_meal = meal
                        break
            
            # If no matching meal found, create one based on ingredients
            if not matching_meal:
                from meal_generator import create_default_meal
                matching_meal = create_default_meal(
                    meal_type=meal_type,
                    ingredients=all_ingredients,
                    diet_type=diet_type,
                    goal=goal
                )
            
            # Format response for a single meal
            response_data = {
                "meals": [matching_meal]
            }
            
            # Include macro info if available in the original plan
            if "calories" in meal_plan_data:
                response_data["calories"] = meal_plan_data["calories"]
            if "protein" in meal_plan_data:
                response_data["protein"] = meal_plan_data["protein"]
            if "carbs" in meal_plan_data:
                response_data["carbs"] = meal_plan_data["carbs"]
            if "fat" in meal_plan_data:
                response_data["fat"] = meal_plan_data["fat"]
                
            return jsonify(response_data)
        
        return jsonify(meal_plan_data)
        
    except Exception as e:
        print(f"Error generating meal plan: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/generate-article', methods=['POST'])
def api_generate_article():
    """API endpoint to generate AI-powered articles based on user goals"""
    try:
        data = request.get_json()
        topic = data.get('topic')
        subtopic = data.get('subtopic')
        
        # Generate AI article
        article_data = generate_ai_article(topic, subtopic)
        
        return jsonify(article_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# Filtro personalizado para formatear fechas
@app.template_filter('format_date')
def format_date(date):
    if date is None:
        return ""
    return date.strftime('%d/%m/%Y')

# Chatbot route
@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.json
    user_message = data.get('message', '')
    conversation_history = data.get('conversation_history', [])
    session_id = data.get('session_id')
    user_id = data.get('user_id', 'anonymous')
    
    # Test if this is just checking AI availability
    if user_message == 'test_ai_availability':
        try:
            from ai_helper import get_ai_response
            # Just test if module is available and working
            return jsonify({'response': 'AI is available'})
        except Exception as e:
            print(f"AI Unavailable: {e}")
            return jsonify({'error': 'ai_unavailable'})
    
    # Use AI-powered response if available, fallback to rule-based
    try:
        from ai_helper import get_ai_response, enhance_chatbot_response
        
        # Get AI response and enhance it for display
        raw_response = get_ai_response(user_message, conversation_history, session_id)
        response = enhance_chatbot_response(raw_response)
    except Exception as e:
        print(f"Error using AI response: {e}")
        # Return an error if this is a request specifically expecting AI
        if any(keyword in user_message.lower() for keyword in ['ذكاء', 'ai', 'gpt']):
            return jsonify({
                'error': 'ai_unavailable',
                'message': 'المساعد الذكي غير متاح حالياً. يرجى طرح أسئلة بسيطة أو زيارة قسم التواصل معنا للمزيد من المساعدة.'
            })
        # Fallback to rule-based responses
        response = get_chatbot_response(user_message)
    
    return jsonify({'response': response})

# Chatbot response logic
def get_chatbot_response(message):
    message = message.lower()
    
    # Helper function to check if any keyword is in the message
    def contains_any(keywords):
        return any(keyword in message for keyword in keywords)
    
    # Basic responses based on keywords
    greeting_keywords = ['مرحبا', 'اهلا', 'السلام', 'صباح', 'مساء', 'هاي', 'هلا', 'هاى', 'مرحباً', 'أهلاً', 'أهلا', 'هلو']
    if contains_any(greeting_keywords):
        greetings = [
            'مرحباً! كيف يمكنني مساعدتك اليوم؟',
            'أهلاً بك في باور جيم! كيف أستطيع مساعدتك؟',
            'مرحباً بك! أنا هنا للإجابة على استفساراتك حول التمارين والتغذية والبرامج التدريبية.',
            'أهلاً! هل تبحث عن معلومات حول التمارين أو التغذية أو برامج التدريب؟'
        ]
        import random
        return random.choice(greetings)
    
    elif any(word in message for word in ['تمارين', 'تمرين', 'تدريب']):
        if 'مبتدئ' in message or 'مبتدئين' in message:
            return 'للمبتدئين، ننصح بالبدء بتمارين الوزن الخفيف والتركيز على التقنية الصحيحة. يمكنك زيارة قسم "تمارين للمبتدئين" في موقعنا.'
        elif 'منزل' in message or 'البيت' in message or 'المنزل' in message:
            return 'لدينا مجموعة رائعة من التمارين المنزلية التي لا تحتاج إلى معدات. تفضل بزيارة قسم "تمارين منزلية" في موقعنا.'
        elif 'تضخيم' in message or 'عضلات' in message:
            return 'لبناء العضلات، ركز على تمارين القوة مع وزن ثقيل وعدد تكرارات أقل. زر قسم "تمارين تضخيم عضلي" لمزيد من المعلومات.'
        elif 'تنشيف' in message or 'حرق' in message or 'دهون' in message:
            return 'لحرق الدهون، ننصح بمزيج من تمارين الكارديو وتمارين المقاومة. زر قسم "تمارين تنشيف" لمعرفة المزيد.'
        else:
            return 'لدينا مجموعة متنوعة من التمارين لجميع مستويات اللياقة والأهداف. ما هو هدفك تحديداً؟'
    
    elif any(word in message for word in ['غذاء', 'تغذية', 'أكل', 'طعام', 'رجيم', 'دايت']):
        if 'تخسيس' in message or 'تنحيف' in message or 'وزن' in message:
            return 'للتخسيس، ننصح بنظام غذائي متوازن مع عجز سعرات حراري معتدل. زر قسم "رجيم للتخسيس" لخطط غذائية مفصلة.'
        elif 'عضلات' in message or 'تضخيم' in message:
            return 'لبناء العضلات، تحتاج إلى زيادة البروتين في نظامك الغذائي مع فائض سعرات حراري معتدل. زر قسم "وجبات رياضية" لمعرفة المزيد.'
        elif 'قبل' in message and ('تمرين' in message or 'تدريب' in message):
            return 'قبل التمرين، تناول وجبة تحتوي على الكربوهيدرات والبروتين بحوالي 1-2 ساعة قبل التمرين. زر قسم "أكل قبل وبعد التمرين" لمزيد من المعلومات.'
        elif 'بعد' in message and ('تمرين' in message or 'تدريب' in message):
            return 'بعد التمرين، تناول وجبة غنية بالبروتين والكربوهيدرات خلال 30-60 دقيقة لتعزيز التعافي. زر قسم "أكل قبل وبعد التمرين" لمزيد من المعلومات.'
        else:
            return 'التغذية السليمة هي أساس النجاح في التمارين. ما هو هدفك الغذائي تحديداً؟'
    
    elif any(word in message for word in ['مكملات', 'بروتين', 'كرياتين']):
        if 'بروتين' in message:
            return 'بروتين مصل اللبن هو مكمل شائع يساعد في بناء العضلات والتعافي. ينصح بتناوله بعد التمرين مباشرة.'
        elif 'كرياتين' in message:
            return 'الكرياتين يساعد في زيادة القوة والأداء خلال تمارين المقاومة. الجرعة الموصى بها هي 3-5 غرام يومياً.'
        else:
            return 'لدينا معلومات عن مختلف المكملات الغذائية في قسم "مكملات غذائية". ما هو المكمل الذي تريد معرفة المزيد عنه؟'
    
    elif any(word in message for word in ['برنامج', 'جدول', 'خطة']):
        if 'مبتدئ' in message:
            return 'للمبتدئين، ننصح ببرنامج 3 أيام في الأسبوع للتعود على التمارين. زر قسم "برنامج 3 أيام للمبتدئ" لمعرفة المزيد.'
        elif 'تضخيم' in message or 'ضخامة' in message:
            return 'لبناء العضلات، جرب برنامج تقسيم عضلي مع 4-5 أيام تدريب في الأسبوع. زر قسم "جدول ضخامة" لمعرفة المزيد.'
        elif 'تنشيف' in message or 'تخسيس' in message:
            return 'لحرق الدهون، ننصح ببرنامج يجمع بين تمارين المقاومة والكارديو. زر قسم "جدول تنشيف" لمعرفة المزيد.'
        elif 'منزل' in message or 'البيت' in message:
            return 'لدينا برامج تدريب منزلية لا تحتاج إلى معدات كثيرة. زر قسم "جدول تمرين في المنزل" لمعرفة المزيد.'
        else:
            return 'لدينا مجموعة متنوعة من برامج التدريب لمختلف الأهداف. ما هو هدفك تحديداً؟'
    
    elif 'حاسبة' in message or 'حساب' in message:
        if 'سعرات' in message or 'كالوري' in message:
            return 'يمكنك استخدام حاسبة السعرات الحرارية في قسم "حاسبات رياضية" لتقدير احتياجاتك اليومية من السعرات.'
        elif 'كتلة' in message or 'bmi' in message:
            return 'يمكنك حساب مؤشر كتلة الجسم (BMI) في قسم "حاسبات رياضية" لتقييم وزنك بالنسبة لطولك.'
        else:
            return 'لدينا عدة حاسبات رياضية في قسم "حاسبات رياضية" تساعدك في تتبع تقدمك وتحديد أهدافك.'
    
    elif 'تواصل' in message or 'اتصال' in message:
        return 'يمكنك التواصل معنا عبر صفحة "تواصل معنا" أو عبر وسائل التواصل الاجتماعي المذكورة في أسفل الصفحة.'
    
    elif 'شكرا' in message or 'شكراً' in message:
        return 'عفواً! سعدت بمساعدتك. هل هناك أي شيء آخر يمكنني مساعدتك به؟'
    
    else:
        return 'عذراً، لم أفهم سؤالك. هل يمكنك إعادة صياغته أو طرح سؤال آخر عن التمارين، التغذية، المكملات الغذائية، أو برامج التدريب؟'

# دوال افتراضية لتوليد الخطط
def generate_default_meal_plan(goal, gender, age, activity_level):
    """Generate a default meal plan when API is not available"""
    calories = 2000 if gender == 'male' else 1800
    
    # Adjust for goal
    if goal == 'muscle_gain':
        calories += 300
        protein_percent = 35
        carbs_percent = 45
        fat_percent = 20
    elif goal == 'fat_loss':
        calories -= 300
        protein_percent = 40
        carbs_percent = 30
        fat_percent = 30
    else:  # maintenance or general fitness
        protein_percent = 30
        carbs_percent = 40
        fat_percent = 30
    
    # Calculate macros
    protein = round((calories * (protein_percent/100)) / 4)  # 4 calories per gram of protein
    carbs = round((calories * (carbs_percent/100)) / 4)      # 4 calories per gram of carbs
    fat = round((calories * (fat_percent/100)) / 9)          # 9 calories per gram of fat
    
    # Create simple meal plan
    meals = [
        {
            "name": "وجبة الإفطار",
            "foods": [
                {"name": "شوفان بالحليب", "portion": "كوب واحد", "calories": "300"},
                {"name": "بيض مسلوق", "portion": "2 حبة", "calories": "140"},
                {"name": "موز", "portion": "حبة واحدة", "calories": "100"}
            ],
            "tip": "تناول الإفطار خلال ساعة من الاستيقاظ لتعزيز التمثيل الغذائي"
        },
        {
            "name": "وجبة الغداء",
            "foods": [
                {"name": "صدر دجاج مشوي", "portion": "150 غرام", "calories": "250"},
                {"name": "أرز بني", "portion": "كوب واحد", "calories": "200"},
                {"name": "سلطة خضراء", "portion": "طبق متوسط", "calories": "50"}
            ],
            "tip": "تناول البروتين مع الكربوهيدرات المعقدة للحصول على طاقة مستدامة"
        },
        {
            "name": "وجبة العشاء",
            "foods": [
                {"name": "سمك مشوي", "portion": "150 غرام", "calories": "200"},
                {"name": "خضروات مشوية", "portion": "كوب واحد", "calories": "80"}
            ],
            "tip": "تناول العشاء قبل النوم بثلاث ساعات على الأقل"
        }
    ]
    
    # Add goal-specific snack
    if goal == 'muscle_gain':
        meals.append({
            "name": "وجبة ما بعد التمرين",
            "foods": [
                {"name": "شيك بروتين", "portion": "كوب واحد", "calories": "150"},
                {"name": "موز", "portion": "حبة واحدة", "calories": "100"}
            ],
            "tip": "تناول البروتين والكربوهيدرات بعد التمرين مباشرة لتعزيز بناء العضلات"
        })
    
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

def generate_default_workout_plan(goal, level, days_per_week):
    """Generate a default workout plan when API is not available"""
    
    # Basic workout templates
    beginner_workout = [
        {"focus": "تمارين الجسم كامل", "exercises": [
            {"name": "تمرين القرفصاء", "sets": "3", "reps": "12", "rest": "60 ثانية"},
            {"name": "تمرين الضغط", "sets": "3", "reps": "10", "rest": "60 ثانية"},
            {"name": "تمرين السحب", "sets": "3", "reps": "10", "rest": "60 ثانية"}
        ]}
    ]
    
    intermediate_workout = [
        {"focus": "تمارين الصدر والظهر", "exercises": [
            {"name": "بنش بريس", "sets": "4", "reps": "12", "rest": "90 ثانية"},
            {"name": "تمرين السحب", "sets": "4", "reps": "12", "rest": "90 ثانية"}
        ]},
        {"focus": "تمارين الأرجل", "exercises": [
            {"name": "تمرين القرفصاء", "sets": "4", "reps": "12", "rest": "90 ثانية"},
            {"name": "تمرين الدفع الأمامي", "sets": "4", "reps": "12", "rest": "90 ثانية"}
        ]}
    ]
    
    # Create workout plan based on level and goal
    workout_plan = []
    
    if level == "beginner":
        workout_plan = beginner_workout * days_per_week
    else:
        workout_plan = intermediate_workout
        
    # Limit to requested days
    workout_plan = workout_plan[:days_per_week]
    
    return {"plan": workout_plan}

def build_prompt(plan_type, goal, level, gender, age, weight, days):
    # Translate goal and level to Arabic for better context
    goal_ar = {
        'muscle_gain': 'بناء العضلات',
        'fat_loss': 'حرق الدهون',
        'fitness': 'تحسين اللياقة البدنية',
        'strength': 'زيادة القوة'
    }.get(goal, goal)
    
    level_ar = {
        'beginner': 'مبتدئ',
        'intermediate': 'متوسط',
        'advanced': 'متقدم'
    }.get(level, level)
    
    gender_ar = 'ذكر' if gender == 'male' else 'أنثى'
    
    if plan_type == "workout":
        prompt = f"""
إنشاء خطة تدريب تفصيلية لمدة {days} أيام لشخص {gender_ar} عمره {age} سنة بهدف {goal_ar}.
مستوى اللياقة البدنية: {level_ar}
الوزن: {weight} كجم

يجب أن تتضمن خطة التدريب:
1. جدول زمني لكل يوم من أيام الأسبوع
2. تمارين محددة مع عدد المجموعات والتكرارات
3. فترات الراحة وأيام الراحة
4. توصيات الإحماء والتهدئة
5. توصيات التقدم والتطور

المخرجات:
- خطة تفصيلية لكل يوم تدريب
- إرشادات تقنية لكل تمرين مع صور توضيحية
- نصائح للمبتدئين لتجنب الإصابات
- خطة تدريجية للتقدم خلال الأسابيع القادمة
"""
    elif plan_type == "nutrition":
        prompt = f"""
إنشاء خطة غذائية تفصيلية لمدة {days} أيام لشخص {gender_ar} عمره {age} سنة بهدف {goal_ar}.
مستوى النشاط البدني: {level_ar}
الوزن: {weight} كجم

يجب أن تتضمن الخطة الغذائية:
1. أهداف السعرات الحرارية اليومية
2. توزيع العناصر الغذائية (البروتين، الكربوهيدرات، الدهون)
3. 3 وجبات رئيسية يومياً بالإضافة إلى وجبات خفيفة
4. اقتراحات طعام محددة مع الكميات التقريبية
5. توصيات الترطيب وشرب الماء

المخرجات:
- خطة غذائية مفصلة لكل يوم
- قائمة تسوق أسبوعية
- بدائل صحية للوجبات السريعة
- نصائح لتحضير الوجبات مسبقاً
- تعديلات مقترحة بناءً على التقدم
"""
    else:
        prompt = "لم يتم تحديد نوع الخطة."
    
    return prompt

# Helper functions to format the plan outputs
def format_workout_plan(plan_data, goal_name, level_name, gender, age, weight, days):
    """Format workout plan data for better display"""
    gender_ar = 'ذكر' if gender == 'male' else 'أنثى'
    
    # Start with the HTML header
    html = f"""<div class="plan-header mb-4">
    <div class="alert alert-success">
        <strong>معلومات الخطة:</strong> خطة تدريب لـ {gender_ar}، العمر: {age} سنة، الوزن: {weight} كجم، الهدف: {goal_name}، المستوى: {level_name}، عدد الأيام: {days}
    </div>
</div>"""
    
    # Agregar recomendaciones de salud si existen
    if isinstance(plan_data, dict) and 'health_recommendations' in plan_data:
        html += """<div class="health-recommendations mb-4">
    <div class="card border-warning">
        <div class="card-header bg-warning text-dark">
            <h4 class="mb-0">توصيات صحية مخصصة</h4>
        </div>
        <div class="card-body">
            <ul class="list-group list-group-flush">"""
        
        for recommendation in plan_data['health_recommendations']:
            html += f"""
                <li class="list-group-item">
                    <i class="bi bi-shield-check me-2 text-warning"></i>{recommendation}
                </li>"""
            
        html += """
            </ul>
        </div>
    </div>
</div>"""
    
    # If plan is in dictionary format
    if isinstance(plan_data, dict) and 'plan' in plan_data:
        workout_plan = plan_data['plan']
        
        html += "<div class='workout-days'>"
        
        # For each day in the plan
        for i, day in enumerate(workout_plan):
            day_number = i + 1
            
            html += f"""<div class="workout-day mb-4">
    <div class="card border-success">
        <div class="card-header bg-success text-white">
            <h4 class="mb-0">اليوم {day_number}: {day.get('focus', '')}</h4>
        </div>
        <div class="card-body">"""
            
            # Add exercises
            if 'exercises' in day:
                html += """<table class="table table-hover">
    <thead class="table-light">
        <tr>
            <th>التمرين</th>
            <th>المجموعات</th>
            <th>التكرارات</th>
            <th>الراحة</th>
        </tr>
    </thead>
    <tbody>"""
                
                for exercise in day['exercises']:
                    html += f"""<tr>
        <td>{exercise.get('name', '')}</td>
        <td>{exercise.get('sets', '')}</td>
        <td>{exercise.get('reps', '')}</td>
        <td>{exercise.get('rest', '')}</td>
    </tr>"""
                
                html += """</tbody>
</table>"""
            
            html += """</div>
    </div>
</div>"""
        
        html += "</div>"
        
        # Add tips section if available
        if 'tips' in plan_data:
            html += f"""<div class="tips mt-4">
    <div class="card border-info">
        <div class="card-header bg-info text-white">
            <h4 class="mb-0">نصائح ومعلومات إضافية</h4>
        </div>
        <div class="card-body">
            <p>{plan_data['tips']}</p>
        </div>
    </div>
</div>"""
    
    else:
        # If plan is just a string, display it directly
        html += f"<div class='plan-content'>{plan_data}</div>"
    
    return html

def format_nutrition_plan(plan_data, goal_name, level_name, gender, age, weight, days):
    """Format nutrition plan data for better display"""
    gender_ar = 'ذكر' if gender == 'male' else 'أنثى'
    
    # Start with the HTML header
    html = f"""<div class="plan-header mb-4">
    <div class="alert alert-primary">
        <strong>معلومات الخطة:</strong> خطة غذائية لـ {gender_ar}، العمر: {age} سنة، الوزن: {weight} كجم، الهدف: {goal_name}، مستوى النشاط: {level_name}
    </div>
</div>"""
    
    # Agregar recomendaciones de salud si existen
    if isinstance(plan_data, dict) and 'health_recommendations' in plan_data:
        html += """<div class="health-recommendations mb-4">
    <div class="card border-warning">
        <div class="card-header bg-warning text-dark">
            <h4 class="mb-0">توصيات غذائية مخصصة</h4>
        </div>
        <div class="card-body">
            <ul class="list-group list-group-flush">"""
        
        for recommendation in plan_data['health_recommendations']:
            html += f"""
                <li class="list-group-item">
                    <i class="bi bi-shield-check me-2 text-warning"></i>{recommendation}
                </li>"""
            
        html += """
            </ul>
        </div>
    </div>
</div>"""
    
    # Add caloric and macronutrient information if available
    if isinstance(plan_data, dict) and all(key in plan_data for key in ['calories', 'protein', 'carbs', 'fat']):
        html += f"""<div class="macros mb-4">
    <div class="card border-primary">
        <div class="card-header bg-primary text-white">
            <h4 class="mb-0">الاحتياجات اليومية من السعرات والعناصر الغذائية</h4>
        </div>
        <div class="card-body">
            <div class="row text-center">
                <div class="col-md-3 mb-3">
                    <div class="p-3 rounded bg-light">
                        <h2 class="text-primary">{plan_data['calories']}</h2>
                        <p class="mb-0">سعرة حرارية</p>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="p-3 rounded bg-light">
                        <h2 class="text-primary">{plan_data['protein']}g</h2>
                        <p class="mb-0">بروتين ({plan_data.get('proteinPercent', '?')}%)</p>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="p-3 rounded bg-light">
                        <h2 class="text-primary">{plan_data['carbs']}g</h2>
                        <p class="mb-0">كربوهيدرات ({plan_data.get('carbsPercent', '?')}%)</p>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="p-3 rounded bg-light">
                        <h2 class="text-primary">{plan_data['fat']}g</h2>
                        <p class="mb-0">دهون ({plan_data.get('fatPercent', '?')}%)</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>"""
    
    # Add meal plan if available
    if isinstance(plan_data, dict) and 'meals' in plan_data:
        meals = plan_data['meals']
        
        html += "<div class='meals mb-4'>"
        
        for i, meal in enumerate(meals):
            html += f"""<div class="meal mb-3">
    <div class="card border-primary">
        <div class="card-header bg-primary text-white">
            <h4 class="mb-0">{meal.get('name', f'الوجبة {i+1}')}</h4>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-light">
                        <tr>
                            <th>الطعام</th>
                            <th>الكمية</th>
                            <th>السعرات الحرارية</th>
                        </tr>
                    </thead>
                    <tbody>"""
            
            if 'foods' in meal:
                for food in meal['foods']:
                    html += f"""<tr>
                        <td>{food.get('name', '')}</td>
                        <td>{food.get('portion', '')}</td>
                        <td>{food.get('calories', '')}</td>
                    </tr>"""
            
            html += """</tbody>
                </table>
            </div>"""
            
            if 'tip' in meal:
                html += f"""<div class="alert alert-light mt-3">
                <i class="fas fa-lightbulb text-warning me-2"></i> {meal['tip']}
            </div>"""
            
            html += """</div>
    </div>
</div>"""
        
        html += "</div>"
    
    # Add hydration section
    html += """<div class="hydration mb-4">
    <div class="card border-info">
        <div class="card-header bg-info text-white">
            <h4 class="mb-0">توصيات الترطيب</h4>
        </div>
        <div class="card-body">
            <div class="row align-items-center">
                <div class="col-md-2 text-center mb-3 mb-md-0">
                    <i class="fas fa-tint fa-4x text-info"></i>
                </div>
                <div class="col-md-10">
                    <p class="mb-1">اشرب 2-3 لتر من الماء يومياً موزعة على مدار اليوم</p>
                    <ul>
                        <li>تناول كوب من الماء فور الاستيقاظ</li>
                        <li>احمل زجاجة ماء معك طوال اليوم</li>
                        <li>تناول كوب من الماء قبل كل وجبة بـ 30 دقيقة</li>
                        <li>قلل من المشروبات التي تحتوي على الكافيين</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</div>"""
    
    return html

@app.route('/virtual-coach')
def virtual_coach():
    return render_template('chatbot.html')

@app.route('/meal-generator')
def meal_generator():
    return render_template('meal_generator.html')

@app.route('/body-analyzer')
def body_analyzer():
    return render_template('body_analyzer.html')

# Generator Control Panel routes
@app.route('/admin/workout-generator')
@admin_required
def admin_workout_generator():
    generator_data = {
        'generator_name': 'مولد خطط التدريب',
        'generator_type': 'workout',
        'status': 'نشط',
        'ai_model': 'gpt-3.5-turbo',
        'api_key': '••••••••',
        'max_tokens': 1500,
        'temperature': 0.7,
        'request_timeout': 60,
        'enable_cache': True,
        'fallback_to_local': True,
        'prompt_template': 'إنشاء خطة تدريب مخصصة ل{{goal}} بمستوى {{level}} لمدة {{days}} أيام في الأسبوع للجنس {{gender}} بعمر {{age}} سنة ووزن {{weight}} كجم.',
        'health_adjustments': 'مرضى السكري: تجنب التمارين عالية الشدة\nإصابات الركبة: تجنب تمارين القرفصاء العميقة',
        'forbidden_terms': 'هرمونات، منشطات، أدوية',
        'content_category': 'fitness_only',
        'safety_level': 'standard',
        'medical_disclaimer': True,
        'usage_count': 145,
        'avg_response_time': 3.2,
        'last_update': '2024-05-10',
        'usage_logs': [
            {'id': 1, 'timestamp': '2025-05-16 14:30', 'response_time': 2.8, 'success': True},
            {'id': 2, 'timestamp': '2025-05-15 10:15', 'response_time': 3.1, 'success': True},
            {'id': 3, 'timestamp': '2025-05-14 16:45', 'response_time': 4.2, 'success': False}
        ]
    }
    return render_template('admin/generator_control.html', **generator_data)

@app.route('/admin/nutrition-generator')
@admin_required
def admin_nutrition_generator():
    generator_data = {
        'generator_name': 'مولد خطط التغذية',
        'generator_type': 'nutrition',
        'status': 'نشط',
        'ai_model': 'gpt-4',
        'api_key': '••••••••',
        'max_tokens': 2000,
        'temperature': 0.6,
        'request_timeout': 90,
        'enable_cache': True,
        'fallback_to_local': True,
        'prompt_template': 'إنشاء خطة غذائية مخصصة ل{{goal}} للجنس {{gender}} بعمر {{age}} سنة ووزن {{weight}} كجم وطول {{height}} سم ومستوى نشاط {{activity_level}}.',
        'health_adjustments': 'مرضى السكري: تجنب الكربوهيدرات المكررة\nارتفاع ضغط الدم: تقليل الملح',
        'forbidden_terms': 'مكملات غذائية غير مرخصة، وصفات طبية',
        'content_category': 'health_only',
        'safety_level': 'strict',
        'medical_disclaimer': True,
        'usage_count': 120,
        'avg_response_time': 4.5,
        'last_update': '2024-05-12',
        'usage_logs': [
            {'id': 1, 'timestamp': '2025-05-16 13:20', 'response_time': 3.9, 'success': True},
            {'id': 2, 'timestamp': '2025-05-15 11:30', 'response_time': 4.2, 'success': True},
            {'id': 3, 'timestamp': '2025-05-14 09:45', 'response_time': 5.1, 'success': True}
        ]
    }
    return render_template('admin/generator_control.html', **generator_data)

@app.route('/admin/article-generator')
@admin_required
def admin_article_generator():
    generator_data = {
        'generator_name': 'مولد المقالات',
        'generator_type': 'article',
        'status': 'نشط',
        'ai_model': 'gpt-3.5-turbo',
        'api_key': '••••••••',
        'max_tokens': 3000,
        'temperature': 0.8,
        'request_timeout': 120,
        'enable_cache': True,
        'fallback_to_local': True,
        'prompt_template': 'إنشاء مقال عن {{topic}} وبالتحديد {{subtopic}} بنبرة {{tone}} وبطول تقريبي {{length}} كلمة.',
        'forbidden_terms': 'أسماء تجارية، ادعاءات مبالغ فيها',
        'content_category': 'general',
        'safety_level': 'standard',
        'medical_disclaimer': True,
        'usage_count': 75,
        'avg_response_time': 5.8,
        'last_update': '2024-05-08',
        'usage_logs': [
            {'id': 1, 'timestamp': '2025-05-16 15:40', 'response_time': 5.2, 'success': True},
            {'id': 2, 'timestamp': '2025-05-15 14:20', 'response_time': 6.1, 'success': True},
            {'id': 3, 'timestamp': '2025-05-14 12:30', 'response_time': 5.7, 'success': True}
        ]
    }
    return render_template('admin/generator_control.html', **generator_data)

@app.route('/admin/meal-generator')
@admin_required
def admin_meal_generator():
    generator_data = {
        'generator_name': 'مولد الوجبات',
        'generator_type': 'meal',
        'status': 'نشط',
        'ai_model': 'local-model',
        'api_key': '',
        'max_tokens': 1200,
        'temperature': 0.7,
        'request_timeout': 45,
        'enable_cache': True,
        'fallback_to_local': False,
        'prompt_template': 'اقتراح وجبة صحية باستخدام المكونات التالية {{ingredients}} لوجبة {{meal_type}} بنمط {{cuisine}} ونظام غذائي {{diet_type}}.',
        'forbidden_terms': 'مكونات غير صحية، طرق طهي غير صحية',
        'content_category': 'health_only',
        'safety_level': 'moderate',
        'medical_disclaimer': True,
        'usage_count': 215,
        'avg_response_time': 1.8,
        'last_update': '2024-05-14',
        'usage_logs': [
            {'id': 1, 'timestamp': '2025-05-16 18:30', 'response_time': 1.5, 'success': True},
            {'id': 2, 'timestamp': '2025-05-16 17:15', 'response_time': 1.7, 'success': True},
            {'id': 3, 'timestamp': '2025-05-16 16:45', 'response_time': 2.0, 'success': True}
        ]
    }
    return render_template('admin/generator_control.html', **generator_data)

@app.route('/admin/chatbot')
@admin_required
def admin_chatbot():
    generator_data = {
        'generator_name': 'المدرب الافتراضي',
        'generator_type': 'chatbot',
        'status': 'نشط',
        'ai_model': 'gpt-4',
        'api_key': '••••••••',
        'max_tokens': 800,
        'temperature': 0.5,
        'request_timeout': 30,
        'enable_cache': True,
        'fallback_to_local': True,
        'prompt_template': 'أنت مدرب افتراضي للياقة البدنية والتغذية. ساعد المستخدم في أسئلته حول {{topic}}.',
        'personality_settings': 'محفز، حازم، صبور، دقيق',
        'forbidden_terms': 'تشخيصات طبية، وصفات علاجية',
        'content_category': 'fitness_only',
        'safety_level': 'strict',
        'medical_disclaimer': True,
        'usage_count': 325,
        'avg_response_time': 2.1,
        'last_update': '2024-05-15',
        'usage_logs': [
            {'id': 1, 'timestamp': '2025-05-16 20:30', 'response_time': 1.8, 'success': True},
            {'id': 2, 'timestamp': '2025-05-16 19:45', 'response_time': 2.2, 'success': True},
            {'id': 3, 'timestamp': '2025-05-16 19:10', 'response_time': 2.0, 'success': True}
        ]
    }
    return render_template('admin/generator_control.html', **generator_data)

@app.route('/admin/body-analyzer')
@admin_required
def admin_body_analyzer():
    generator_data = {
        'generator_name': 'محلل الجسم من الصورة',
        'generator_type': 'body_analyzer',
        'status': 'قريباً',
        'ai_model': 'custom',
        'api_key': '••••••••',
        'max_tokens': 1000,
        'temperature': 0.5,
        'request_timeout': 60,
        'enable_cache': False,
        'fallback_to_local': False,
        'prompt_template': 'تحليل جسم الشخص من الصورة وتقديم توصيات تدريبية وغذائية مناسبة له حسب شكل الجسم.',
        'forbidden_terms': 'تعليقات سلبية على الجسم، نقد غير بناء',
        'content_category': 'fitness_only',
        'safety_level': 'strict',
        'medical_disclaimer': True,
        'usage_count': 0,
        'avg_response_time': 0,
        'last_update': '2024-05-01',
        'usage_logs': []
    }
    return render_template('admin/generator_control.html', **generator_data)

# استقبال طلبات اختبار المولدات
@app.route('/admin/test-generator', methods=['POST'])
@admin_required
def test_generator():
    data = request.json
    generator_type = data.get('generator_type')
    test_params = data.get('params', {})
    
    # سيتم إضافة منطق الاختبار الفعلي هنا
    
    # نتيجة مثالية للاختبار
    result = {
        'success': True,
        'data': {
            'content': 'محتوى مولد بنجاح',
            'metadata': {
                'response_time': 2.5,
                'model_used': 'gpt-3.5-turbo',
                'timestamp': datetime.utcnow().isoformat()
            }
        }
    }
    
    return jsonify(result)

# حفظ إعدادات المولدات
@app.route('/admin/save-generator-settings', methods=['POST'])
@admin_required
def save_generator_settings():
    data = request.json
    generator_type = data.get('generator_type')
    settings = data.get('settings', {})
    
    # سيتم إضافة منطق حفظ الإعدادات الفعلي هنا
    
# إعداد ChromaDB
client = chromadb.Client(Settings(
    persist_directory="chroma_db"  # مسار حفظ البيانات
))

# إنشاء مجموعة للتمارين
exercises_collection = client.create_collection("exercises")
nutrition_collection = client.create_collection("nutrition")

# تحميل نموذج التحويل إلى متجهات
embedder = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

# مثال: إضافة تمرين
exercise = {
    "id": "1",
    "name": "تمرين الضغط",
    "description": "تمرين لتقوية عضلات الصدر والذراعين."
}
embedding = embedder.encode([exercise["description"]])[0]
exercises_collection.add(
    documents=[exercise["description"]],
    embeddings=[embedding],
    ids=[exercise["id"]]
)

# مثال: إضافة وجبة
meal = {
    "id": "1",
    "title": "وجبة إفطار صحية",
    "description": "شوفان مع حليب وموز."
}
embedding = embedder.encode([meal["description"]])[0]
nutrition_collection.add(
    documents=[meal["description"]],
    embeddings=[embedding],
    ids=[meal["id"]]
)

if __name__ == '__main__':
    # Initialize the database and model within app context
    with app.app_context():
        init_db()  # Initialize the database before running the app
        load_model()  # Load the model within app context
    app.run(debug=True, host='0.0.0.0', port=5000)