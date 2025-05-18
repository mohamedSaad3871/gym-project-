# AI Fitness Plan Generator

A Flask web application that uses Hugging Face's open-source AI models to generate personalized workout and meal plans.

## Features

- Generate personalized workout plans
- Generate customized meal plans
- Uses the free TinyLlama model (no API key required)
- Mobile-friendly UI
- Print-friendly results

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd ai-fitness-plan-generator
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python hugging_face_plan_generator.py
```

2. Open your web browser and go to:
```
http://127.0.0.1:5000
```

3. Fill out the form with your details and click "Generate Plan"

## How It Works

This application uses a smaller version of the TinyLlama model, which is an open-source large language model that can run on consumer hardware. When you submit the form:

1. Your input is processed to create a detailed prompt
2. The prompt is sent to the TinyLlama model
3. The model generates a personalized plan based on your inputs
4. The generated plan is displayed in a user-friendly format

## Notes

- The first time you run the application, it will download the model (approximately 1GB) which may take some time depending on your internet connection
- Model inference can take 1-2 minutes to generate a complete plan
- This application runs the model locally on your device, so no data is sent to external APIs

## Requirements

- Python 3.8 or higher
- Minimum 4GB of RAM (8GB recommended)
- Approximately 2GB of disk space for the model

## Customization

If you want to use a different Hugging Face model, you can modify the `MODEL_NAME` variable in `hugging_face_plan_generator.py`:

```python
MODEL_NAME = "facebook/opt-350m"  # Example of a smaller model
```

## License

MIT 