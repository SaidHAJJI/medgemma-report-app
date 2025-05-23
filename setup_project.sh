#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
PROJECT_NAME="medgemma-report-app"
BACKEND_PORT="5001"
PYTHON_VERSION_MAJOR_MINOR="3.9" # Used for Dockerfile, can be adjusted

# --- Helper Functions ---
echogreen() {
    echo -e "\033[0;32m$1\033[0m"
}
echoblue() {
    echo -e "\033[0;34m$1\033[0m"
}

# --- Main Script ---
echogreen "🚀 Starting project setup for: $PROJECT_NAME"

# 1. Create Root Project Directory
if [ -d "$PROJECT_NAME" ]; then
    echoblue "Directory '$PROJECT_NAME' already exists. Skipping creation."
else
    mkdir "$PROJECT_NAME"
    echogreen "✅ Created root directory: $PROJECT_NAME"
fi
cd "$PROJECT_NAME"

# 2. Create Backend Directory and Files
echoblue "🔧 Setting up backend structure..."
mkdir -p backend
cd backend

# requirements.txt
echo "Flask
python-dotenv
google-cloud-aiplatform
gunicorn
Flask-CORS
" > requirements.txt
echogreen "  ✅ Created backend/requirements.txt"

# .env.example (for environment variables)
echo "FLASK_APP=app.py
FLASK_ENV=development
FLASK_RUN_PORT=$BACKEND_PORT

# --- Vertex AI Credentials (to be filled later) ---
# For local development, you might point GOOGLE_APPLICATION_CREDENTIALS to your service account JSON key
# GOOGLE_APPLICATION_CREDENTIALS=\"/path/to/your/service-account-key.json\"
GOOGLE_CLOUD_PROJECT=\"your-gcp-project-id\"
VERTEX_AI_LOCATION=\"your-vertex-ai-region\" # e.g., us-central1
VERTEX_AI_ENDPOINT_ID=\"projects/your-gcp-project-id/locations/your-vertex-ai-region/endpoints/your-vertex-ai-endpoint-id\"
" > .env.example
echogreen "  ✅ Created backend/.env.example (Remember to create a .env file from this)"

# app.py (Basic Flask App)
echo "from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# from google.cloud import aiplatform # Uncomment when ready
# from google.protobuf import json_format # Uncomment when ready
# from google.protobuf.struct_pb2 import Value # Uncomment when ready

load_dotenv()

app = Flask(__name__)
CORS(app) # Enable CORS for all routes and origins by default

# --- Vertex AI Configuration (to be filled from .env) ---
# PROJECT_ID = os.getenv(\"GOOGLE_CLOUD_PROJECT\")
# LOCATION = os.getenv(\"VERTEX_AI_LOCATION\")
# ENDPOINT_ID = os.getenv(\"VERTEX_AI_ENDPOINT_ID\")

# def predict_text_llm(prompt: str, temperature: float = 0.2, max_output_tokens: int = 1024):
#     aiplatform.init(project=PROJECT_ID, location=LOCATION)
#     endpoint = aiplatform.Endpoint(ENDPOINT_ID)
#     instances = [{\"prompt\": prompt}] # This will vary based on your model
#     parameters_dict = {
#         \"temperature\": temperature,
#         \"maxOutputTokens\": max_output_tokens,
#     }
#     try:
#         response = endpoint.predict(instances=instances, parameters=parameters_dict)
#         # --- IMPORTANT: Parse response.predictions[0] based on your model's output structure ---
#         # Example for PaLM 2 text-bison:
#         # prediction_output = response.predictions[0]['content']
#         # Example for Gemini Pro:
#         # prediction_output = response.predictions[0]['candidates'][0]['content']['parts'][0]['text']
#         # For now, placeholder:
#         prediction_output = \"LLM Response for: \" + prompt[:50] + \"... (Implement actual parsing)\"
#         return prediction_output
#     except Exception as e:
#         app.logger.error(f\"Vertex AI prediction error: {e}\")
#         raise

