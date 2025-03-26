
import os
import json
import base64
import requests
from datetime import datetime

class IdeogramHandler:
    def __init__(self):
        self.api_key = "mtTlpac2euwPQ8GvLjs6HxHMv3cQvBeZmsYzVETAMXJF3W5qOfBg-OchQ0imPxTbwbMbzMO-TGtr_ztvO7_Efg"
        self.api_url = "https://api.ideogram.ai/generate"

    def generate_image(self, prompt, style="", aspect_ratio="ASPECT_1_1", model="V_2"):
        if not self.api_key:
            return {
                "success": False,
                "error": "Ideogram API key not found"
            }

        headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "image_request": {
                "prompt": prompt,
                "style": style,
                "aspect_ratio": aspect_ratio,
                "model": model,
                "magic_prompt_option": "AUTO"
            }
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            response_data = response.json()
            print("Ideogram API Response:", response_data)  # Debug print
            
            if not response_data.get('data'):
                return {
                    "success": False,
                    "error": "No data in response",
                    "raw_response": response_data
                }

            image_data = response_data['data'][0]
            image_url = image_data.get('url')
            
            if not image_url:
                return {
                    "success": False,
                    "error": "No image URL in response",
                    "raw_response": response_data
                }
            
            from datetime import datetime, timezone
            result = {
                "success": True,
                "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "data": response_data['data'],
                "image": image_url,  # For compatibility
                "url": image_url    # For direct access
            }
            print("Handler returning:", result)  # Debug print
            return result
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"API Error: {str(e)}"
            }

    def get_available_styles(self):
        return [
            "DEFAULT",
            "CINEMATIC",
            "COMIC_BOOK", 
            "DIGITAL_ART",
            "FANTASY_ART",
            "ISOMETRIC",
            "LINE_ART",
            "PHOTOGRAPHIC"
        ]

    def get_aspect_ratios(self):
        return [
            "ASPECT_1_1",
            "ASPECT_16_9", 
            "ASPECT_9_16",
            "ASPECT_4_3",
            "ASPECT_3_4",
            "ASPECT_2_1",
            "ASPECT_1_2"
        ]

    def get_models(self):
        return [
            "V_2",
            "V_1"
        ]
