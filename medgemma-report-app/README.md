# medgemma-report-app

A web application using Google MedGemma (via Vertex AI) to output reports.

## Project Structure

-   `backend/`: Python Flask application for handling API requests and Vertex AI communication.
-   `frontend/`: React application for the user interface.

## Setup

### Prerequisites

-   Node.js and npm/yarn (for frontend)
-   Python 3.9+ (for backend)
-   Docker (for containerization)
-   Google Cloud SDK (gcloud CLI)
-   Access to a Vertex AI Endpoint for a medical LLM.

### Backend Setup

1.  Navigate to the `backend` directory:
    `cd backend`
2.  Create and activate a Python virtual environment:
    `python3.9 -m venv venv`
    `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate` (Windows)
3.  Install dependencies:
    `pip install -r requirements.txt`
4.  Create a `.env` file from `.env.example` and fill in your Vertex AI details:
    `cp .env.example .env`
    (Edit `.env` with your credentials)
5.  Run the Flask development server:
    `flask run`
    The backend should be running on `http://localhost:5001`.

### Frontend Setup

1.  Navigate to the `frontend` directory:
    `cd frontend`
2.  **IMPORTANT**: Initialize the React project (this will overwrite placeholder files):
    `npx create-react-app . --template minimal`
    (Or use `npx create-react-app . ` for the standard template)
    (Or use `yarn create react-app .`)
3.  Once initialized, install any additional frontend dependencies if needed.
4.  Create a `.env` file from `.env.example` if you need to customize `REACT_APP_API_URL` (though the default should work with the backend setup):
    `cp .env.example .env`
5.  Start the React development server:
    `npm start` (or `yarn start`)
    The frontend should be running on `http://localhost:3000` by default.

## Deployment (Example: Google Cloud Run)

### Backend

1.  Ensure your `backend/Dockerfile` is configured.
2.  Build and push the Docker image to Google Artifact Registry.
3.  Deploy to Cloud Run, setting necessary environment variables (PROJECT_ID, LOCATION, ENDPOINT_ID) and associating a service account with Vertex AI permissions.

### Frontend

1.  Build the static assets: `npm run build` (or `yarn build`) in the `frontend` directory.
2.  Deploy the `build` folder to a static hosting service (e.g., Firebase Hosting, Netlify, Vercel, Google Cloud Storage).
    Ensure the `REACT_APP_API_URL` environment variable is set correctly during the build or in the hosting service's settings to point to your deployed backend.

## Disclaimer
This tool is for research and informational purposes only and is NOT a substitute for professional medical advice.

