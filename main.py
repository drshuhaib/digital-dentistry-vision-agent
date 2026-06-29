import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

# Load API key from the .env file
load_dotenv()

# Connect to NVIDIA's AI servers
client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=os.environ.get("NVIDIA_API_KEY")
)

def analyze_clinical_image(image_path):
    """Reads a dental image and asks the AI to analyze it."""
    print(f"Loading {image_path}...")
    
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    print("Sending to NVIDIA Vision Model for analysis...")
    
    # Send the instruction and the image to the AI
    response = client.chat.completions.create(
        model="meta/llama-3.2-11b-vision-instruct", # 🔴 UPDATED: This model has "eyes"!
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "You are a digital dentistry AI assistant. Look closely at this image. First, explicitly state that you see BOTH arches (Maxillary and Mandibular) in occlusion. Next, analyze the visible teeth for crowding, note the presence of any clear aligner attachments on the tooth surfaces, and identify any rotational misalignments. Provide a brief clinical summary."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        max_tokens=500
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    image_filename = "test_image.jpg"
    
    if os.path.exists(image_filename):
        result = analyze_clinical_image(image_filename)
        print("\n=== CLINICAL AI REPORT ===")
        print(result)
        print("==========================")
    else:
        print(f"\nError: Could not find '{image_filename}'. Please check the spelling.")