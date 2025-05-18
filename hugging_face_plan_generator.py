from flask import Flask, render_template, request, jsonify
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import os

app = Flask(__name__)

# Configure to load model only once when app starts
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Relatively small model that can run on CPU
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Initialize global variables for model and tokenizer
model = None
tokenizer = None

# Load model and tokenizer
@app.before_first_request
def load_model():
    global model, tokenizer
    print(f"Loading model {MODEL_NAME} on {DEVICE}...")
    
    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        low_cpu_mem_usage=True
    )
    model.to(DEVICE)
    model.eval()  # Set to evaluation mode
    print("Model loaded successfully!")

# Route for home page
@app.route('/')
def index():
    return render_template('hf_plan_generator.html')

# Function to create prompts for different plan types
def create_prompt(plan_type, goal, age, gender, activity_level, weight=None, height=None):
    """Create appropriate prompt based on plan type and user information"""
    
    if plan_type == "workout":
        prompt = f"""
Please create a detailed 1-week workout plan for a {age} year old {gender} with the goal of {goal}. 
Their activity level is {activity_level}.

The workout plan should include:
1. A schedule for each day of the week
2. Specific exercises with sets and repetitions
3. Rest periods and rest days
4. Warm-up and cool-down recommendations
5. Progression recommendations

Please format the response in a clear, structured way.
"""
    
    elif plan_type == "meal":
        prompt = f"""
Please create a detailed 1-week meal plan for a {age} year old {gender} with the goal of {goal}.
Their activity level is {activity_level}.
{"Their weight is " + weight + " kg." if weight else ""}
{"Their height is " + height + " cm." if height else ""}

The meal plan should include:
1. Daily caloric targets
2. Macronutrient distribution (protein, carbs, fat)
3. 3 meals per day plus snacks
4. Specific food suggestions with approximate portions
5. Hydration recommendations

Please format the response in a clear, structured way.
"""
    
    return prompt

# Function to generate text using the model
def generate_plan(prompt, max_length=1024):
    """Generate text using the loaded model"""
    
    # Format the prompt according to the model's expected format
    # TinyLlama uses the Alpaca format
    formatted_prompt = f"<human>: {prompt}\n<assistant>:"
    
    # Tokenize the prompt
    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(DEVICE)
    
    # Generate response
    with torch.no_grad():
        outputs = model.generate(
            inputs.input_ids,
            max_length=max_length,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    # Decode and return the response
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract only the assistant's response
    response = response.split("<assistant>:")[-1].strip()
    
    return response

# Route for generating plans
@app.route('/generate_plan', methods=['POST'])
def generate_plan_route():
    try:
        # Get form data
        plan_type = request.form.get('plan_type')
        goal = request.form.get('goal')
        age = request.form.get('age')
        gender = request.form.get('gender')
        activity_level = request.form.get('activity_level')
        weight = request.form.get('weight')
        height = request.form.get('height')
        
        # Create appropriate prompt
        prompt = create_prompt(plan_type, goal, age, gender, activity_level, weight, height)
        
        # Generate plan using the model
        plan = generate_plan(prompt)
        
        # Return the plan
        return render_template('hf_plan_result.html', plan=plan, plan_type=plan_type)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # In newer Flask versions, before_first_request is deprecated
    with app.app_context():
        load_model()
    app.run(debug=True) 