@app.route('/api/test', methods=['GET'])
def test_route():
    app.logger.info('Test route accessed')
    return jsonify({'message': 'Backend is running!'})

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    try:
        data = request.get_json()
        if not data or 'inputText' not in data or 'reportType' not in data:
            app.logger.error('Missing inputText or reportType in request')
            return jsonify({'error': 'Missing inputText or reportType'}), 400

        input_text = data['inputText']
        report_type = data['reportType']
        app.logger.info(f'Received report request: type={report_type}, text_snippet=\"{input_text[:50]}...\"')

        # --- PROMPT ENGINEERING (Placeholder) ---
        prompt = f\"Generate a {report_type} based on the following: {input_text}\"

        # --- Call Vertex AI (Placeholder) ---
        # report_content = predict_text_llm(prompt=prompt)
        report_content = f\"Simulated LLM Report for type '{report_type}': Summary of '{input_text[:30]}...' (Connect to Vertex AI)\"
        app.logger.info('Successfully generated report (simulated)')
        return jsonify({'report': report_content})

    except Exception as e:
        app.logger.error(f\"Error in /api/generate-report: {e}\", exc_info=True)
        return jsonify({'error': f'An internal error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_RUN_PORT', $BACKEND_PORT))
    # Use 0.0.0.0 to be accessible from outside the container/network
    app.run(debug=(os.getenv('FLASK_ENV') == 'development'), host='0.0.0.0', port=port)
" > app.py
echogreen "  ✅ Created backend/app.py"

# Dockerfile
echo "FROM python:${PYTHON_VERSION_MAJOR_MINOR}-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Environment variables for Gunicorn and Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
# PORT environment variable is typically set by Cloud Run
ENV PORT 8080

# Command to run the application using Gunicorn
# Use the PORT environment variable Cloud Run provides.
CMD exec gunicorn --bind :\$PORT --workers 2 --threads 2 --timeout 0 app:app
" > Dockerfile
echogreen "  ✅ Created backend/Dockerfile"

cd .. # Back to root project directory
echogreen "✅ Backend structure complete."

# 3. Create Frontend Directory (minimal, will be populated by create-react-app)
echoblue "🔧 Setting up frontend structure (minimal placeholders)..."
mkdir -p frontend
cd frontend

# .env.example (for environment variables)
echo "REACT_APP_API_URL=http://localhost:$BACKEND_PORT
" > .env.example
echogreen "  ✅ Created frontend/.env.example (Remember to create a .env file from this)"

# Placeholder files that create-react-app will typically overwrite or use
mkdir -p public src
echo "{
  \"name\": \"frontend\",
  \"version\": \"0.1.0\",
  \"private\": true,
  \"dependencies\": {},
  \"scripts\": {
    \"start\": \"echo \\\"Run 'npm start' or 'yarn start' after 'create-react-app . --template minimal' or similar\\\"\",
    \"build\": \"echo \\\"Run 'npm run build' or 'yarn build' after CRA setup\\\"\"
  }
}" > package.json.placeholder # Placeholder, CRA will generate the real one
echogreen "  ✅ Created frontend/package.json.placeholder"
echo "// Minimal index.html, create-react-app will generate a proper one
// You can run 'npx create-react-app . --template minimal' in this 'frontend' directory
// or 'npx create-react-app . ' for the standard template.
" > public/index.html.placeholder
echogreen "  ✅ Created frontend/public/index.html.placeholder"
echo "// Minimal App.js, create-react-app will generate a proper one
function App() {
  return (
    <div className=\"App\">
      <header className=\"App-header\">
        <p>Frontend (Initialize with create-react-app)</p>
      </header>
    </div>
  );
}
export default App;
" > src/App.js.placeholder
echogreen "  ✅ Created frontend/src/App.js.placeholder"
echo "// Minimal index.js, create-react-app will generate a proper one
import React from 'react';
import ReactDOM from 'react-dom/client';
// import './index.css'; // CRA will create this
// import App from './App'; // CRA will create/use this
// import reportWebVitals from './reportWebVitals'; // CRA will create this

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <div>Frontend Placeholder. Initialize with create-react-app.</div>
  </React.StrictMode>
);
// reportWebVitals();
" > src/index.js.placeholder
echogreen "  ✅ Created frontend/src/index.js.placeholder"


