
import os
import io
import time
import base64
import uuid
from PIL import Image
from werkzeug.utils import secure_filename

class ImageHandler:
    @staticmethod
    def compress_image(image_path, max_size=(300, 300), quality=85, output_format='JPEG'):
        """Compress an image from path and return the compressed image as bytes"""
        try:
            with Image.open(image_path) as img:
                img.thumbnail(max_size, Image.LANCZOS)
                
                # Convert to RGB if RGBA (remove transparency for JPEG)
                if img.mode == 'RGBA' and output_format == 'JPEG':
                    img = img.convert('RGB')
                
                # Save to bytes buffer
                buffer = io.BytesIO()
                img.save(buffer, format=output_format, quality=quality, optimize=True)
                return buffer.getvalue()
        except Exception as e:
            print(f"Error compressing image: {str(e)}")
            return None
    
    @staticmethod
    def compress_from_file_object(file_object, max_size=(300, 300), quality=85, output_format='JPEG'):
        """Compress an image from a file object and return the compressed image as bytes"""
        try:
            file_object.seek(0)  # Ensure we're at the start of the file
            with Image.open(file_object) as img:
                img.thumbnail(max_size, Image.LANCZOS)
                
                # Convert to RGB if RGBA (remove transparency for JPEG)
                if img.mode == 'RGBA' and output_format == 'JPEG':
                    img = img.convert('RGB')
                
                # Save to bytes buffer
                buffer = io.BytesIO()
                img.save(buffer, format=output_format, quality=quality, optimize=True)
                return buffer.getvalue()
        except Exception as e:
            print(f"Error compressing image from file object: {str(e)}")
            return None
    
    @staticmethod
    def generate_unique_filename(username, extension='.jpg'):
        """Generate a unique filename for profile pictures"""
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        return secure_filename(f"{username}_{timestamp}_{unique_id}{extension}")
    
    @staticmethod
    def save_profile_picture(username, file_object, upload_dir='static/uploads'):
        """Save a compressed profile picture and return the path"""
        try:
            # Ensure upload directory exists
            os.makedirs(upload_dir, exist_ok=True)
            
            # Compress the image
            compressed_data = ImageHandler.compress_from_file_object(
                file_object, 
                max_size=(300, 300),
                quality=85
            )
            
            if not compressed_data:
                return None
                
            # Generate a unique filename
            filename = ImageHandler.generate_unique_filename(username)
            file_path = os.path.join(upload_dir, filename)
            
            # Save the compressed image
            with open(file_path, 'wb') as f:
                f.write(compressed_data)
                
            return f'/static/uploads/{filename}'
        except Exception as e:
            print(f"Error saving profile picture: {str(e)}")
            return None
