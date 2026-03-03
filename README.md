A multi-agent AI system that answers math questions accurately, without hallucinating, by grounding responses in over 2,000 pages of verified mathematical theory.
Built as my MYP Personal Project over 4 months.


How It Works
Study Buddy uses two agents working in tandem:
Theory Agent: Built on Google Cloud VertexAI and Discovery Engine. Queries a knowledge base of 2,000+ pages of mathematical theory, spanning high school to university level (Algebra & Geometry). Responsible for accurate, source-grounded retrieval.
Creative Agent: Built on Gemini. Takes the Theory Agent's output and turns it into a clear, conversational response. Handles follow-up questions, maintains context, and explains step-by-step solutions in plain language.
This architecture solves a core problem with general-purpose LLMs (ChatGPT, Gemini, etc.): they predict answers rather than retrieve them, which leads to math errors. Study Buddy grounds every response in real source material.

Technologies used:

Google Cloud VertexAI — Theory Agent backend
Discovery Engine — RAG knowledge base (2,000+ pages)
Gemini API — Creative Agent (response generation)
Streamlit — Frontend chat interface
Python — Core logic

Cost
Total cloud cost to build and run: €1.05
