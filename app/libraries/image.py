import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from PIL import Image as PILImage
from io import BytesIO

class Image:
  def __init__(self):
    load_dotenv()
    
    self.cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
    self.api_key = os.getenv('CLOUDINARY_API_KEY')
    self.api_secret = os.getenv('CLOUDINARY_API_SECRET')

    cloudinary.config(
      cloud_name=self.cloud_name,
      api_key=self.api_key,
      api_secret=self.api_secret
    )

  def compress_image(self, image_path_or_file, user_id, quality=85):
    """
    Compress the image by reducing its quality and saving it in WebP format.
    The filename will be <user_id>-profile.webp.
    """
    try:
      if isinstance(image_path_or_file, str):
        image = PILImage.open(image_path_or_file)
      else:
        image = PILImage.open(image_path_or_file.stream)
  
      filename = f"{user_id}"

      img_byte_arr = BytesIO()
      image.save(img_byte_arr, format='WEBP', quality=quality)
      img_byte_arr.seek(0)
      return img_byte_arr, filename
        
    except Exception as e:
      print(f"Error compressing image: {str(e)}")
      return None, None

  def upload_to_cloudinary(self, image_path_or_file, user_id, quality=85):
    """
    Compress the image using the compress_image function and upload it to Cloudinary.
    If the image already exists, it will be replaced.
    """
    try:
      compressed_image, filename = self.compress_image(image_path_or_file, user_id, quality)

      if not compressed_image:
        print("Compression failed")
        return None

      folder_path = f"/users/{user_id}/"
      
      upload_result = cloudinary.uploader.upload(
        compressed_image,
        folder=folder_path,
        public_id=filename,
        resource_type="auto",
        overwrite=True
      )
      
      return upload_result
    
    except Exception as e:
      print(f"Error uploading to Cloudinary: {str(e)}")
      return None

  def get_default_image_path(self):
    """
    Get the path for the default image stored in the assets folder.
    """
    default_image_path = os.path.join(os.getcwd(), 'assets', 'default.webp')
    return default_image_path

  def delete_from_cloudinary(self, user_id):
    """
    Delete the current user profile image from Cloudinary and replace it with the default image.
    """
    try:
      default_image_path = self.get_default_image_path()

      folder_path = f"/users/{user_id}/"
      profile_image_public_id = f"{user_id}-profile.webp"
      cloudinary.uploader.destroy(
        f"{folder_path}{profile_image_public_id}",
        resource_type="auto"
      )
      print(f"Deleted existing profile image: {profile_image_public_id}")

      upload_result = self.upload_to_cloudinary(default_image_path, user_id)

      if upload_result:
        print("Profile image replaced with default image")
      else:
        print("Failed to upload default image")

      return upload_result
    
    except Exception as e:
      print(f"Error deleting image from Cloudinary: {str(e)}")
      return None
