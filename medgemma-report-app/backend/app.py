from flask import Flask, request, jsonify
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
# PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
# LOCATION = os.getenv("VERTEX_AI_LOCATION")
# ENDPOINT_ID = os.getenv("VERTEX_AI_ENDPOINT_ID")

# def predict_text_llm(prompt: str, temperature: float = 0.2, max_output_tokens: int = 1024):
#     aiplatform.init(project=PROJECT_ID, location=LOCATION)
#     endpoint = aiplatform.Endpoint(ENDPOINT_ID)
#     instances = [{"prompt": prompt}] # This will vary based on your model
#     parameters_dict = {
#         "temperature": temperature,
#         "maxOutputTokens": max_output_tokens,
#     }
#     try:
#         response = endpoint.predict(instances=instances, parameters=parameters_dict)
#         # --- IMPORTANT: Parse response.predictions[0] based on your model's output structure ---
#         # Example for PaLM 2 text-bison:
#         # prediction_output = response.predictions[0]['content']
#         # Example for Gemini Pro:
#         # prediction_output = response.predictions[0]['candidates'][0]['content']['parts'][0]['text']
#         # For now, placeholder:
#         prediction_output = "LLM Response for: " + prompt[:50] + "... (Implement actual parsing)"
#         return prediction_output
#     except Exception as e:
#         app.logger.error(f"Vertex AI prediction error: {e}")
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
        app.logger.info(f'Received report request: type={report_type}, text_snippet="{input_text[:50]}..."')

        # --- PROMPT ENGINEERING (Placeholder) ---
        prompt = f"Generate a {report_type} based on the following: {input_text}"

        # --- Call Vertex AI (Placeholder) ---
        # report_content = predict_text_llm(prompt=prompt)
        report_content = f"Simulated LLM Report for type '{report_type}': Summary of '{input_text[:30]}...' (Connect to Vertex AI)"
        app.logger.info('Successfully generated report (simulated)')
        return jsonify({'report': report_content})

    except Exception as e:
        app.logger.error(f"Error in /api/generate-report: {e}", exc_info=True)
        return jsonify({'error': f'An internal error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_RUN_PORT', 5001))
    # Use 0.0.0.0 to be accessible from outside the container/network
    app.run(debug=(os.getenv('FLASK_ENV') == 'development'), host='0.0.0.0', port=port)

