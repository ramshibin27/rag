import pandas as pd
import pypdf
import docx
import google.generativeai as genai
import os
from dotenv import load_dotenv

# --- 1. EXTRACTION & TRANSFORMATION (Happens once at the start) ---

def extract_from_pdf(file_path):
    """Extracts text from a PDF file."""
    try:
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    except FileNotFoundError:
        return f"ERROR: The file '{file_path}' was not found."
    except Exception as e:
        return f"Error reading PDF: {e}"

def extract_from_csv(file_path):
    """Extracts data from a CSV file and formats it as a string."""
    try:
        df = pd.read_csv(file_path)
        return df.to_string()
    except FileNotFoundError:
        return f"ERROR: The file '{file_path}' was not found."
    except Exception as e:
        return f"Error reading CSV: {e}"

def extract_from_docx(file_path):
    """Extracts text from a DOCX file."""
    try:
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except FileNotFoundError:
        return f"ERROR: The file '{file_path}' was not found."
    except Exception as e:
        return f"Error reading DOCX: {e}"

def build_context():
    """Extracts data from all sources and combines it into a single context."""
    print("Loading data from PDF, CSV, and DOCX files...")
    
    # Define file paths
    pdf_path = 'AetherFit_Product_Catalog_2024.pdf'
    csv_path = 'AetherFit_Inventory_Pricing.csv'
    docx_path = 'AetherFit_User_Reviews.docx'

    # Extract data
    pdf_data = extract_from_pdf(pdf_path)
    csv_data = extract_from_csv(csv_path)
    docx_data = extract_from_docx(docx_path)
    
    # Combine into a single context string
    full_context = f"""
    --- START PRODUCT CATALOG DATA (from PDF) ---
    {pdf_data}
    --- END PRODUCT CATALOG DATA ---

    --- START INVENTORY & PRICING DATA (from CSV) ---
    {csv_data}
    --- END INVENTORY & PRICING DATA ---

    --- START USER REVIEW DATA (from DOCX) ---
    {docx_data}
    --- END USER REVIEW DATA ---
    """
    print("Data loaded successfully!")
    return full_context

# --- 2. INGESTION & QUERYING SETUP ---

def ask_aetherfit_assistant(question, context, model):
    """Formats the prompt and sends a question to the LLM."""
    prompt = f"""
    You are an expert AI assistant for the 'AetherFit' fitness equipment company.
    Your task is to answer customer questions.
    
    **CRITICAL RULE: Answer the user's question based ONLY on the provided context below. If the information is not in the context, you MUST say 'I do not have that information in my provided data.' Do not make up answers.**

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
        return f"An error occurred while contacting the AI model: {e}"

# --- 3. MAIN INTERACTIVE LOOP ---

if __name__ == "__main__":
    # Setup API Key
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("FATAL ERROR: GOOGLE_API_KEY not found. Please set it in your .env file.")
        exit()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    # Build the context from files once
    knowledge_base = build_context()

    print("\n--- Welcome to the AetherFit Interactive Assistant ---")
    print("Ask a question about our products. Type 'quit' or 'exit' to end the session.")

    while True:
        # Get user input
        user_question = input("\nYour Question: ")

        # Check if the user wants to quit
        if user_question.lower().strip() in ['quit', 'exit']:
            print("Thank you for using the AetherFit assistant. Goodbye!")
            break
        
        # Get the answer from the LLM
        print("...Thinking...")
        answer = ask_aetherfit_assistant(user_question, knowledge_base, model)
        
        # Print the answer
        print(f"\nAnswer: {answer}")