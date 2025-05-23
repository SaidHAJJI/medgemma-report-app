from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json # Importer le module json pour une journalisation plus détaillée

from google.cloud import aiplatform
from google.auth.transport.requests import Request # Pour le client d'API personnalisé
from google.oauth2.service_account import Credentials as ServiceAccountCredentials # Si utilisation de clé SA
from google.oauth2 import default as default_credentials # Pour ADC

load_dotenv()

app = Flask(__name__)
CORS(app)

# --- Configuration Vertex AI ---
PROJECT_ID_NUMBER = os.getenv("GOOGLE_CLOUD_PROJECT") # Devrait être le numéro du projet
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION")
# VERTEX_AI_ENDPOINT_ID DOIT être le chemin complet : projects/.../endpoints/...
FULL_VERTEX_AI_ENDPOINT_PATH = os.getenv("VERTEX_AI_ENDPOINT_ID")


# Vérifier si nous utilisons un point de terminaison dédié (basé sur le message d'erreur précédent)
# L'URL de base pour les points de terminaison dédiés
# Exemple: 786455378580733952.us-central1-265233472303.prediction.vertexai.goog
# Nous allons construire cela dynamiquement ou le récupérer depuis une variable d'env si nécessaire
# Pour l'instant, nous allons supposer que FULL_VERTEX_AI_ENDPOINT_PATH est le chemin standard
# et nous allons déterminer si nous devons utiliser un client d'API personnalisé pour le domaine dédié.

# Le SDK Python de Vertex AI devrait gérer les points de terminaison dédiés si l'endpoint
# est correctement initialisé avec le nom complet du point de terminaison.
# Cependant, si le SDK ne gère pas le changement de domaine pour les prédictions
# vers le domaine .prediction.vertexai.goog, nous devrons utiliser un client HTTP plus direct.

# Pour l'instant, essayons avec le SDK standard. Si cela échoue avec une erreur
# similaire à "Dedicated Endpoint cannot be accessed through shared domain",
# nous devrons passer à un client HTTP personnalisé.
# Le SDK google-cloud-aiplatform devrait être capable de gérer cela si on lui donne le bon
# nom de point de terminaison COMPLET au format projects/PROJECT_NUM/locations/LOC/endpoints/ENDPOINT_NUM.

# Initialisation de Vertex AI (faite une fois globalement)
if PROJECT_ID_NUMBER and VERTEX_AI_LOCATION:
    aiplatform.init(project=PROJECT_ID_NUMBER, location=VERTEX_AI_LOCATION)
else:
    app.logger.warning("Vertex AI Project ID ou Location non défini. Les appels API échoueront.")


