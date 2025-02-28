import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv


load_dotenv()  # Load environment variables from .env


OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

client = OpenAI(
  api_key= OPENAI_API_KEY
)

# App Title
st.title("Gerador de Respostas")

# Text input for customer email
customer_email = st.text_area("Coloca aqui o email:")

avoid = ["desculpe", "desculpa", "a culpa é nossa", "negativo"]

i_want_to = st.multiselect(
    "Tipo de resposta:", 
    ["Explicar causa do problema", "Oferecer desconto", "Explicar que portes gratis não são possíveis nesta encomenda", "Oferecer uma substituição gratuita"]   
)

manager_note = st.text_area("Adicione notas adicionais, caso queira")

# Generate AI response
def generate_email_response(email_text):
    prompt = f"""
    Act as a polite customer service agent for a clothing company. 
    Your task is to generate a polite, brand-consistent email reply

    Customer email:
    {email_text}
    
    The reply email should convey the following message:
    {i_want_to}
    
    Avoid the following list of expressions/words, without changing the intent of the message:
    {avoid}
    
    {f"Manager's special instruction: {manager_note}" if manager_note else ""}
    
    Everything must be in Portuguese from Portugal
    
    Be polite and consise
    """
    
    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": customer_email}
    ]
    )
    
    return response.choices[0].message.content

# Button to generate response
if st.button("Generate Response"):
    if customer_email:
        ai_response = generate_email_response(customer_email)
        st.subheader("Resposta sugerida:")
        st.text_area("AI-generated email:", ai_response, height=250)
    else:
        st.warning("Por favor escreve um email")
