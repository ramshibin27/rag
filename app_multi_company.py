import streamlit as st
import pandas as pd
import pypdf
import docx
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

# --- CONFIGURATION ---

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("Google API Key not found. Please set it in your .env file.")
    st.stop()
genai.configure(api_key=api_key)

# Define company-specific data paths and names
# (This is the NEW, CORRECTED code)
COMPANY_CONFIG = {
    "aetherfit": {
        "name": "AetherFit (Fitness Equipment)",
        "path": "data/aetherfit",
        "image_path": "images"  # <--- CORRECTED PATH
    },
    "terratiles": {
        "name": "TerraTiles (Luxury Tiles)",
        "path": "data/terratiles",
    
        "image_path": "data/terratiles/images"
    },
}
# --- DATA EXTRACTION (Now dynamic based on company) ---

def get_file_path(company_path, file_name):
    return os.path.join(company_path, file_name)

# Using st.cache_data to avoid reloading data on every interaction
@st.cache_data(show_spinner="Loading knowledge base...")
def build_context(company_key):
    """Extracts data from all sources for the selected company and combines it."""
    config = COMPANY_CONFIG[company_key]
    company_path = config["path"]
    
    context_parts = []
    
    # 1. Extract from PDF
    try:
        pdf_path = get_file_path(company_path, "catalog.pdf")
        with open(pdf_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            pdf_text = "".join(page.extract_text() for page in reader.pages)
            context_parts.append(f"--- START PDF CATALOG ---\n{pdf_text}\n--- END PDF CATALOG ---")
    except Exception as e:
        st.warning(f"Could not load catalog.pdf: {e}")

    # 2. Extract from CSV
    try:
        csv_path = get_file_path(company_path, "inventory.csv")
        df = pd.read_csv(csv_path)
        context_parts.append(f"--- START CSV INVENTORY/PRICING ---\n{df.to_string()}\n--- END CSV INVENTORY/PRICING ---")
    except Exception as e:
        st.warning(f"Could not load inventory.csv: {e}")

    # 3. Extract from DOCX
    try:
        docx_path = get_file_path(company_path, "reviews.docx")
        doc = docx.Document(docx_path)
        docx_text = "\n".join([para.text for para in doc.paragraphs])
        context_parts.append(f"--- START DOCX REVIEWS ---\n{docx_text}\n--- END DOCX REVIEWS ---")
    except Exception as e:
        st.warning(f"Could not load reviews.docx: {e}")
        
    return "\n\n".join(context_parts)

# --- LLM INTERACTION (With Image Handling Logic) ---

def ask_assistant(question, context, company_key):
    """Formats the prompt, sends it to the LLM, and includes image instructions."""
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    # NEW INSTRUCTION FOR THE LLM!
    prompt = f"""
    You are an AI assistant for the company '{COMPANY_CONFIG[company_key]['name']}'.
    
    **CRITICAL RULES:**
    1. Answer the user's question based ONLY on the provided context. If the information is not in the context, you MUST say 'I do not have that information in my provided data.'
    2. When a user asks about a specific product that has an image file listed in the CSV data, you MUST include a special tag in your response: [IMAGE: filename.jpg]. For example, if the user asks about 'PowerCycle C500' and its image is 'C500.jpg', part of your response must be '[IMAGE: C500.jpg]'.
    3. Do not show the image tag for products that do not have an image file listed.
    
    CONTEXT:
    {context}

    QUESTION:
    {question}
    
    ANSWER:
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

# --- STREAMLIT UI ---

st.set_page_config(layout="wide")
st.title("🤖 AI Assistant for Companies")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = {}

# Sidebar for company selection
st.sidebar.title("Configuration")
selected_company_key = st.sidebar.selectbox(
    "Choose a company to chat with:",
    options=list(COMPANY_CONFIG.keys()),
    format_func=lambda key: COMPANY_CONFIG[key]["name"]
)

# Load context for the selected company
knowledge_base = build_context(selected_company_key)

# Initialize chat history for the selected company if it doesn't exist
if selected_company_key not in st.session_state.messages:
    st.session_state.messages[selected_company_key] = [
        {"role": "assistant", "content": f"Hello! How can I help you with {COMPANY_CONFIG[selected_company_key]['name']} today?"}
    ]

# Display chat messages
for message in st.session_state.messages[selected_company_key]:
    with st.chat_message(message["role"]):
        # This part handles displaying content that might have an image
        if "image" in message:
            st.image(message["image"])
        st.markdown(message["content"])

# Main chat input
if prompt := st.chat_input(f"Ask about {COMPANY_CONFIG[selected_company_key]['name']}..."):
    # Add user message to chat history
    st.session_state.messages[selected_company_key].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            full_response = ask_assistant(prompt, knowledge_base, selected_company_key)
            
            # Use regex to find the image tag
            image_match = re.search(r"\[IMAGE: (.*?)\]", full_response)
            
            # Clean the response text by removing the tag
            cleaned_response = re.sub(r"\[IMAGE: (.*?)\]", "", full_response).strip()
            
            response_data = {"role": "assistant", "content": cleaned_response}
            
            # If an image tag was found, find and display the image
            if image_match:
                image_filename = image_match.group(1)
                # This path needs to be correct based on your folder structure
                image_path = os.path.join(COMPANY_CONFIG[selected_company_key]["image_path"], image_filename)
                
                if os.path.exists(image_path):
                    st.image(image_path)
                    # We can store the path in the message dict if needed, but displaying it directly is fine
                else:
                    # If image file is listed but not found, inform the user.
                    st.warning(f"Image '{image_filename}' not found at path '{image_path}'.")
            
            st.markdown(cleaned_response)
            st.session_state.messages[selected_company_key].append(response_data)