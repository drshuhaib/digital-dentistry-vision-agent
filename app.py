import streamlit as st
import os
import base64
import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw
import io
import math
from fpdf import FPDF
from streamlit_image_coordinates import streamlit_image_coordinates

# Load the secret NVIDIA API key
load_dotenv()
API_KEY = os.environ.get("NVIDIA_API_KEY")

# ==========================================
# MATHEMATICAL CEPHALOMETRIC ENGINE
# ==========================================
def calculate_angle_3_points(p1, vertex, p2):
    angle = math.degrees(math.atan2(p2[1] - vertex[1], p2[0] - vertex[0]) - 
                         math.atan2(p1[1] - vertex[1], p1[0] - vertex[0]))
    angle = abs(angle)
    if angle > 180:
        angle = 360 - angle
    return round(angle, 2)

def calculate_angle_between_lines(line1_p1, line1_p2, line2_p1, line2_p2):
    angle1 = math.atan2(line1_p2[1] - line1_p1[1], line1_p2[0] - line1_p1[0])
    angle2 = math.atan2(line2_p2[1] - line2_p1[1], line2_p2[0] - line2_p1[0])
    angle = math.degrees(angle1 - angle2)
    angle = abs(angle)
    if angle > 180:
        angle = 360 - angle
    if angle > 90 and angle < 180:
        angle = 180 - angle
    return round(angle, 2)

def run_steiner_analysis(points):
    sna = calculate_angle_3_points(points["S"], points["N"], points["A"])
    snb = calculate_angle_3_points(points["S"], points["N"], points["B"])
    anb = round(sna - snb, 2)
    
    u1_na_angle = calculate_angle_between_lines(points["U1A"], points["U1T"], points["N"], points["A"])
    l1_nb_angle = calculate_angle_between_lines(points["L1A"], points["L1T"], points["N"], points["B"])
    
    if anb > 4.0:
        diagnosis = "Class II Skeletal Pattern"
    elif anb < 0.0:
        diagnosis = "Class III Skeletal Pattern"
    else:
        diagnosis = "Class I Skeletal Pattern"
        
    return {
        "Diagnosis": diagnosis,
        "SNA": sna, "SNB": snb, "ANB": anb,
        "U1_NA": u1_na_angle, "L1_NB": l1_nb_angle
    }

# ==========================================
# PDF GENERATION FUNCTION
# ==========================================
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

# ==========================================
# PAGE SETUP & STYLING
# ==========================================
st.set_page_config(page_title="Vision Agent", page_icon="🦷", layout="centered")
st.title("🦷 Digital Dentistry Vision Agent")
st.write("Upload an intraoral scan, cephalometric image, or clinical photograph for automated analysis.")

image_type = st.selectbox(
    "Select the type of clinical image:",
    ["Lateral Cephalogram", "Intraoral Photo / Clear Aligner Tracking", "Panoramic Radiograph (OPG)"]
)

prompts = {
    "Intraoral Photo / Clear Aligner Tracking": "Analyze this intraoral dental image. Identify crowding, rotational misalignments, hygiene status, and the presence of any clear aligner attachments. Provide a clinical summary.",
    "Lateral Cephalogram": "Analyze this lateral cephalometric radiograph. Evaluate the skeletal classification (Class I, II, or III), incisor inclination, soft tissue profile, and any notable anatomical landmarks. Provide a clinical summary.",
    "Panoramic Radiograph (OPG)": "Analyze this panoramic radiograph (OPG). Evaluate general bone levels, identify any impacted teeth (such as third molars), and note any apparent pathology, existing restorations, or missing teeth. Provide a clinical summary."
}
selected_prompt = prompts[image_type]