cd .. # Back to root project directory
echogreen "✅ Frontend structure complete."

# 4. Create Root Files
echoblue "🔧 Creating root files..."

# .gitignore
echo "# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
*.egg-info/
.installed.cfg
*.egg
*.whl

# Backend .env file
backend/.env

# Node / React
frontend/node_modules/
frontend/build/
frontend/coverage/
frontend/.env
frontend/.env.local
frontend/.env.development.local
frontend/.env.test.local
frontend/.env.production.local
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE / OS specific
.vscode/
.idea/
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?
.DS_Store
Thumbs.db
" > .gitignore
echogreen "  ✅ Created .gitignore"

# README.md
echo "# $PROJECT_NAME

A web application using Google MedGemma (via Vertex AI) to output reports.

## Project Structure

-   \`backend/\`: Python Flask application for handling API requests and Vertex AI communication.
-   \`frontend/\`: React application for the user interface.

## Setup

### Prerequisites

-   Node.js and npm/yarn (for frontend)
-   Python $PYTHON_VERSION_MAJOR_MINOR+ (for backend)
-   Docker (for containerization)
-   Google Cloud SDK (gcloud CLI)
-   Access to a Vertex AI Endpoint for a medical LLM.

### Backend Setup

1.  Navigate to the \`backend\` directory:
    \`cd backend\`
2.  Create and activate a Python virtual environment:
    \`python$PYTHON_VERSION_MAJOR_MINOR -m venv venv\`
    \`source venv/bin/activate\` (Linux/macOS) or \`venv\\Scripts\\activate\` (Windows)
3.  Install dependencies:
    \`pip install -r requirements.txt\`
4.  Create a \`.env\` file from \`.env.example\` and fill in your Vertex AI details:
    \`cp .env.example .env\`
    (Edit \`.env\` with your credentials)
5.  Run the Flask development server:
    \`flask run\`
    The backend should be running on \`http://localhost:$BACKEND_PORT\`.

### Frontend Setup

1.  Navigate to the \`frontend\` directory:
    \`cd frontend\`
2.  **IMPORTANT**: Initialize the React project (this will overwrite placeholder files):
    \`npx create-react-app . --template minimal\`
    (Or use \`npx create-react-app . \` for the standard template)
    (Or use \`yarn create react-app .\`)
3.  Once initialized, install any additional frontend dependencies if needed.
4.  Create a \`.env\` file from \`.env.example\` if you need to customize \`REACT_APP_API_URL\` (though the default should work with the backend setup):
    \`cp .env.example .env\`
5.  Start the React development server:
    \`npm start\` (or \`yarn start\`)
    The frontend should be running on \`http://localhost:3000\` by default.

## Deployment (Example: Google Cloud Run)

### Backend

1.  Ensure your \`backend/Dockerfile\` is configured.
2.  Build and push the Docker image to Google Artifact Registry.
3.  Deploy to Cloud Run, setting necessary environment variables (PROJECT_ID, LOCATION, ENDPOINT_ID) and associating a service account with Vertex AI permissions.

### Frontend

1.  Build the static assets: \`npm run build\` (or \`yarn build\`) in the \`frontend\` directory.
2.  Deploy the \`build\` folder to a static hosting service (e.g., Firebase Hosting, Netlify, Vercel, Google Cloud Storage).
    Ensure the \`REACT_APP_API_URL\` environment variable is set correctly during the build or in the hosting service's settings to point to your deployed backend.

## Disclaimer
This tool is for research and informational purposes only and is NOT a substitute for professional medical advice.
" > README.md
echogreen "  ✅ Created README.md"

echogreen "🎉 Project structure for '$PROJECT_NAME' created successfully! 🎉"
echoblue "Next Steps:"
echo "1. cd $PROJECT_NAME"
echo "2. Initialize Git: git init && git add . && git commit -m \"Initial project structure\""
echo "3. Follow the setup instructions in README.md to develop backend and frontend."
echo "   - Especially, run 'npx create-react-app .' in the 'frontend' directory."
echo "4. Once your Vertex AI endpoint is ready, update 'backend/.env' with its details."