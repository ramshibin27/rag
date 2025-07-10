# import streamlit as st
# import pandas as pd
# import pypdf
# import docx
# import google.generativeai as genai
# import os
# import re
# # --- THIS IS THE NEW, CORRECT CODE ---

# # Load the API key from Streamlit's secrets manager
# try:
#     api_key = st.secrets["GOOGLE_API_KEY"]
# except KeyError:
#     st.error("Google API Key not found in Streamlit Secrets. Please add it.")
#     st.stop()

# # Configure the Generative AI model
# genai.configure(api_key=api_key)

# # Define company-specific data paths and names
# # (This is the NEW, CORRECTED code)
# COMPANY_CONFIG = {
#     "aetherfit": {
#         "name": "AetherFit (Fitness Equipment)",
#         "path": "data/aetherfit",
#         "image_path": "images"  # <--- CORRECTED PATH
#     },
#     "terratiles": {
#         "name": "TerraTiles (Luxury Tiles)",
#         "path": "data/terratiles",
    
#         "image_path": "data/terratiles/images"
#     },
# }
# # --- DATA EXTRACTION (Now dynamic based on company) ---

# def get_file_path(company_path, file_name):
#     return os.path.join(company_path, file_name)

# # Using st.cache_data to avoid reloading data on every interaction
# @st.cache_data(show_spinner="Loading knowledge base...")
# def build_context(company_key):
#     """Extracts data from all sources for the selected company and combines it."""
#     config = COMPANY_CONFIG[company_key]
#     company_path = config["path"]
    
#     context_parts = []
    
#     # 1. Extract from PDF
#     try:
#         pdf_path = get_file_path(company_path, "catalog.pdf")
#         with open(pdf_path, 'rb') as f:
#             reader = pypdf.PdfReader(f)
#             pdf_text = "".join(page.extract_text() for page in reader.pages)
#             context_parts.append(f"--- START PDF CATALOG ---\n{pdf_text}\n--- END PDF CATALOG ---")
#     except Exception as e:
#         st.warning(f"Could not load catalog.pdf: {e}")

#     # 2. Extract from CSV
#     try:
#         csv_path = get_file_path(company_path, "inventory.csv")
#         df = pd.read_csv(csv_path)
#         context_parts.append(f"--- START CSV INVENTORY/PRICING ---\n{df.to_string()}\n--- END CSV INVENTORY/PRICING ---")
#     except Exception as e:
#         st.warning(f"Could not load inventory.csv: {e}")

#     # 3. Extract from DOCX
#     try:
#         docx_path = get_file_path(company_path, "reviews.docx")
#         doc = docx.Document(docx_path)
#         docx_text = "\n".join([para.text for para in doc.paragraphs])
#         context_parts.append(f"--- START DOCX REVIEWS ---\n{docx_text}\n--- END DOCX REVIEWS ---")
#     except Exception as e:
#         st.warning(f"Could not load reviews.docx: {e}")
        
#     return "\n\n".join(context_parts)

# # --- LLM INTERACTION (With Image Handling Logic) ---

# def ask_assistant(question, context, company_key):
#     """Formats the prompt, sends it to the LLM, and includes image instructions."""
#     model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
#     # NEW INSTRUCTION FOR THE LLM!
#     prompt = f"""
#     You are an AI assistant for the company '{COMPANY_CONFIG[company_key]['name']}'.
    
#     **CRITICAL RULES:**
#     1. Answer the user's question based ONLY on the provided context. If the information is not in the context, you MUST say 'I do not have that information in my provided data.'
#     2. When a user asks about a specific product that has an image file listed in the CSV data, you MUST include a special tag in your response: [IMAGE: filename.jpg]. For example, if the user asks about 'PowerCycle C500' and its image is 'C500.jpg', part of your response must be '[IMAGE: C500.jpg]'.
#     3. Do not show the image tag for products that do not have an image file listed.
    
#     CONTEXT:
#     {context}

#     QUESTION:
#     {question}
    
#     ANSWER:
#     """
    
#     try:
#         response = model.generate_content(prompt)
#         return response.text
#     except Exception as e:
#         return f"An error occurred: {e}"

# # --- STREAMLIT UI ---

# st.set_page_config(layout="wide")
# st.title("🤖 AI Assistant for Companies")

# # Initialize session state for chat history
# if "messages" not in st.session_state:
#     st.session_state.messages = {}