uploaded_file = st.file_uploader("Select a clinical image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    original_img = Image.open(uploaded_file)
    if original_img.mode in ("RGBA", "P"):
        original_img = original_img.convert("RGB")
        
    # Standardize image size for coordinate mapping
    max_width = 800
    if original_img.width > max_width:
        ratio = max_width / original_img.width
        new_size = (max_width, int(original_img.height * ratio))
        original_img = original_img.resize(new_size, Image.Resampling.LANCZOS)
        
    img_for_drawing = original_img.copy()
    
    st.divider()
    
    # ==========================================
    # INTERACTIVE CLINICAL WORKFLOW
    # ==========================================
    if image_type == "Lateral Cephalogram":
        st.subheader("📐 Quantitative Cephalometric Engine")
        
        required_landmarks = ["S", "N", "A", "B", "U1A", "U1T", "L1A", "L1T"]
        landmark_names = {
            "S": "Sella (S) - Center of pituitary fossa",
            "N": "Nasion (N) - Anterior frontonasal suture",
            "A": "Point A - Deepest curve of maxilla",
            "B": "Point B - Deepest curve of mandible",
            "U1A": "Upper Incisor Apex (Root tip)",
            "U1T": "Upper Incisor Tip (Incisal edge)",
            "L1A": "Lower Incisor Apex (Root tip)",
            "L1T": "Lower Incisor Tip (Incisal edge)"
        }
        
        # --- NEW: Anatomical Line Drawings & Descriptions ---
        landmark_visuals = {
            "S": {"desc": "Look dead center in the skull base for a bright white U-shaped 'bowl' (sella turcica). Do not click the bone; click the exact geometric center of the empty space inside the bowl.", 
                  "svg": """<svg viewBox="0 0 100 80" width="100" height="80"><path d="M 10 20 Q 30 20 40 40 C 40 80, 80 80, 80 40 Q 90 20 100 20" fill="none" stroke="#666" stroke-width="4"/><circle cx="60" cy="45" r="5" fill="lime" stroke="black" stroke-width="2"/></svg>"""},
            "N": {"desc": "Follow the forehead profile down to the bridge of the nose. Find the V-shaped notch where the frontal bone meets the nasal bone, and click the deepest point.", 
                  "svg": """<svg viewBox="0 0 100 80" width="100" height="80"><path d="M 80 10 Q 50 40 40 50 Q 30 60 70 90" fill="none" stroke="#666" stroke-width="4"/><circle cx="40" cy="50" r="5" fill="lime" stroke="black" stroke-width="2"/></svg>"""},
            "A": {"desc": "Look at the front of the upper jaw, between the nose and the upper teeth. Find the most concave (inward curving) point of the bone profile.", 
                  "svg": """<svg viewBox="0 0 100 80" width="100" height="80"><path d="M 80 10 Q 20 50 60 90" fill="none" stroke="#666" stroke-width="4"/><circle cx="36" cy="50" r="5" fill="lime" stroke="black" stroke-width="2"/></svg>"""},
            "B": {"desc": "Look at the front of the lower jaw, just above the chin. Find the deepest concave curve of the bone profile.", 
                  "svg": """<svg viewBox="0 0 100 80" width="100" height="80"><path d="M 60 10 Q 20 40 80 90" fill="none" stroke="#666" stroke-width="4"/><circle cx="36" cy="40" r="5" fill="lime" stroke="black" stroke-width="2"/></svg>"""},
            "U1A": {"desc": "Click the very tip of the root (apex) of the most prominent upper central incisor.", 
                  "svg": """<svg viewBox="0 0 100 80" width="100" height="80"><path d="M 40 10 L 60 10 L 70 70 L 30 70 Z" fill="none" stroke="#666" stroke-width="3"/><circle cx="50" cy="10" r="5" fill="lime" stroke="black" stroke-width="2"/></svg>"""},
            "U1T": {"desc": "Click the exact biting edge (incisal tip) of the most prominent upper central incisor.", 
                  "svg": """<svg viewBox="0 0 100 80" width="100" height="80"><path d="M 40 10 L 60 10 L 70 70 L 30 70 Z" fill="none" stroke="#666" stroke-width="3"/><circle cx="50" cy="70" r="5" fill="lime" stroke="black" stroke-width="2"/></svg>"""},
            "L1A": {"desc": "Click the very tip of the root (apex) of the most prominent lower central incisor.", 
                  "svg": """<svg viewBox="0 0 100 80" width="100" height="80"><path d="M 30 10 L 70 10 L 60 70 L 40 70 Z" fill="none" stroke="#666" stroke-width="3"/><circle cx="50" cy="70" r="5" fill="lime" stroke="black" stroke-width="2"/></svg>"""},
            "L1T": {"desc": "Click the exact biting edge (incisal tip) of the most prominent lower central incisor.", 
                  "svg": """<svg viewBox="0 0 100 80" width="100" height="80"><path d="M 30 10 L 70 10 L 60 70 L 40 70 Z" fill="none" stroke="#666" stroke-width="3"/><circle cx="50" cy="10" r="5" fill="lime" stroke="black" stroke-width="2"/></svg>"""}
        }
        # --------------------------------------------------------
        
        if 'placed_landmarks' not in st.session_state:
            st.session_state.placed_landmarks = {}
            
        current_index = len(st.session_state.placed_landmarks)
        
        # Workflow Prompting with Layout
        if current_index < len(required_landmarks):
            next_point = required_landmarks[current_index]
            
            # Split the UI so the drawing sits neatly next to the instructions
            col_text, col_drawing = st.columns([3, 1])
            with col_text:
                st.warning(f"📍 **Action Required:** Click to place **{landmark_names[next_point]}**")
                st.write(f"*{landmark_visuals[next_point]['desc']}*")
            with col_drawing:
                st.markdown(landmark_visuals[next_point]['svg'], unsafe_allow_html=True)
        else:
            st.success("✅ All landmarks placed! Analysis generated below.")
            
        # Draw the points
        draw = ImageDraw.Draw(img_for_drawing)
        for key, (x, y) in st.session_state.placed_landmarks.items():
            r = 8 
            draw.ellipse((x-r, y-r, x+r, y+r), fill="lime", outline="black", width=2)
            
        clicked = streamlit_image_coordinates(img_for_drawing, key="ceph_clicker_static")
        
        # Capture logic
        if clicked is not None:
            if current_index < len(required_landmarks):
                next_point = required_landmarks[current_index]
                new_point = (clicked['x'], clicked['y'])
                
                if new_point not in st.session_state.placed_landmarks.values():
                    st.session_state.placed_landmarks[next_point] = new_point
                    st.rerun()
                    
        # Reset Button
        if st.session_state.placed_landmarks:
            if st.button("Reset Landmarks"):
                st.session_state.placed_landmarks = {}
                st.rerun()
                
        # Generate the Math Dashboard when complete
        if len(st.session_state.placed_landmarks) == len(required_landmarks):
            st.divider()
            results = run_steiner_analysis(st.session_state.placed_landmarks)
            
            st.subheader("📊 Steiner Analysis Results")
            st.info(f"**Clinical Conclusion:** {results['Diagnosis']}")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("SNA Angle (Norm: 82°)", f"{results['SNA']}°")
            col2.metric("SNB Angle (Norm: 80°)", f"{results['SNB']}°")
            col3.metric("ANB Angle (Norm: 2°)", f"{results['ANB']}°")
            
            col4, col5 = st.columns(2)
            col4.metric("U1 to NA (Norm: 22°)", f"{results['U1_NA']}°")
            col5.metric("L1 to NB (Norm: 25°)", f"{results['L1_NB']}°")
            
    else:
        st.info("The interactive Cephalometric Engine is only available when 'Lateral Cephalogram' is selected.")
        st.image(original_img, use_container_width=True)

    st.divider()
    
    # ==========================================
    # AI VISION MODEL (Qualitative Report)
    # ==========================================
    if st.button("Generate Qualitative AI Report", type="primary"):
        with st.spinner(f"Analyzing {image_type.lower()}..."):
            try:
                clean_img = original_img.copy()
                clean_img.thumbnail((1024, 1024))
                buffered = io.BytesIO()
                clean_img.save(buffered, format="JPEG", quality=85)
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
                    
                    st.subheader("📋 Qualitative AI Report")
                    st.info(f"**Diagnostic Framework Used:** {image_type}")
                    st.write(ai_report)
                    
                    pdf_bytes = create_pdf(ai_report, image_type)
                    st.download_button(
                        label="📄 Download AI Report as PDF",
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
                