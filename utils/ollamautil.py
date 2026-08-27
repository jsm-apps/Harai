import json
import ollama

class OllamaUtil():
    def __init__(self, model):
        self.model = model
        
    
    def chat_with_text_response(self, messages):
        response = ollama.chat(
                model=self.model,
                messages=messages,
                think=False
        )

        return response["message"]["content"]
