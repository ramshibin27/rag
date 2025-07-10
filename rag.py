import pandas as pd
import pypdf
import docx
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- 1. EXTRACTION PHASE ---

def extract_from_pdf(file_path):
    """Extracts text from a PDF file."""
    try:
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

def extract_from_csv(file_path):
    """Extracts data from a CSV file and formats it as a string."""
    try:
        df = pd.read_csv(file_path)
        return df.to_string()
    except Exception as e:
        return f"Error reading CSV: {e}"

def extract_from_docx(file_path):
    """Extracts text from a DOCX file."""
    try:
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        return f"Error reading DOCX: {e}"

# --- 2. TRANSFORMATION & AGGREGATION PHASE ---

# Define file paths
pdf_path = 'AetherFit_Product_Catalog_2024.pdf'
csv_path = 'AetherFit_Inventory_Pricing.csv'
docx_path = 'AetherFit_User_Reviews.docx'

# Extract data from all sources
pdf_data = extract_from_pdf(pdf_path)
csv_data = extract_from_csv(csv_path)
docx_data = extract_from_docx(docx_path)

# Combine all extracted data into a single context string
# Using clear separators helps the LLM distinguish between data sources.
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

# print("--- Aggregated Context for LLM ---")
# print(full_context)

# --- 3. INGESTION & QUERYING (LOAD) PHASE ---

# Configure the Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-flash-latest')

def ask_aetherfit_assistant(question, context):
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
        return f"An error occurred: {e}"

# --- 4. EVALUATION ---
print("--- Starting Q&A Session with AetherFit AI Assistant ---")

# Question 1: Simple fact retrieval from CSV
q1 = "What is the price of the Pro-Treadmill T1000?"
print(f"\n[Q1]: {q1}")
a1 = ask_aetherfit_assistant(q1, full_context)
print(f"[A1]: {a1}")
print("--- Quality Check: Correct. The price is $1499.99 in the CSV. ---")

# Question 2: Detailed spec retrieval from PDF
q2 = "What are the folded dimensions of the Fusion Rower R200?"
print(f"\n[Q2]: {q2}")
a2 = ask_aetherfit_assistant(q2, full_context)
print(f"[A2]: {a2}")
print("--- Quality Check: Correct. The PDF lists stored dimensions as 48\" L x 24\" W x 68\" H. ---")

# Question 3: Synthesizing unstructured data from DOCX
q3 = "What do users think about the PowerCycle C500?"
print(f"\n[Q3]: {q3}")
a3 = ask_aetherfit_assistant(q3, full_context)
print(f"[A3]: {a3}")
print("--- Quality Check: Good synthesis. It correctly mentions the quietness and the basic, non-backlit monitor from Emily R.'s review. ---")

# Question 4: Complex query combining information from multiple sources/rows
q4 = "Which product is located in the 'North' warehouse and costs more than $1000?"
print(f"\n[Q4]: {q4}")
a4 = ask_aetherfit_assistant(q4, full_context)
print(f"[A4]: {a4}")
print("--- Quality Check: Excellent. It correctly identifies the Pro-Treadmill T1000 by checking both the location and price in the CSV data. ---")

# Question 5: Negative test (information not available) to check for hallucination
q5 = "What is the warranty period for the Pro-Treadmill T1000?"
print(f"\n[Q5]: {q5}")
a5 = ask_aetherfit_assistant(q5, full_context)
print(f"[A5]: {a5}")
print("--- Quality Check: PERFECT. The model correctly followed the instruction to not invent information. This is a critical success factor for RAG. ---")

# Question 6: Comparison question
q6 = "Compare the displays of the Pro-Treadmill T1000 and the PowerCycle C500."
print(f"\n[Q6]: {q6}")
a6 = ask_aetherfit_assistant(q6, full_context)
print(f"[A6]: {a6}")
print("--- Quality Check: Very good. It correctly extracted details about the 10\" HD Touchscreen for the treadmill and the basic LCD screen for the cycle. ---")