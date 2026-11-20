import streamlit as st
from google import genai
from PIL import Image
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="AI Image-to-Content Automator", page_icon="🚀")
st.title("📸 Image-to-Text & Content Generator")
st.write("Upload an image to extract text, generate content, and auto-save to Google Sheets.")

# --- AUTHENTICATION (Using Streamlit Secrets) ---
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_resource
def init_gsheets():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)
    # Open the Google Sheet by exact name
    return gc.open("AI_Content_Logs").sheet1

sheet = init_gsheets()

# --- USER INTERFACE ---
uploaded_file = st.file_uploader("Upload an Image (JPG, PNG, WEBP)", type=["jpg", "jpeg", "png", "webp"])
content_type = st.selectbox(
    "Select Content to Generate:",
    ["Social Media Post (Facebook/LinkedIn)", "SEO Blog Summary", "Product Description", "Just Extract Raw Text"]
)
custom_instructions = st.text_input("Optional custom instructions (e.g., 'Write in Bengali' or 'Keep it under 100 words'):")

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_container_width=True)

    if st.button("✨ Extract, Generate & Save"):
        with st.spinner("Processing image with Gemini AI..."):
            try:
                # Step A: Extract Text (OCR)
                ocr_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[image, "Extract all visible text from this image accurately. If there is no text, describe the image in detail."]
                )
                extracted_text = ocr_response.text

                # Step B: Generate Content
                if content_type == "Just Extract Raw Text":
                    generated_content = extracted_text
                else:
                    prompt = f"Based on the following extracted text/context, write a compelling {content_type}. {custom_instructions}\n\nContext:\n{extracted_text}"
                    gen_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )
                    generated_content = gen_response.text

                # Step C: Save to Google Sheets
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet.append_row([timestamp, uploaded_file.name, extracted_text, generated_content])

                # Display Results
                st.success("✅ Saved to Google Sheets successfully!")
                
                with st.expander("📄 View Extracted Text", expanded=True):
                    st.write(extracted_text)
                
                st.subheader("✍️ Generated Content")
                st.write(generated_content)

            except Exception as e:
                st.error(f"An error occurred: {e}")
