import streamlit as st
import os
import base64
import requests
from dotenv import load_dotenv
from PIL import Image
import io
from fpdf import FPDF
from streamlit_image_coordinates import streamlit_image_coordinates

# Load the secret NVIDIA API key
load_dotenv()
API_KEY = os.environ.get("NVIDIA_API_KEY")

# PDF Generation Function
def create_pdf(report_text, image_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Clinical AI Report", ln=True, align='C')
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(0, 10, f"Diagnostic Framework: {image_type}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    safe_text = report_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, safe_text)
    return bytes(pdf.output())

# Set up the web page styling
st.set_page_config(page_title="Vision Agent", page_icon="🦷", layout="centered")
st.title("🦷 Digital Dentistry Vision Agent")
st.write("Upload an intraoral scan, cephalometric image, or clinical photograph for automated analysis.")

# Dynamic Diagnostic Profiles
image_type = st.selectbox(
    "Select the type of clinical image:",
    ["Intraoral Photo / Clear Aligner Tracking", "Lateral Cephalogram", "Panoramic Radiograph (OPG)"]
)

prompts = {
    "Intraoral Photo / Clear Aligner Tracking": "Analyze this intraoral dental image. Identify crowding, rotational misalignments, hygiene status, and the presence of any clear aligner attachments. Provide a clinical summary.",
    "Lateral Cephalogram": "Analyze this lateral cephalometric radiograph. Evaluate the skeletal classification (Class I, II, or III), incisor inclination, soft tissue profile, and any notable anatomical landmarks. Provide a clinical summary.",
    "Panoramic Radiograph (OPG)": "Analyze this panoramic radiograph (OPG). Evaluate general bone levels, identify any impacted teeth (such as third molars), and note any apparent pathology, existing restorations, or missing teeth. Provide a clinical summary."
}
selected_prompt = prompts[image_type]

# Create the drag-and-drop upload box
uploaded_file = st.file_uploader("Select a clinical image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Process the image
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    st.divider()
    st.write("🎯 **CEPHALOMETRIC ENGINE TEST:**")
    st.write("Hover over the image and click anywhere to test the coordinate tracker.")
    
    # --- THE INTERACTIVE IMAGE COMPONENT ---
    clicked_points = streamlit_image_coordinates(img, key="ceph_clicker")
    
    # Show the coordinates when clicked
    if clicked_points is not None:
        st.success(f"📍 Point captured! X: {clicked_points['x']} | Y: {clicked_points['y']}")
    # ---------------------------------------
    
    st.divider()
    
    # The original AI Report Button
    if st.button("Generate Clinical AI Report", type="primary"):
        with st.spinner(f"Analyzing {image_type.lower()}..."):
            try:
                img.thumbnail((1024, 1024))
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=85)
                image_b64 = base64.b64encode(buffered.getvalue()).decode()
                mime_type = "image/jpeg"
                
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
                                {"type": "text", "text": selected_prompt},
                                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}}
                            ]
                        }
                    ],
                    "max_tokens": 1024,
                    "temperature": 0.2
                }
                
                response = requests.post(invoke_url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    response_data = response.json()
                    ai_report = response_data["choices"][0]["message"]["content"]
                    
                    st.subheader("📋 Clinical AI Report")
                    st.info(f"**Diagnostic Framework Used:** {image_type}")
                    st.write(ai_report)
                    
                    pdf_bytes = create_pdf(ai_report, image_type)
                    st.download_button(
                        label="📄 Download Report as PDF",
                        data=pdf_bytes,
                        file_name="Clinical_AI_Report.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                else:
                    st.error(f"API Error ({response.status_code}): Something went wrong.")
            except Exception as e:
                st.error("There was a system error processing the image.")
                st.write(e)
                