# # Sidebar for company selection
# st.sidebar.title("Configuration")
# selected_company_key = st.sidebar.selectbox(
#     "Choose a company to chat with:",
#     options=list(COMPANY_CONFIG.keys()),
#     format_func=lambda key: COMPANY_CONFIG[key]["name"]
# )

# # Load context for the selected company
# knowledge_base = build_context(selected_company_key)

# # Initialize chat history for the selected company if it doesn't exist
# if selected_company_key not in st.session_state.messages:
#     st.session_state.messages[selected_company_key] = [
#         {"role": "assistant", "content": f"Hello! How can I help you with {COMPANY_CONFIG[selected_company_key]['name']} today?"}
#     ]

# # Display chat messages
# for message in st.session_state.messages[selected_company_key]:
#     with st.chat_message(message["role"]):
#         # This part handles displaying content that might have an image
#         if "image" in message:
#             st.image(message["image"])
#         st.markdown(message["content"])

# # Main chat input
# if prompt := st.chat_input(f"Ask about {COMPANY_CONFIG[selected_company_key]['name']}..."):
#     # Add user message to chat history
#     st.session_state.messages[selected_company_key].append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # Get assistant response
#     with st.chat_message("assistant"):
#         with st.spinner("Thinking..."):
#             full_response = ask_assistant(prompt, knowledge_base, selected_company_key)
            
#             # Use regex to find the image tag
#             image_match = re.search(r"\[IMAGE: (.*?)\]", full_response)
            
#             # Clean the response text by removing the tag
#             cleaned_response = re.sub(r"\[IMAGE: (.*?)\]", "", full_response).strip()
            
#             response_data = {"role": "assistant", "content": cleaned_response}
            
#             # If an image tag was found, find and display the image
#             if image_match:
#                 image_filename = image_match.group(1)
#                 # This path needs to be correct based on your folder structure
#                 image_path = os.path.join(COMPANY_CONFIG[selected_company_key]["image_path"], image_filename)
                
#                 if os.path.exists(image_path):
#                     st.image(image_path)
#                     # We can store the path in the message dict if needed, but displaying it directly is fine
#                 else:
#                     # If image file is listed but not found, inform the user.
#                     st.warning(f"Image '{image_filename}' not found at path '{image_path}'.")
            
#             st.markdown(cleaned_response)
#             st.session_state.messages[selected_company_key].append(response_data)


import streamlit as st
import pandas as pd
import pypdf
import docx
import google.generativeai as genai
import os
import re
import time

# --- CONFIGURATION and DATA FUNCTIONS (No changes needed here) ---

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("Google API Key not found. Please set it in your Streamlit secrets or local .env file.")
    st.stop()
genai.configure(api_key=api_key)

COMPANY_CONFIG = {
    "aetherfit": { "name": "AetherFit (Fitness Equipment)", "path": "data/aetherfit", "image_path": "images" },
    "terratiles": { "name": "TerraTiles (Luxury Tiles)", "path": "data/terratiles", "image_path": "data/terratiles/images" },
}

if 'llm_cache' not in st.session_state:
    st.session_state.llm_cache = {}

