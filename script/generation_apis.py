import os
import io
import base64
import requests
import openai
import discord
from PIL import Image, ImageFile
from diffusers import StableDiffusionPipeline
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GenerationAPI:
    def __init__(self):
        # Initialize API keys from environment variables
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.runway_api_key = os.getenv('RUNWAY_API_KEY')
        self.pika_api_key = os.getenv('PIKA_API_KEY')
        self.discord_token = os.getenv('DISCORD_TOKEN')
        self.discord_channel_id = os.getenv('DISCORD_CHANNEL_ID')

        # Initialize OpenAI client
        if self.openai_api_key:
            openai.api_key = self.openai_api_key

        # Initialize Discord client for Midjourney
        if self.discord_token:
            self.discord_client = discord.Client(intents=discord.Intents.default())

    async def generate_stable_diffusion(self, prompt):
        """Generate image using Stable Diffusion"""
        try:
            model_id = "runwayml/stable-diffusion-v1-5"
            pipe = StableDiffusionPipeline.from_pretrained(model_id)
            if torch.cuda.is_available():
                pipe = pipe.to("cuda")
            
            image = pipe(prompt).images[0]
            return image
        except Exception as e:
            raise Exception(f"Stable Diffusion error: {str(e)}")

    async def generate_dalle(self, prompt):
        """Generate image using DALL-E 3"""
        try:
            if not self.openai_api_key:
                raise Exception("OpenAI API key not found")

            response = await openai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            # Download the image
            image_url = response.data[0].url
            image_data = requests.get(image_url).content
            image = Image.open(io.BytesIO(image_data))
            return image
        except Exception as e:
            raise Exception(f"DALL-E error: {str(e)}")

    async def generate_midjourney(self, prompt):
        """Generate image using Midjourney via Discord bot"""
        try:
            if not self.discord_token or not self.discord_channel_id:
                raise Exception("Discord credentials not found")

            # Send prompt to Discord channel
            channel = self.discord_client.get_channel(int(self.discord_channel_id))
            await channel.send(f"/imagine prompt: {prompt}")

            # In a real implementation, you would need to:
            # 1. Wait for Midjourney to generate the image
            # 2. Capture the generated image URL
            # 3. Download and return the image
            
            raise Exception("Midjourney integration requires full Discord bot implementation")
        except Exception as e:
            raise Exception(f"Midjourney error: {str(e)}")

    async def generate_runway(self, prompt):
        """Generate video using Runway Gen-2"""
        try:
            if not self.runway_api_key:
                raise Exception("Runway API key not found")

            url = "https://api.runwayml.com/v1/generation/text-to-video"
            headers = {
                "Authorization": f"Bearer {self.runway_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "prompt": prompt,
                "num_frames": 30,
                "fps": 30
            }
            
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                # In a real implementation, you would:
                # 1. Handle the video data appropriately
                # 2. Save or stream the video
                video_data = response.content
                return video_data
            else:
                raise Exception(f"Runway API error: {response.text}")
        except Exception as e:
            raise Exception(f"Runway error: {str(e)}")

    async def generate_pika(self, prompt):
        """Generate video using Pika Labs"""
        try:
            if not self.pika_api_key:
                raise Exception("Pika Labs API key not found")

            url = "https://api.pika.art/v1/generate"
            headers = {
                "Authorization": f"Bearer {self.pika_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "prompt": prompt,
                "negative_prompt": "",
                "steps": 30,
                "cfg_scale": 7.5,
                "seed": -1
            }
            
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                # In a real implementation, you would:
                # 1. Handle the video data
                # 2. Save or stream the video
                video_data = response.content
                return video_data
            else:
                raise Exception(f"Pika Labs API error: {response.text}")
        except Exception as e:
            raise Exception(f"Pika Labs error: {str(e)}")
