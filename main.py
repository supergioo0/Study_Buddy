# study_buddy.py
import google.generativeai as genai
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
import os

api_key = os.getenv('GEMINI_API_KEY')
# Set up the Gemini API Key
genai.configure(api_key="AIzaSyC4Ptf8m0Ma5GwhYAvZwEPNkav6Nq7XwNk")

class TheoryAgent:
    def __init__(self, project_id, location, engine_id):
        self.project_id = project_id
        self.location = location
        self.engine_id = engine_id
        self.client = self.initialize_client()

    def initialize_client(self):
        """Initialize the Discovery Engine client."""
        try:
            client_options = (
                ClientOptions(api_endpoint=f"{self.location}-discoveryengine.googleapis.com")
                if self.location != "global"
                else None
            )
            return discoveryengine.ConversationalSearchServiceClient(client_options=client_options)
        except Exception as e:
            print(f"DEBUG: Failed to initialize client: {e}")
            raise RuntimeError("Failed to initialize Discovery Engine client.") from e

    def query(self, query_text):
        """Query the Discovery Engine and return a dictionary with the answer_text."""
        try:
            # Full resource name for the Search serving config
            serving_config = f"projects/{self.project_id}/locations/{self.location}/collections/default_collection/engines/{self.engine_id}/servingConfigs/default_serving_config"

            # Query Understanding and Answer Generation specifications
            query_understanding_spec = discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec(
                query_rephraser_spec=discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryRephraserSpec(
                    disable=False,
                    max_rephrase_steps=1,
                ),
                query_classification_spec=discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec(
                    types=[discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec.Type.ADVERSARIAL_QUERY,
                           discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec.Type.NON_ANSWER_SEEKING_QUERY],
                ),
            )

            answer_generation_spec = discoveryengine.AnswerQueryRequest.AnswerGenerationSpec(
                ignore_adversarial_query=False,
                ignore_non_answer_seeking_query=False,
                ignore_low_relevant_content=False,
                model_spec=discoveryengine.AnswerQueryRequest.AnswerGenerationSpec.ModelSpec(
                    model_version="gemini-1.5-flash-001/answer_gen/v2"
                ),
                prompt_spec=discoveryengine.AnswerQueryRequest.AnswerGenerationSpec.PromptSpec(
                    preamble="You are a theory agent. Provide concrete and concise answers. Be formally friendly."
                ),
                include_citations=False,
                answer_language_code="en",
            )

            # Create the request object
            request = discoveryengine.AnswerQueryRequest(
                serving_config=serving_config,
                query=discoveryengine.Query(text=query_text),
                query_understanding_spec=query_understanding_spec,
                answer_generation_spec=answer_generation_spec,
            )

            # Perform the query
            response = self.client.answer_query(request)

            # Debugging: print the full API response
            print("DEBUG: Full response from TheoryAgent:", response)

            # Extract and return only the 'answer_text'
            answer_text = response.answer.answer_text if hasattr(response, 'answer') and hasattr(response.answer, 'answer_text') else None

            if not answer_text:
                print("DEBUG: No 'answer_text' found in the response.")
                return {"error": "No answer_text found in the response."}

            return {"answer_text": answer_text}  # Return as dictionary with answer_text

        except Exception as e:
            print(f"DEBUG: An error occurred in TheoryAgent query: {e}")
            raise RuntimeError("Failed to query Discovery Engine.") from e


class CreativeAgent:
    def __init__(self, model_name, theory_agent=None):
        self.model_name = model_name
        self.theory_agent = theory_agent  # Store the theory_agent instance
        self.model = genai.GenerativeModel(model_name)

    def formulate_response(self, user_input, theory_response, context):
        try:
            # Add current query and response to context
            context.append({'query': user_input, 'response': theory_response})

            # Check if theory response is needed or skip it
            if theory_response and not self.should_use_theory(user_input):
                return self.generate_creative_response(user_input, context)

            # If the theory response is useful, use it
            answer_text = theory_response.get("answer_text", "No theory response available.")

            # Formulate the prompt for Gemini
            prompt = (
                f"Here is the theory response:\n\n{answer_text}\n\n"
                "Gemini, please use this theory to provide a helpful, detailed, and concise answer to the user's query.\n\n"
                f"User's Question: {user_input}\n\n"
                "You are a study buddy like a tutor for math. Provide friendly and formal assistance."
                "Do not mention the theory explicitly; instead, integrate it seamlessly into your response."
                "If user query seems to be a follow up question, please answer it yourself."
            )

            # Use the Gemini model to generate a response
            response = self.model.generate_content(prompt)

            return response.text if hasattr(response, 'text') else "No response generated."

        except Exception as e:
            print(f"DEBUG: Error in formulate_response: {e}")
            raise RuntimeError(f"CreativeAgent failed to generate response: {e}") from e

    def generate_creative_response(self, user_input, context):
        """Generate a completely new creative response without theory."""
        prompt = f"User's Question: {user_input}\n\n"
        prompt += "You are a friendly tutor who provides helpful, detailed, and concise answers to math problems."
        prompt += " Do not reference any previous theory responses, and provide your answer from scratch."
        prompt += "If user query seems to be a follow up question, please answer it yourself."
        prompt += "Do not answer any query outside of mathematical concepts"

        response = self.model.generate_content(prompt)
        return response.text if hasattr(response, 'text') else "No response generated."

    def should_use_theory(self, user_input):
        # Creative Agent's logic to decide if theory should be used
        # For now, we'll just skip the theory on specific questions like "Can you give me more examples?"
        return "examples" not in user_input.lower()


class StudyBuddy:
    def __init__(self, project_id, location, engine_id, model_name):
        self.theory_agent = TheoryAgent(project_id, location, engine_id)
        self.creative_agent = CreativeAgent(model_name, theory_agent=self.theory_agent)
        self.context = []  # Initialize context to store user queries and responses

    def get_study_buddy_response(self, user_query):
        try:
            # Theory Agent always generates a response
            theory_response = self.theory_agent.query(user_query)

            # Use the creative agent to formulate a response based on the theory response
            return self.creative_agent.formulate_response(user_query, theory_response, self.context)
        except Exception as e:
            print(f"DEBUG: Error in get_study_buddy_response: {e}")
            raise RuntimeError("StudyBuddy failed to generate a response.") from e