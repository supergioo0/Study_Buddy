from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
import google.generativeai as genai

genai.configure(api_key="AIzaSyC4Ptf8m0Ma5GwhYAvZwEPNkav6Nq7XwNk")

def create_session(project_id, location, engine_id, user_pseudo_id):
    """Creates a session."""
    client = discoveryengine.ConversationalSearchServiceClient()
    parent = f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}"
    request = discoveryengine.CreateSessionRequest(
        parent=parent,
        session=discoveryengine.Session(
            user_pseudo_id=user_pseudo_id
        )
    )
    return client.create_session(request)

class TheoryAgent:
    def __init__(self, project_id, location, engine_id, user_pseudo_id):
        self.project_id = project_id
        self.location = location
        self.engine_id = engine_id
        self.user_pseudo_id = user_pseudo_id
        self.client = self.initialize_client()
        self.session = self.initialize_session()

    def initialize_client(self):
        """Initialize the Discovery Engine client."""
        try:
            client = discoveryengine.ConversationalSearchServiceClient()
            return client
        except Exception as e:
            print(f"DEBUG: Failed to initialize client: {e}")
            raise RuntimeError("Failed to initialize the Discovery Engine client.") from e

    def initialize_session(self):
        """Initialize a session."""
        return create_session(self.project_id, self.location, self.engine_id, self.user_pseudo_id)

    def query(self, query_text):
        """Query the Discovery Engine with session."""
        try:
            session_name = self.session.name

            query_understanding_spec = discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec(
                query_rephraser_spec=discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryRephraserSpec(
                    disable=False,
                    max_rephrase_steps=1,
                ),
                query_classification_spec=discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec(
                    types=[
                        discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec.Type.ADVERSARIAL_QUERY,
                        discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec.Type.NON_ANSWER_SEEKING_QUERY,
                    ],
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
                    preamble="You are a theory agent. Provide concrete and concise answers. Be formally friendly. If the resources don't give an exact answer but can be used as theory use them."
                ),
                include_citations=False,
                answer_language_code="en",
            )

            request = discoveryengine.AnswerQueryRequest(
                serving_config=f"projects/{self.project_id}/locations/{self.location}/collections/default_collection/engines/{self.engine_id}/servingConfigs/default_serving_config",
                query=discoveryengine.Query(text=query_text),
                session=session_name,
                query_understanding_spec=query_understanding_spec,
                answer_generation_spec=answer_generation_spec,
            )

            response = self.client.answer_query(request)

            print("DEBUG: Full response from TheoryAgent:", response)

            answer_text = response.answer.answer_text if hasattr(response, 'answer') and hasattr(response.answer, 'answer_text') else None

            if not answer_text:
                print("DEBUG: No 'answer_text' found in the response.")
                return {"error": "No answer_text found in the response."}

            return {"answer_text": answer_text}

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
                "Whenever you need to write formulas or equations, format them using LaTeX syntax. Enclose the formula in $ for inline math or $$ for block math. For example: $ \displaystyle{ \int^{1}_{0} (2x+3) \, dx } $."
                "Please also keep a track of what is being said in chat."
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
        prompt += "If user query seems to be a follow up question, please answer it yourself. Based on the previous query"
        prompt += "Do not answer any query outside of mathematical concepts."
        prompt += "Whenever you need to write formulas or equations, format them using LaTeX syntax. Enclose the formula in $ for inline math or $$ for block math. For example: $ \displaystyle{ \int^{1}_{0} (2x+3) \, dx } $."

        response = self.model.generate_content(prompt)
        return response.text if hasattr(response, 'text') else "No response generated."

    def should_use_theory(self, user_input):
        # Creative Agent's logic to decide if theory should be used
        # For now, we'll just skip the theory on specific questions like "Can you give me more examples?"
        return "examples" not in user_input.lower()


class StudyBuddy:
    def __init__(self, project_id, location, engine_id, model_name, user_pseudo_id):
        self.theory_agent = TheoryAgent(project_id, location, engine_id, user_pseudo_id)
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


# Example usage for testing
if __name__ == "__main__":
    # Setup
    project_id = "united-impact-440612-m8"
    location = "global"
    engine_id = "study-buddy_1731147577608"
    model_name = "gemini-1.5-pro"

    # Initialize the Gemini client
    API_KEY = "AIzaSyC4Ptf8m0Ma5GwhYAvZwEPNkav6Nq7XwNk"
    genai.configure(api_key=API_KEY)


    # Initialize the StudyBuddy system
    study_buddy = StudyBuddy(project_id, location, engine_id, model_name)

    # Test a query
    user_query = "How to solve quadratic equations?"
    response = study_buddy.get_study_buddy_response(user_query)

    # Output
    print("Study Buddy's Response:", response)