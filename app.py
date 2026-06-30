import streamlit as st
import os
import base64
import requests
from dotenv import load_dotenv
from PIL import Image
import io

# Load the secret NVIDIA API key from your .env vault
load_dotenv()
API_KEY = os.environ.get("NVIDIA_API_KEY")

# Set up the web page styling
st.set_page_config(page_title="Vision Agent", page_icon="🦷", layout="centered")

st.title("🦷 Digital Dentistry Vision Agent")
st.write("Upload an intraoral scan, cephalometric image, or clinical photograph for automated analysis.")

# --- NEW: Dynamic Diagnostic Profiles ---
image_type = st.selectbox(
    "Select the type of clinical image:",
    ["Intraoral Photo / Clear Aligner Tracking", "Lateral Cephalogram", "Panoramic Radiograph (OPG)"]
)

# Map the selection to a highly specific clinical prompt
prompts = {
    "Intraoral Photo / Clear Aligner Tracking": "Analyze this intraoral dental image. Identify crowding, rotational misalignments, hygiene status, and the presence of any clear aligner attachments. Provide a clinical summary.",
    "Lateral Cephalogram": "Analyze this lateral cephalometric radiograph. Evaluate the skeletal classification (Class I, II, or III), incisor inclination, soft tissue profile, and any notable anatomical landmarks. Provide a clinical summary.",
    "Panoramic Radiograph (OPG)": "Analyze this panoramic radiograph (OPG). Evaluate general bone levels, identify any impacted teeth (such as third molars), and note any apparent pathology, existing restorations, or missing teeth. Provide a clinical summary."
}
selected_prompt = prompts[image_type]
# ----------------------------------------

# Create the drag-and-drop upload box
uploaded_file = st.file_uploader("Select a clinical image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Show the high-res image on the screen once uploaded
    st.image(uploaded_file, caption=f"Uploaded: {image_type}", use_container_width=True)
    
    # Create a button to trigger the AI
    if st.button("Generate Clinical AI Report", type="primary"):
        
        # Show a loading spinner while the AI thinks
        with st.spinner(f"Analyzing {image_type.lower()}..."):
            
            try:
                # 1. Open the uploaded image
                img = Image.open(uploaded_file)
                
                # 2. Convert PNGs (which have transparency) to standard RGB JPEGs
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # 3. Resize the image to standard AI dimensions (max 1024px)
                img.thumbnail((1024, 1024))
                
                # 4. Save to a temporary buffer
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=85)
                
                # 5. Convert to base64
                image_b64 = base64.b64encode(buffered.getvalue()).decode()
                mime_type = "image/jpeg"
                
                # Prepare the request to the NVIDIA NIM Vision Model
                invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "Accept": "application/json"
                }
                
                payload = {
                    "model": "meta/llama-3.2-90b-vision-instruct",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    # Insert the dynamically selected prompt here
                                    "text": selected_prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{image_b64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 1024,
                    "temperature": 0.2
                }
                
                # Send the request and display the result
                response = requests.post(invoke_url, headers=headers, json=payload)
                
                # Check if the API request was successful
                if response.status_code == 200:
                    response_data = response.json()
                    ai_report = response_data["choices"][0]["message"]["content"]
                    
                    st.divider()
                    st.subheader("📋 Clinical AI Report")
                    st.info(f"**Diagnostic Framework Used:** {image_type}")
                    st.write(ai_report)
                else:
                    st.error(f"API Error ({response.status_code}): Something went wrong.")
                    st.write(response.json())
                    
            except Exception as e:
                st.error("There was a system error processing the image.")
                st.write(e)
                