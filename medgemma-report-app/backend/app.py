from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json # Ensure this is imported for json.dumps

from google.cloud import aiplatform
# from google.auth.transport.requests import Request # Currently unused
# from google.oauth2.service_account import Credentials as ServiceAccountCredentials # Currently unused

load_dotenv()

app = Flask(__name__)
CORS(app)

# --- Vertex AI Configuration ---
PROJECT_ID_NUMBER = os.getenv("GOOGLE_CLOUD_PROJECT")
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION")
FULL_VERTEX_AI_ENDPOINT_PATH = os.getenv("VERTEX_AI_ENDPOINT_ID")


if PROJECT_ID_NUMBER and VERTEX_AI_LOCATION:
    try:
        aiplatform.init(project=PROJECT_ID_NUMBER, location=VERTEX_AI_LOCATION)
        app.logger.info(f"Vertex AI SDK initialized for project {PROJECT_ID_NUMBER} in {VERTEX_AI_LOCATION}")
    except Exception as e_init:
        app.logger.error(f"Failed to initialize Vertex AI SDK: {e_init}", exc_info=True)
else:
    app.logger.warning("Vertex AI Project ID or Location not defined. API calls will likely fail.")


def predict_medgemma_chat( # Consider renaming if it's no longer strictly "chat" input
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.3
):
    if not FULL_VERTEX_AI_ENDPOINT_PATH:
        app.logger.error("FULL_VERTEX_AI_ENDPOINT_PATH (from VERTEX_AI_ENDPOINT_ID) is not defined.")
        raise ValueError("VERTEX_AI_ENDPOINT_ID is not defined in the environment.")

    try:
        endpoint = aiplatform.Endpoint(FULL_VERTEX_AI_ENDPOINT_PATH)
        app.logger.info(f"Using Vertex AI Endpoint: {FULL_VERTEX_AI_ENDPOINT_PATH}")
    except Exception as e_endpoint_init:
        app.logger.error(f"Failed to initialize Vertex AI Endpoint object for {FULL_VERTEX_AI_ENDPOINT_PATH}: {e_endpoint_init}", exc_info=True)
        raise ValueError(f"Failed to initialize Vertex AI Endpoint: {e_endpoint_init}")

    full_prompt_text = ""
    if system_prompt: 
        full_prompt_text += f"System: {system_prompt}\n\n" 
    full_prompt_text += f"User: {user_prompt}"

    instances = [
        {
            "prompt": full_prompt_text
        }
    ]
    
    parameters_for_predict_call = {
        "temperature": temperature,
        "maxOutputTokens": max_tokens 
    }

    # This is the main try block for the Vertex AI call and response processing
    try: 
        app.logger.info(f"Sending request to Vertex AI. Instance (prompt): {json.dumps(instances[0], indent=2, default=str)}")
        app.logger.info(f"Parameters for predict call: {json.dumps(parameters_for_predict_call, indent=2, default=str)}")
        
        prediction_response = endpoint.predict(instances=instances, parameters=parameters_for_predict_call)
        app.logger.info("Response received from Vertex AI.")

        # --- ENHANCED LOGGING FOR THE RESPONSE ---
        app.logger.info(f"Raw prediction_response object type: {type(prediction_response)}")
        app.logger.debug(f"Attributes and methods of prediction_response: {dir(prediction_response)}") 
        
        if hasattr(prediction_response, 'predictions'):
            app.logger.info(f"prediction_response.predictions type: {type(prediction_response.predictions)}")
            # This is a nested try-except for logging the predictions content
            try: 
                predictions_log_content = json.dumps(prediction_response.predictions, indent=2, default=str)
                if len(predictions_log_content) > 2000: 
                     predictions_log_content = predictions_log_content[:2000] + "..."
                app.logger.info(f"prediction_response.predictions content (json.dumps attempt): {predictions_log_content}")
            except TypeError: # This except belongs to the nested try
                app.logger.info(f"prediction_response.predictions content (raw str): {str(prediction_response.predictions)[:2000]}")
        else: # This else belongs to 'if hasattr(prediction_response, 'predictions')'
            app.logger.warning("prediction_response object does not have a 'predictions' attribute.")
        
        if hasattr(prediction_response, 'deployed_model_id'):
            app.logger.info(f"Deployed Model ID from response: {prediction_response.deployed_model_id}")
        # --- END OF ENHANCED LOGGING ---

        prediction_output = "Erreur : Impossible d'analyser la prédiction."
        
        if hasattr(prediction_response, 'predictions') and \
           prediction_response.predictions and \
           isinstance(prediction_response.predictions, list) and \
           len(prediction_response.predictions) > 0:
            
            first_prediction_obj = prediction_response.predictions[0] 
            app.logger.info(f"Type de first_prediction_obj: {type(first_prediction_obj)}")

                                        # ... inside the 'if isinstance(first_prediction_obj, str):' block
            if isinstance(first_prediction_obj, str):
                prediction_output = first_prediction_obj
                app.logger.info(f"Prédiction extraite directement (brute) : {prediction_output[:300]}...")
                
                processed_output = prediction_output 

                # Try to find the most specific start of the actual content
                # Order matters here: check for more specific prefixes first.
                if "Résumé :" in processed_output: # French "Summary :"
                     parts = processed_output.split("Résumé :", 1)
                     if len(parts) > 1:
                        processed_output = parts[1].strip()
                elif "Output:" in processed_output: # English "Output:"
                    parts = processed_output.split("Output:", 1)
                    if len(parts) > 1:
                        processed_output = parts[1].strip()
                elif "Réponse:" in processed_output: # French "Response:"
                     parts = processed_output.split("Réponse:", 1)
                     if len(parts) > 1:
                        processed_output = parts[1].strip()
                # You could add more generic stripping if the model sometimes just outputs without a clear prefix
                # For instance, if "System: " is always there before the real summary:
                elif "System: " in processed_output and len(processed_output.split("System: ", 1)) > 1:
                    # This is a bit broad, be careful it doesn't strip actual content if "System: " appears mid-text
                    # Might be better to rely on the "Résumé :", "Output:", "Réponse:" markers
                    pass # Avoid overly broad stripping for now unless necessary

                if processed_output != prediction_output:
                    app.logger.info(f"Après post-traitement : {processed_output[:200]}...")
                    prediction_output = processed_output
                else:
                    app.logger.info("Aucun marqueur connu pour le post-traitement trouvé, ou aucun texte après. Retour de la chaîne telle quelle ou précédemment traitée.")
                    # Decide if you want to return the full string or indicate an issue
                    # For now, we return the (potentially still unprocessed) string
                    
            elif isinstance(first_prediction_obj, dict): 
                app.logger.debug(f"Premier objet de prédiction (dict) : {json.dumps(first_prediction_obj, indent=2, default=str)}")
                if 'content' in first_prediction_obj: 
                    prediction_output = first_prediction_obj['content']
                    app.logger.info("Prédiction extraite (structure simple 'content').")
                elif 'choices' in first_prediction_obj and \
                   isinstance(first_prediction_obj['choices'], list) and \
                   len(first_prediction_obj['choices']) > 0:
                    first_choice = first_prediction_obj['choices'][0]
                    if isinstance(first_choice, dict) and \
                       'message' in first_choice and \
                       isinstance(first_choice['message'], dict) and \
                       'content' in first_choice['message']:
                        prediction_output = first_choice['message']['content']
                        finish_reason = first_choice.get('finish_reason', 'N/A')
                        app.logger.info(f"Prédiction extraite avec succès (structure 'choices'). Fin : {finish_reason}")
                    else:
                        app.logger.error("Structure 'message' ou 'content' manquante ou incorrecte dans 'choices[0]'.")
                elif 'candidates' in first_prediction_obj and \
                     isinstance(first_prediction_obj.get('candidates'), list) and \
                     len(first_prediction_obj['candidates']) > 0:
                    try:
                        prediction_output = first_prediction_obj['candidates'][0]['content']['parts'][0]['text']
                        app.logger.info("Prédiction extraite (structure type Gemini).")
                    except (KeyError, IndexError, TypeError) as e_gemini:
                        app.logger.error(f"Erreur lors de l'analyse de la structure Gemini : {e_gemini}")
                else:
                    app.logger.error("Structure 'choices' manquante ou incorrecte, ou autre structure non reconnue dans la prédiction.")
            else: 
                app.logger.error(f"Le premier objet de prédiction n'est ni une chaîne ni un dictionnaire : {type(first_prediction_obj)}. Contenu brut (partiel) : {str(first_prediction_obj)[:500]}")
        else:
            app.logger.warning("Aucune prédiction reçue (prediction_response.predictions est vide, None, non une liste, ou n'existe pas).")

        return prediction_output

    # This 'except' belongs to the main 'try' block above
    except Exception as e: 
        app.logger.error(f"Erreur de prédiction Vertex AI : {e}", exc_info=True)
        error_details = str(e)
        if hasattr(e, 'grpc_status_code'): 
            error_details = f"gRPC status: {e.grpc_status_code}, Details: {getattr(e, 'message', str(e))}"
        elif hasattr(e, 'details') and callable(e.details):
             error_details = e.details()
        elif hasattr(e, 'message') and e.message:
             error_details = e.message
        
        app.logger.error(f"Détails de l'erreur API extraits : {error_details}")
        raise ValueError(f"Échec de l'appel à Vertex AI : {error_details}")


