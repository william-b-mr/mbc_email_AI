import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import bcrypt
import json
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional


load_dotenv()  # Load environment variables from .env

# Security configurations
SECRET_KEY = st.secrets["JWT_SECRET_KEY"]  # Add this to your streamlit secrets
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
LOGIN_REQUIRED = st.secrets["LOGIN_REQUIRED"]

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    

class UserDB:
    """Secure user database management"""
    def __init__(self):
        self.users_file = "secure_users.json"
        self._load_users()
    
    def _load_users(self):
        """Load users from secure storage"""
        try:
            if not os.path.exists(self.users_file):
                # Create default admin if file doesn't exist
                admin_password = st.secrets["ADMIN_PASSWORD"]  # Get from Streamlit secrets
                hashed_password = self._hash_password(admin_password)
                self.users = {
                    "admin": {
                        "hashed_password": hashed_password,
                        "name": "Administrator",
                        "role": "admin"
                    }
                }
                self._save_users()
            else:
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
        except Exception as e:
            st.error(f"Error loading users: {str(e)}")
            self.users = {}
    
    def _save_users(self):
        """Save users to secure storage"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f)
        except Exception as e:
            st.error(f"Error saving users: {str(e)}")
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(
                plain_password.encode(), 
                hashed_password.encode()
            )
        except Exception:
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Authenticate a user and return user data if successful"""
        if username not in self.users:
            return None
        user = self.users[username]
        if not self.verify_password(password, user["hashed_password"]):
            return None
        return user
    
    def create_user(self, username: str, password: str, name: str, role: str = "user"):
        """Create a new user"""
        if username in self.users:
            raise ValueError("Username already exists")
        
        hashed_password = self._hash_password(password)
        self.users[username] = {
            "hashed_password": hashed_password,
            "name": name,
            "role": role
        }
        self._save_users()

def create_access_token(data: dict):
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# Initialize UserDB
user_db = UserDB()

def check_password(username: str, password: str) -> bool:
    """Verify username and password"""
    user = user_db.authenticate_user(username, password)
    if user:
        # Create and store access token
        access_token = create_access_token({"sub": username, "role": user["role"]})
        st.session_state.access_token = access_token
        st.session_state.user_role = user["role"]
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

def verify_session():
    """Verify if the current session is valid"""
    if 'access_token' not in st.session_state:
        return False
    
    token_data = verify_token(st.session_state.access_token)
    if not token_data:
        return False
    
    return True

def main_app():
    """Main application code"""
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

    client = OpenAI(
        api_key=OPENAI_API_KEY
    )

    if LOGIN_REQUIRED == "YES":
        # Add logout button and user management in sidebar
        with st.sidebar:
            st.write(f"👤 Utilizador: {st.session_state.username}")
            
            # Add user management section for admins
            if st.session_state.user_role == "admin":
                st.markdown("---")
                st.markdown("### ⚙️ Gestão de Utilizadores")
                
                # Create new user form
                with st.expander("➕ Criar Novo Utilizador"):
                    new_username = st.text_input("Nome de Utilizador", key="new_username")
                    new_password = st.text_input("Palavra-passe", type="password", key="new_password")
                    new_name = st.text_input("Nome Completo", key="new_name")
                    new_role = st.selectbox("Função", ["user", "admin"], key="new_role")
                    
                    if st.button("Criar Utilizador"):
                        try:
                            user_db.create_user(
                                username=new_username,
                                password=new_password,
                                name=new_name,
                                role=new_role
                            )
                            st.success(f"Utilizador '{new_username}' criado com sucesso!")
                        except ValueError as e:
                            st.error(str(e))
                        except Exception as e:
                            st.error(f"Erro ao criar utilizador: {str(e)}")
                
                # List existing users
                with st.expander("👥 Listar Utilizadores"):
                    st.markdown("#### Utilizadores Existentes:")
                    for username, user_data in user_db.users.items():
                        st.markdown(f"""
                        **{username}**
                        - Nome: {user_data['name']}
                        - Função: {user_data['role']}
                        ---
                        """)
            
            # Logout button
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
if LOGIN_REQUIRED == "YES":
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()

else:
    main_app()
