import streamlit as st
import pandas as pd
import pypdf
import docx
import google.generativeai as genai
import os
from dotenv import load_dotenv

# --- Configuration and Setup ---
st.set_page_config(page_title="AetherFit AI Assistant", page_icon="🤖", layout="wide")
st.title("🤖 AetherFit AI Assistant")
st.caption("Your personal guide to AetherFit products. Ask me anything!")

# --- Caching, Data Loading, and Image Mapping ---
@st.cache_resource
def load_all_data():
    """Loads all data sources and creates a product-to-image mapping."""
    st.write("First time setup: Loading knowledge base from files...")
    
    # Define file paths
    pdf_path = 'AetherFit_Product_Catalog_2024.pdf'
    csv_path = 'AetherFit_Inventory_Pricing.csv'
    docx_path = 'AetherFit_User_Reviews.docx'
    
    # --- Extraction Functions ---
    def extract_from_pdf(file_path):
        try:
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                return "".join(page.extract_text() for page in reader.pages)
        except Exception: return f"Error: Could not read {os.path.basename(file_path)}."

    def extract_from_csv(file_path):
        try:
            return pd.read_csv(file_path).to_string()
        except Exception: return f"Error: Could not read {os.path.basename(file_path)}."

    def extract_from_docx(file_path):
        try:
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception: return f"Error: Could not read {os.path.basename(file_path)}."

    # --- Create Image Mapping (NEW) ---
    try:
        df = pd.read_csv(csv_path)
        # Create a dictionary mapping ProductID to ImagePath: {'AFT-101': 'images/T1000.jpg', ...}
        image_map = df.set_index('ProductID')['ImagePath'].dropna().to_dict()
    except Exception:
        image_map = {}

    # --- Combine data into a single context string ---
    pdf_data = extract_from_pdf(pdf_path)
    csv_data = extract_from_csv(csv_path)
    docx_data = extract_from_docx(docx_path)
    
    knowledge_base = f"""
    --- START PRODUCT CATALOG DATA ---
    {pdf_data}
    --- END PRODUCT CATALOG DATA ---
    --- START INVENTORY & PRICING DATA ---
    {csv_data}
    --- END INVENTORY & PRICING DATA ---
    --- START USER REVIEW DATA ---
    {docx_data}
    --- END USER REVIEW DATA ---
    """
    return knowledge_base, image_map

@st.cache_resource
def configure_ai_model():
    """Loads API key and configures the Gemini model."""
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("Google API Key not found! Please set it in your .env file.")
        st.stop()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash-latest')

# --- Main App Logic ---
knowledge_base, image_map = load_all_data()
model = configure_ai_model()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # NEW: If an image was associated with the message, display it
        if "image" in message:
            st.image(message["image"])

# --- Chat Input and Response Generation ---
def get_ai_response(question, context):
    prompt = f"""
    You are an expert AI assistant for 'AetherFit'. Your task is to answer questions.
    **CRITICAL RULE: Answer based ONLY on the provided context. If the information is not in the context, say 'I do not have that information in my provided data.' Crucially, when you mention a product, ALWAYS include its ProductID in parentheses, for example: Pro-Treadmill T1000 (AFT-101).**
    CONTEXT: {context}
    QUESTION: {question}
    ANSWER:
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e: return f"An error occurred: {e}"

def find_image_for_response(response_text, image_mapping):
    """Checks if a ProductID from the response text has a corresponding image."""
    for product_id, image_path in image_mapping.items():
        if product_id in response_text:
            if os.path.exists(image_path):
                return image_path
    return None

if prompt := st.chat_input("Ask about the Pro-Treadmill T1000..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_text = get_ai_response(prompt, knowledge_base)
            image_to_display = find_image_for_response(response_text, image_map)
            
            st.markdown(response_text)
            if image_to_display:
                st.image(image_to_display, width=300)

    # Add the full response (text and image path) to history
    message_to_save = {"role": "assistant", "content": response_text}
    if image_to_display:
        message_to_save["image"] = image_to_display
    st.session_state.messages.append(message_to_save)