@app.route('/api/test', methods=['GET'])
def test_route():
    app.logger.info('Route de test accédée')
    return jsonify({'message': 'Le backend fonctionne !'})

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    try:
        data = request.get_json()
        if not data or 'inputText' not in data or 'reportType' not in data:
            app.logger.error('inputText ou reportType manquant dans la requête')
            return jsonify({'error': 'inputText ou reportType manquant'}), 400

        input_text = data['inputText']
        report_type = data['reportType']
        
        app.logger.info(f'Requête de rapport reçue : type={report_type}, extrait de texte="{input_text[:50]}..."')

        system_prompt = "Vous êtes un assistant médical IA utile. Votre rôle est de traiter du texte médical et de générer des rapports comme demandé. Soyez toujours factuel et prudent."
        user_prompt = ""

        if report_type == "Summarize Clinical Notes":
            system_prompt = "Vous êtes un expert pour résumer les informations cliniques de manière concise et précise pour les professionnels de la santé."
            user_prompt = f"Veuillez résumer les notes cliniques suivantes :\n\n---\n{input_text}\n---"
        elif report_type == "Explain Medical Terminology":
            system_prompt = "Vous êtes un expert pour expliquer la terminologie médicale complexe en termes simples et compréhensibles."
            user_prompt = f"Veuillez expliquer tous les termes ou concepts médicaux complexes trouvés dans le texte suivant. Si des termes spécifiques ne sont pas mis en évidence, expliquez les concepts clés présents :\n\n---\n{input_text}\n---"
        else: 
            user_prompt = f"Concernant le contexte médical suivant :\n\n---\n{input_text}\n---\n\nVeuillez effectuer la tâche suivante : {report_type}"
        
        app.logger.info(f"Prompt système : {system_prompt}")
        app.logger.info(f"Prompt utilisateur (100 premiers caractères) : {user_prompt[:100]}")

        report_content = predict_medgemma_chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1500, 
            temperature=0.3
        )
        
        app.logger.info('Rapport généré avec succès depuis Vertex AI.')
        return jsonify({'report': report_content})

    except ValueError as ve: 
        app.logger.error(f"Erreur de valeur dans /api/generate-report: {ve}", exc_info=False) 
        return jsonify({'error': str(ve)}), 500
    except Exception as e:
        app.logger.error(f"Erreur inattendue dans /api/generate-report: {e}", exc_info=True)
        return jsonify({'error': f'Une erreur interne non gérée est survenue : {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_RUN_PORT', 5001))
    app.run(debug=(os.getenv('FLASK_ENV') == 'development'), host='0.0.0.0', port=port)