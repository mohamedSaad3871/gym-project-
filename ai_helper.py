"""
Módulo para la integración del chatbot con modelos de IA.
Proporciona funciones para generar respuestas usando el modelo TinyLlama.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import sqlite3
import json
import time
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Configuración del modelo
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Inicialización perezosa del modelo
model = None
tokenizer = None

# Load environment variables
load_dotenv()

# Initialize OpenAI API
api_key = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")

# Initialize client even if key is invalid (will handle errors later)
client = OpenAI(api_key=api_key)

# Cache for storing conversation histories
conversation_cache = {}

# Set expiration time for cache entries (3 hours)
CACHE_EXPIRY_SECONDS = 10800

def load_model():
    """Carga el modelo y el tokenizador"""
    global model, tokenizer
    
    if model is None or tokenizer is None:
        print(f"Cargando modelo {MODEL_NAME} en {DEVICE}...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
            low_cpu_mem_usage=True
        )
        model.to(DEVICE)
        model.eval()
        print(f"Modelo cargado exitosamente")

def create_conversation_db():
    """Crea una base de datos SQLite para almacenar el historial de conversaciones"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conversations.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Crear tabla de conversaciones si no existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversations (
        session_id TEXT,
        user_id TEXT,
        timestamp TEXT,
        message TEXT,
        role TEXT,
        PRIMARY KEY (session_id, timestamp)
    )
    ''')
    
    # Crear índice para búsquedas más rápidas
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON conversations (session_id)')
    
    conn.commit()
    conn.close()

def save_message(session_id, user_id, message, role):
    """Guarda un mensaje en la base de datos
    
    Args:
        session_id (str): ID de la sesión de conversación
        user_id (str): ID del usuario (puede ser anónimo)
        message (str): Contenido del mensaje
        role (str): 'user' o 'assistant'
    """
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conversations.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        cursor.execute(
            'INSERT INTO conversations VALUES (?, ?, ?, ?, ?)',
            (session_id, user_id, timestamp, message, role)
        )
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error al guardar mensaje: {str(e)}")

def get_conversation_history(session_id, limit=10):
    """Obtiene el historial de conversación para una sesión
    
    Args:
        session_id (str): ID de la sesión
        limit (int): Número máximo de mensajes a recuperar
        
    Returns:
        list: Lista de mensajes con sus roles
    """
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conversations.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT message, role FROM conversations WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?',
            (session_id, limit)
        )
        
        results = cursor.fetchall()
        conn.close()
        
        return [{'content': message, 'role': role} for message, role in results]
    except Exception as e:
        print(f"Error al obtener historial: {str(e)}")
        return []

def format_prompt(user_message, conversation_history=None):
    """Format the message and conversation history for the AI model

    Args:
        user_message (str): User message
        conversation_history (list): List of previous messages

    Returns:
        list: Formatted messages for the AI model
    """
    # Initialize messages with system prompt
    messages = [
        {
            "role": "system", 
            "content": """
أنت مدرب محترف متخصص في اللياقة البدنية والتغذية، مع شهادات معتمدة وخبرة أكثر من 10 سنوات. مهمتك هي:

1. تقديم استشارات دقيقة وشخصية للمستخدمين حول:
   - تمارين مخصصة حسب أهدافهم ومستواهم وظروفهم الصحية
   - خطط غذائية مبنية على أسس علمية
   - استراتيجيات فعّالة لبناء العضلات، فقدان الوزن، وتحسين الأداء الرياضي

2. استناد إجاباتك على الأبحاث العلمية الحديثة والمعايير المهنية في مجال اللياقة البدنية والتغذية. عندما تذكر حقائق علمية، أشر لها بـ "وفقاً للدراسات العلمية" أو "من الناحية العلمية".

3. التفاعل بأسلوب إيجابي ومحفّز، مع الاعتراف بمحدوديتك كمدرب افتراضي عند الضرورة. أوصي بمراجعة الطبيب أو المدرب الشخصي في الحالات التي تتطلب ذلك.

4. إظهار صفات المدرب الناجح: الاستماع الجيد، التشجيع، المعرفة العميقة، والقدرة على تحفيز المتدربين.

5. الاحتفاظ بهوية ثابتة مع المتدرب، مع إشارات متكررة إلى أهمية الالتزام والصبر في تحقيق النتائج.

قيود مهمة:
- عدم تقديم نصائح طبية متخصصة
- عدم التشخيص أو علاج الحالات الطبية
- الإشارة إلى ضرورة استشارة الطبيب عند الحديث عن الحالات الصحية الخاصة

يجب أن تكون إجاباتك دقيقة وموثوقة مع توازن بين المعلومات العلمية والنصائح العملية القابلة للتطبيق.
            """
        }
    ]
    
    # Add conversation history if available
    if conversation_history:
        for message in conversation_history:
            messages.append(message)
    
    # Add user message
    messages.append({"role": "user", "content": user_message})
    
    return messages

def get_ai_response(user_message, conversation_history=None, session_id=None):
    """Get AI response using OpenAI API
    
    Args:
        user_message (str): User message
        conversation_history (list): Conversation history
        session_id (str): Session ID to maintain conversation context
        
    Returns:
        str: AI response text
        
    Raises:
        Exception: If there's an error getting AI response
    """
    # Check if API key is valid
    if not api_key or api_key == "your_openai_api_key_here":
        raise ValueError("OpenAI API key is not set. Please configure the API key.")
        
    # Clean and validate user message
    if not user_message or len(user_message.strip()) < 1:
        return "يرجى كتابة سؤال أو طلب للمدرب الافتراضي."
    
    try:
        # Handle session conversation history
        if session_id and session_id in conversation_cache:
            # Get cached conversation if within expiry time
            cache_entry = conversation_cache[session_id]
            now = datetime.now().timestamp()
            if now - cache_entry["timestamp"] < CACHE_EXPIRY_SECONDS:
                conversation_history = cache_entry["conversation"]
            else:
                # Expired cache, start new conversation
                conversation_history = []
        elif not conversation_history:
            conversation_history = []
        
        # Create formatted prompt for OpenAI
        messages = format_prompt(user_message, conversation_history)
        
        # Call OpenAI API with better parameters
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",  # Using a more capable model
            messages=messages,
            temperature=0.7,
            max_tokens=800,
            top_p=0.95,
            frequency_penalty=0.5,
            presence_penalty=0.5
        )
        
        # Get the response text
        response_text = response.choices[0].message.content.strip()
        
        # Update conversation history and cache
        if session_id:
            # Add the interaction to conversation history
            conversation_history.append({"role": "user", "content": user_message})
            conversation_history.append({"role": "assistant", "content": response_text})
            
            # Limit conversation history to last 10 messages (5 exchanges)
            if len(conversation_history) > 10:
                conversation_history = conversation_history[-10:]
                
            # Update or create cache entry
            conversation_cache[session_id] = {
                "conversation": conversation_history,
                "timestamp": datetime.now().timestamp()
            }
            
            # Clean up expired cache entries
            clean_expired_cache()
        
        return response_text
        
    except Exception as e:
        print(f"Error getting AI response: {str(e)}")
        raise Exception(f"حدث خطأ في الاتصال بنظام المدرب الافتراضي: {str(e)}")

def enhance_chatbot_response(response):
    """
    Enhance chatbot responses with better formatting for display
    
    Args:
        response (str): Raw AI response
        
    Returns:
        str: Enhanced response for display
    """
    # Add HTML formatting for better readability
    response = response.replace('\n\n', '</p><p>')
    response = response.replace('\n', '<br>')
    
    # Wrap in paragraph tags
    if not response.startswith('<p>'):
        response = f'<p>{response}</p>'
        
    # Replace plain URLs with clickable links
    import re
    url_pattern = r'(https?://[^\s]+)'
    response = re.sub(url_pattern, r'<a href="\1" target="_blank" class="coach-link">\1</a>', response)
    
    return response

def clean_expired_cache():
    """Clean up expired entries from conversation cache"""
    now = datetime.now().timestamp()
    expired_keys = []
    
    for key, value in conversation_cache.items():
        if now - value["timestamp"] > CACHE_EXPIRY_SECONDS:
            expired_keys.append(key)
            
    for key in expired_keys:
        del conversation_cache[key]
