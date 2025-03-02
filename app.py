import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import hmac
import yaml


load_dotenv()  # Load environment variables from .env

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def load_users():
    """Load users from users.yml file"""
    try:
        with open('users.yml', 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        # Default admin user if no file exists
        return {
            'users': {
                'admin': {
                    'password': 'admin123',  # Change this in production
                    'name': 'Administrator'
                }
            }
        }

def check_password(username, password):
    """Verify username and password"""
    users = load_users()
    if username in users['users']:
        if hmac.compare_digest(users['users'][username]['password'], password):
            return True
    return False

def login_page():
    """Display the login page"""
    st.title("🔐 Login")
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Acesso ao Sistema")
        username = st.text_input("👤 Nome de Utilizador")
        password = st.text_input("🔑 Palavra-passe", type="password")
        
        if st.button("Entrar", type="primary"):
            if check_password(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Nome de utilizador ou palavra-passe incorretos")

def main_app():
    """Main application code"""
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

    client = OpenAI(
        api_key=OPENAI_API_KEY
    )

    # Add logout button in sidebar
    with st.sidebar:
        st.write(f"👤 Utilizador: {st.session_state.username}")
        if st.button("📤 Terminar Sessão"):
            st.session_state.authenticated = False
            st.rerun()

    # App Title
    st.title("Gerador de Respostas")

    # Create categories of responses
    response_categories = {
        "Resolução de Problemas": [
            "Explicar causa do problema",
            "Oferecer substituição gratuita",
            "Informar sobre reembolso",
            "Pedir desculpas por atraso na entrega",
            "Explicar política de devoluções"
        ],
        "Informações sobre Produtos": [
            "Fornecer informações sobre tamanhos",
            "Explicar materiais e cuidados",
            "Informar sobre disponibilidade",
            "Explicar processo de personalização",
            "Fornecer guia de medidas"
        ],
        "Envios e Portes": [
            "Explicar que portes gratis não são possíveis",
            "Informar prazo de entrega estimado",
            "Fornecer informação de tracking",
            "Explicar custos de envio internacional"
        ],
        "Ofertas e Descontos": [
            "Oferecer desconto compensatório",
            "Informar sobre promoções atuais",
            "Oferecer voucher de desconto futuro",
            "Explicar programa de fidelidade"
        ]
    }

    avoid = [
        "Desculpe", 
        "Desculpa", 
        "culpa", 
        "nossa culpa",
        "erro nosso",
        "falha nossa",
        "não podemos",
        "impossível",
        "não é possível",
        "complicado"
    ]

    # Create tabs for better organization
    tab1, tab2 = st.tabs(["Composição do Email", "Configurações Avançadas"])

    with tab1:
        # Text input for customer email
        customer_email = st.text_area("📧 Email do Cliente:", height=150)
        
        # Multiselect for response types, organized by category
        selected_responses = []
        for category, options in response_categories.items():
            st.subheader(f"🔹 {category}")
            category_selections = st.multiselect(
                "Selecione as opções aplicáveis:",
                options,
                key=category
            )
            selected_responses.extend(category_selections)
        
        # Manager notes with improved UI
        manager_note = st.text_area("📝 Notas Adicionais (opcional):", height=100)

    with tab2:
        # Tone selection
        tone = st.select_slider(
            "Tom da Resposta:",
            options=["Muito Formal", "Formal", "Neutro", "Amigável", "Casual"],
            value="Neutro"
        )
        
        # Response length
        max_length = st.slider(
            "Comprimento da Resposta:",
            min_value=50,
            max_value=500,
            value=200,
            step=50,
            help="Número aproximado de palavras na resposta"
        )
        
        # Additional customization
        include_signature = st.checkbox("Incluir Assinatura da Empresa", value=True)
        include_contact = st.checkbox("Incluir Informações de Contacto", value=True)

    # Update the generate_email_response function
    def generate_email_response(email_text):
        prompt = f"""
        Act as a polite customer service agent for a clothing brand. 
        Your task is to generate a polite, brand-consistent email reply in Portuguese from Portugal.

        Guidelines:
        - Tone: {tone}
        - Maximum length: {max_length} words
        - Include signature: {include_signature}
        - Include contact info: {include_contact}

        Customer email:
        {email_text}
        
        The reply email should address the following points:
        {", ".join(selected_responses)}
        
        Avoid these expressions/words:
        {", ".join(avoid)}
        
        {f"Additional instructions: {manager_note}" if manager_note else ""}
        
        Key requirements:
        1. Use Portuguese from Portugal
        2. Be polite and concise
        3. Maintain a professional tone
        4. Focus on solutions
        """
        
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",  # Updated to a more capable model
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": customer_email}
            ],
            temperature=0.7,  # Add some creativity while maintaining professionalism
            max_tokens=1000
        )
        
        return response.choices[0].message.content

    # Improved response display
    if st.button("📤 Gerar Resposta", type="primary"):
        if customer_email:
            with st.spinner("A gerar resposta..."):
                ai_response = generate_email_response(customer_email)
                st.success("Resposta gerada com sucesso!")
                st.subheader("✉️ Resposta Sugerida:")
                st.text_area("", ai_response, height=300)
                
                # Add copy button
                st.button("📋 Copiar para Área de Transferência", 
                         on_click=lambda: st.write(ai_response))
        else:
            st.warning("⚠️ Por favor insira o email do cliente")

    # Add helpful footer
    st.markdown("---")
    st.markdown("💡 **Dica:** Para melhores resultados, certifique-se de selecionar todas as opções relevantes para o contexto do email.")

# Check if the user is authenticated, if not, show the login page
if not st.session_state.authenticated:
    login_page()
else:
    main_app()
