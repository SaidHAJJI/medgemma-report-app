#!/bin/bash

set -e # Exit on error

# --- Configuration (Fill these in if they change or are not passed as arguments) ---
DEFAULT_GCP_PROJECT_ID="265233472303" # Your Project Number
DEFAULT_VERTEX_AI_REGION="us-central1"
# !! IMPORTANT: You need to get this after deploying your model to an endpoint !!
DEFAULT_VERTEX_AI_ENDPOINT_NUMERIC_ID="YOUR_ENDPOINT_ID_NUMBER_HERE" # e.g., 1234567890123456789

DEFAULT_FLASK_RUN_PORT="5001"

# --- Input Prompts if variables are not set or are placeholders ---
GCP_PROJECT_ID="${1:-$DEFAULT_GCP_PROJECT_ID}"
VERTEX_AI_REGION="${2:-$DEFAULT_VERTEX_AI_REGION}"
VERTEX_AI_ENDPOINT_NUMERIC_ID="${3:-$DEFAULT_VERTEX_AI_ENDPOINT_NUMERIC_ID}"
FLASK_RUN_PORT="${4:-$DEFAULT_FLASK_RUN_PORT}"

# --- Helper Functions ---
echogreen() {
    echo -e "\033[0;32m$1\033[0m"
}
echored() {
    echo -e "\033[0;31m$1\033[0m"
}
echoblue() {
    echo -e "\033[0;34m$1\033[0m"
}

# Check if inside the project root (where 'backend' and 'frontend' dirs are)
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echored "ERROR: This script should be run from the root of your project directory (e.g., 'medgemma-report-app')."
    echored "It expects 'backend' and 'frontend' subdirectories to exist."
    exit 1
fi

# Prompt for Endpoint ID if it's still the placeholder
if [ "$VERTEX_AI_ENDPOINT_NUMERIC_ID" == "YOUR_ENDPOINT_ID_NUMBER_HERE" ]; then
    echoblue "The Vertex AI Model has been identified, but it needs to be deployed to an Endpoint."
    echoblue "Please deploy your MedGemma model (google_medgemma-4b-it-1748009733891@1) to a Vertex AI Endpoint in the '$VERTEX_AI_REGION' region."
    read -p "Once deployed, enter the NUMERIC ID of that Vertex AI Endpoint: " USER_ENTERED_ENDPOINT_ID
    if [ -z "$USER_ENTERED_ENDPOINT_ID" ]; then
        echored "No Endpoint ID entered. Exiting. Please update backend/.env manually later."
        exit 1
    fi
    VERTEX_AI_ENDPOINT_NUMERIC_ID="$USER_ENTERED_ENDPOINT_ID"
fi

# Construct the full Vertex AI Endpoint path
VERTEX_AI_ENDPOINT_FULL_PATH="projects/${GCP_PROJECT_ID}/locations/${VERTEX_AI_REGION}/endpoints/${VERTEX_AI_ENDPOINT_NUMERIC_ID}"

# Create/Overwrite backend/.env file
ENV_FILE_PATH="backend/.env"

echoblue "✏️  Creating/Updating backend environment file: $ENV_FILE_PATH"

echo "# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
FLASK_RUN_PORT=${FLASK_RUN_PORT}

# --- Vertex AI Credentials ---
# For local development using a service account JSON key, uncomment and set the path below:
# GOOGLE_APPLICATION_CREDENTIALS=\"/path/to/your/service-account-key.json\"
#
# If you run 'gcloud auth application-default login' locally,
# you might not need to set GOOGLE_APPLICATION_CREDENTIALS explicitly.
# For Cloud Run, the service account associated with the Cloud Run service will be used.

GOOGLE_CLOUD_PROJECT=\"${GCP_PROJECT_ID}\"
VERTEX_AI_LOCATION=\"${VERTEX_AI_REGION}\"
VERTEX_AI_ENDPOINT_ID=\"${VERTEX_AI_ENDPOINT_FULL_PATH}\"

# --- Other Backend Settings (if any) ---
" > "$ENV_FILE_PATH"

echogreen "✅ Successfully created/updated '$ENV_FILE_PATH' with:"
echogreen "   GOOGLE_CLOUD_PROJECT=${GCP_PROJECT_ID}"
echogreen "   VERTEX_AI_LOCATION=${VERTEX_AI_REGION}"
echogreen "   VERTEX_AI_ENDPOINT_ID=${VERTEX_AI_ENDPOINT_FULL_PATH}"
echogreen "   FLASK_RUN_PORT=${FLASK_RUN_PORT}"
echo ""
echoblue "Next Steps for Backend:"
echo "1. If you are developing locally and want to use a service account JSON key:"
echo "   a. Make sure you have downloaded the key file."
echo "   b. Uncomment the 'GOOGLE_APPLICATION_CREDENTIALS' line in '$ENV_FILE_PATH' and set the correct path to your key file."
echo "2. Alternatively, for local development, you can run: 'gcloud auth application-default login'"
echo "   This allows your local environment to use your user credentials for accessing Google Cloud services (ensure your user has Vertex AI permissions)."
echo "3. Ensure your Python virtual environment is activated and dependencies are installed (\`pip install -r backend/requirements.txt\`)."
echo "4. You can then run the backend: \`cd backend && flask run\`"
echo ""
echored "IMPORTANT: The backend code (backend/app.py) will need to be updated to correctly parse the specific input/output format of the MedGemma model on your Vertex AI endpoint."
echored "The current placeholder in app.py will likely not work directly with MedGemma."