@st.cache_data(show_spinner="Loading knowledge base...")
def build_context(company_key):
    config = COMPANY_CONFIG[company_key]
    company_path = config["path"]
    context_parts = []
    # PDF
    try:
        pdf_path = os.path.join(company_path, "catalog.pdf")
        with open(pdf_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            pdf_text = "".join(page.extract_text() for page in reader.pages)
            context_parts.append(f"--- START PDF CATALOG ---\n{pdf_text}\n--- END PDF CATALOG ---")
    except Exception: pass
    # CSV
    try:
        csv_path = os.path.join(company_path, "inventory.csv")
        df = pd.read_csv(csv_path)
        context_parts.append(f"--- START CSV INVENTORY/PRICING ---\n{df.to_string()}\n--- END CSV INVENTORY/PRICING ---")
    except Exception: pass
    # DOCX
    try:
        docx_path = os.path.join(company_path, "reviews.docx")
        doc = docx.Document(docx_path)
        docx_text = "\n".join([para.text for para in doc.paragraphs])
        context_parts.append(f"--- START DOCX REVIEWS ---\n{docx_text}\n--- END DOCX REVIEWS ---")
    except Exception: pass
    return "\n\n".join(context_parts)

def ask_assistant(question, context, company_key):
    cache_key = f"{company_key}-{question.lower().strip()}"
    if cache_key in st.session_state.llm_cache:
        return st.session_state.llm_cache[cache_key]
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    prompt = f"""
    You are an AI assistant for the company '{COMPANY_CONFIG[company_key]['name']}'.
    CRITICAL RULES:
    1. Answer ONLY from the provided context. If not in context, say 'I do not have that information in my provided data.'
    2. If a product has an image file in the CSV, include the tag: [IMAGE: filename.jpg].
    3. After your answer, provide 3 relevant follow-up questions inside a tag like this: [SUGGESTIONS]Question 1?|Question 2?|Which is cheaper?[/SUGGESTIONS]. Do not provide suggestions if the information is not found.
    CONTEXT: {context}
    QUESTION: {question}
    ANSWER:
    """
    try:
        time.sleep(1) # Small delay to show spinner and prevent rapid-fire API calls
        response = model.generate_content(prompt)
        st.session_state.llm_cache[cache_key] = response.text
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

# --- STREAMLIT UI (UPDATED) ---
st.set_page_config(layout="wide")
st.title("🤖 AI Assistant for Multiple Companies")

if "messages" not in st.session_state:
    st.session_state.messages = {}

st.sidebar.title("Configuration")
selected_company_key = st.sidebar.selectbox(
    "Choose a company to chat with:",
    options=list(COMPANY_CONFIG.keys()),
    format_func=lambda key: COMPANY_CONFIG[key]["name"],
    key="company_selector"
)

knowledge_base = build_context(selected_company_key)

if selected_company_key not in st.session_state.messages:
    st.session_state.messages[selected_company_key] = [
        {"role": "assistant", "content": f"Hello! How can I help you with {COMPANY_CONFIG[selected_company_key]['name']} today?"}
    ]

# *** NEW: Initialize a variable to hold the clicked suggestion ***
clicked_suggestion = None

# Display chat history and suggestion buttons
for message_idx, message in enumerate(st.session_state.messages[selected_company_key]):
    with st.chat_message(message["role"]):
        if "image" in message and message["image"]:
            image_path = os.path.join(COMPANY_CONFIG[selected_company_key]["image_path"], message["image"])
            if os.path.exists(image_path):
                st.image(image_path)
            else:
                st.warning(f"Image '{message['image']}' not found.")
        
        st.markdown(message["content"])
        
        if "suggestions" in message:
            cols = st.columns(len(message["suggestions"]))
            for suggestion_idx, suggestion in enumerate(message["suggestions"]):
                with cols[suggestion_idx]:
                    # *** CHANGE: If a button is clicked, store its text ***
                    if st.button(suggestion, key=f"suggestion_{message_idx}_{suggestion_idx}"):
                        clicked_suggestion = suggestion

# Determine the prompt to process
# It's either from the chat input OR from a clicked suggestion button
chat_input_prompt = st.chat_input(f"Ask about {COMPANY_CONFIG[selected_company_key]['name']}...")
prompt = chat_input_prompt or clicked_suggestion

# Main logic for processing a prompt
if prompt:
    # Add the user's question to the chat history
    st.session_state.messages[selected_company_key].append({"role": "user", "content": prompt})

    # Get and parse the assistant's response
    with st.spinner("Thinking..."):
        full_response = ask_assistant(prompt, knowledge_base, selected_company_key)
        
        cleaned_response = full_response
        suggestions = []
        image_filename = None
        
        # Parse suggestions
        suggestion_match = re.search(r"\[SUGGESTIONS\](.*?)\[/SUGGESTIONS\]", cleaned_response, re.DOTALL)
        if suggestion_match:
            suggestion_text = suggestion_match.group(1)
            suggestions = [s.strip() for s in suggestion_text.split('|') if s.strip()]
            cleaned_response = re.sub(r"\[SUGGESTIONS\].*\[/SUGGESTIONS\]", "", cleaned_response).strip()

        # Parse image
        image_match = re.search(r"\[IMAGE: (.*?)\]", cleaned_response)
        if image_match:
            image_filename = image_match.group(1).strip()
            cleaned_response = re.sub(r"\[IMAGE: (.*?)\]", "", cleaned_response).strip()

        # Store the complete, parsed AI response in session state
        response_data = {"role": "assistant", "content": cleaned_response}
        if suggestions:
            response_data["suggestions"] = suggestions
        if image_filename:
            response_data["image"] = image_filename
            
        st.session_state.messages[selected_company_key].append(response_data)
        
        # Rerun the app to display the new messages immediately
        st.rerun()