def predict_medgemma_chat(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.3
):
    if not FULL_VERTEX_AI_ENDPOINT_PATH:
        app.logger.error("FULL_VERTEX_AI_ENDPOINT_PATH (depuis VERTEX_AI_ENDPOINT_ID) n'est pas défini.")
        raise ValueError("VERTEX_AI_ENDPOINT_ID n'est pas défini dans l'environnement.")

    # Le SDK Python utilise le nom complet du point de terminaison pour déterminer comment l'appeler.
    # Il devrait gérer les points de terminaison publics et dédiés/privés correctement.
    endpoint = aiplatform.Endpoint(FULL_VERTEX_AI_ENDPOINT_PATH)
    app.logger.info(f"Utilisation du point de terminaison Vertex AI : {FULL_VERTEX_AI_ENDPOINT_PATH}")


    messages = []
    if system_prompt:
        messages.append({
            "role": "system",
            "content": [{"type": "text", "text": system_prompt}]
        })
    
    user_content = [{"type": "text", "text": user_prompt}]
    messages.append({
        "role": "user",
        "content": user_content
    })

    instances = [
        {
            "@requestFormat": "chatCompletions",
            "messages": messages,
            "max_tokens": max_tokens
        }
    ]
    
    # Les paramètres comme la température sont parfois envoyés dans l'instance elle-même
    # pour les modèles de type chat, ou parfois comme un paramètre de niveau supérieur.
    # Pour votre modèle, la température n'était pas dans l'instance de la requête curl.
    # Essayons de la passer comme paramètre de niveau supérieur à la méthode predict().
    parameters_for_predict_call = {
        "temperature": temperature
        # Si d'autres paramètres de niveau supérieur sont nécessaires, ajoutez-les ici.
    }
    # Si la température doit être dans l'instance :
    # instances[0]["temperature"] = temperature # (Vérifiez la doc de votre modèle)


    try:
        app.logger.info(f"Envoi de la requête à Vertex AI. Instance (partielle) : {json.dumps(instances[0]['messages'], indent=2)}")
        prediction_response = endpoint.predict(instances=instances, parameters=parameters_for_predict_call)
        app.logger.info("Réponse reçue de Vertex AI.")

        # --- ANALYSE DE LA RÉPONSE BASÉE SUR VOTRE SORTIE CURL ---
        prediction_output = "Erreur : Impossible d'analyser la prédiction."
        
        # prediction_response.predictions est une liste d'objets (ou dicts)
        if prediction_response.predictions and len(prediction_response.predictions) > 0:
            # Contrairement à d'autres modèles, votre `predictions` est un OBJET, pas une liste directement.
            # Le SDK le convertit peut-être en une liste avec un seul élément dict.
            # Vérifions la structure réelle de prediction_response.predictions
            
            first_prediction_obj = prediction_response.predictions[0] # Supposons que c'est un dict

            if isinstance(first_prediction_obj, dict):
                app.logger.debug(f"Premier objet de prédiction (dict) : {json.dumps(first_prediction_obj, indent=2)}")
                if 'choices' in first_prediction_obj and \
                   isinstance(first_prediction_obj['choices'], list) and \
                   len(first_prediction_obj['choices']) > 0:
                    
                    first_choice = first_prediction_obj['choices'][0]
                    if isinstance(first_choice, dict) and \
                       'message' in first_choice and \
                       isinstance(first_choice['message'], dict) and \
                       'content' in first_choice['message']:
                        
                        prediction_output = first_choice['message']['content']
                        finish_reason = first_choice.get('finish_reason', 'N/A')
                        app.logger.info(f"Prédiction extraite avec succès. Fin : {finish_reason}")
                    else:
                        app.logger.error("Structure 'message' ou 'content' manquante ou incorrecte dans 'choices[0]'.")
                else:
                    app.logger.error("Structure 'choices' manquante ou incorrecte dans la prédiction.")
            else:
                # Si ce n'est pas un dict, c'est peut-être un objet protobuf. Essayons de le convertir.
                try:
                    # Nécessite : from google.protobuf import json_format
                    # prediction_dict = json_format.MessageToDict(first_prediction_obj)
                    # app.logger.debug(f"Premier objet de prédiction (converti en dict) : {json.dumps(prediction_dict, indent=2)}")
                    # Réessayez la logique d'analyse avec prediction_dict ici...
                    app.logger.error(f"Le premier objet de prédiction n'est pas un dictionnaire : {type(first_prediction_obj)}. Contenu brut (partiel) : {str(first_prediction_obj)[:500]}")

                except Exception as conv_err:
                    app.logger.error(f"Impossible de convertir l'objet de prédiction en dict : {conv_err}")
        else:
            app.logger.warning("Aucune prédiction reçue de Vertex AI ou la liste des prédictions est vide.")
            if hasattr(prediction_response, 'raw_response'): # Certaines bibliothèques ont ça
                 app.logger.warning(f"Réponse brute : {prediction_response.raw_response}")


        return prediction_output

    except Exception as e:
        app.logger.error(f"Erreur de prédiction Vertex AI : {e}", exc_info=True)
        # Vérifier si l'erreur vient de l'API Google pour plus de détails
        error_details = str(e)
        if hasattr(e, 'details'): # Pour google.api_core.exceptions
             error_details = e.details() if callable(e.details) else str(e.details)
        elif hasattr(e, 'message'):
             error_details = e.message
        app.logger.error(f"Détails de l'erreur API : {error_details}")
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
            max_tokens=1500, # Augmentez si nécessaire, attention à "finish_reason": "length"
            temperature=0.3
        )
        
        app.logger.info('Rapport généré avec succès depuis Vertex AI.')
        return jsonify({'report': report_content})

    except ValueError as ve: # Capturer notre erreur personnalisée de predict_medgemma_chat
        app.logger.error(f"Erreur de valeur dans /api/generate-report: {ve}", exc_info=True)
        return jsonify({'error': str(ve)}), 500
    except Exception as e:
        app.logger.error(f"Erreur dans /api/generate-report: {e}", exc_info=True)
        return jsonify({'error': f'Une erreur interne est survenue : {str(e)}'}), 500

if __name__ == '__main__':
    # Configurer la journalisation pour voir les messages DEBUG s'ils sont utiles
    # import logging
    # logging.basicConfig(level=logging.DEBUG) # Ou app.logger.setLevel(logging.DEBUG)

    port = int(os.environ.get('FLASK_RUN_PORT', 5001))
    app.run(debug=(os.getenv('FLASK_ENV') == 'development'), host='0.0.0.0', port=port)