import google.generativeai as genai
from langchain_ollama import OllamaLLM

class AIHandler:
    def __init__(self, ollama_base_url, ollama_model):
        self.ollama_llm = OllamaLLM(base_url=ollama_base_url, model=ollama_model)
    
    def generate_summary_ollama(self, transcript_text, prompt):
        full_prompt = prompt + "\n\nTranscript: " + transcript_text
        response = self.ollama_llm.generate([full_prompt])
        return response.generations[0][0].text if response.generations else "No response generated"

    def generate_summary_gemini(self, transcript_text, prompt):
        full_prompt = prompt + "\n\n" + transcript_text
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(full_prompt)
        return response.text
