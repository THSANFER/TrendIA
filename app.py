# app.py
import streamlit as st
import database
import agent_core
import learning_engine # <-- Importa nosso novo módulo de aprendizado

# --- Configuração da Página ---
st.set_page_config(
    page_title="TrendIA",
    page_icon="🧠",
    layout="wide"
)

# --- Carregamento dos Dados ---
@st.cache_data(ttl=600)
def get_products():
    print("Carregando produtos do banco de dados...")
    products_dict = database.load_products()
    return list(products_dict.values())

all_products = get_products()

# --- Interface do Usuário ---

st.title("🧠 TrendIA")
st.caption("Criatividade que cabe no seu bolso e aprende com você!")

# --- Barra Lateral (Sidebar) com Controles e Informações de Aprendizado ---
st.sidebar.title("Configurações do Agente")

user_profile = st.sidebar.selectbox(
    "Selecione seu perfil:",
    ("Empresário de Brindes", "Loja de Presentes para Festas", "Consumidor Final"),
    key="user_profile_selector"
)
st.sidebar.info(f"Você está navegando como: **{user_profile}**")
st.sidebar.divider()

# --- Lógica de Aprendizado (Módulo 4) ---
# Carrega os pesos personalizados para o perfil selecionado
weights = learning_engine.get_user_weights(user_profile)

# Mostra os pesos atuais para o usuário de forma transparente
st.sidebar.subheader("Preferências Aprendidas:")
st.sidebar.progress(weights['w1'], text=f"Prioridade para Inovação: {weights['w1']:.2f}")
st.sidebar.progress(weights['w2'], text=f"Prioridade para Custo-Benefício: {weights['w2']:.2f}")

# Botão para acionar o aprendizado manualmente (para fins de demonstração)
if st.sidebar.button("Atualizar Aprendizado"):
    with st.spinner("Analisando feedbacks e atualizando preferências..."):
        learning_engine.update_weights_from_feedback()
    st.sidebar.success("Preferências atualizadas!")
    # Força o recarregamento dos pesos na interface
    st.rerun()

# --- Barra de Busca (Prompt do Usuário) ---
user_prompt = st.text_input(
    "O que você procura? Descreva o produto ou evento que você tem em mente:",
    placeholder="Ex: 'a smart custom book' ou 'digital gifts'"
)

# --- Lógica de Busca e Exibição ---
if not all_products:
    st.error("O banco de dados de produtos está vazio. Execute o 'scraper_worker.py'.")
else:
    if user_prompt:
        # Usa o 'agent_core' com os pesos personalizados carregados pelo 'learning_engine'
        ranked_products = agent_core.find_and_rank_products(user_prompt, all_products, weights)
        
        st.subheader(f"Resultados personalizados para '{user_prompt}'")
        
        if ranked_products:
            cols = st.columns(4)
            for i, product in enumerate(ranked_products):
                col = cols[i % 4]
                with col:
                    with st.container(border=True):
                        st.image(product.get('image_url', ''), use_column_width=True)
                        st.caption(product.get('title', ''))
                        
                        score_cols = st.columns(2)
                        score_cols[0].metric(label="Preço", value=f"£{product.get('price_gbp', 0):.2f}")
                        score_cols[1].metric(
                            label="Relevância", 
                            value=f"{product.get('utility_score', 0):.2f}",
                            help=f"Score de Inovação: {product.get('innovation_score',0)}"
                        )

                        st.link_button("Ver na Loja", product.get('product_url', '#'))
                        
                        feedback_cols = st.columns(2)
                        if feedback_cols[0].button("👍", key=f"like_{product.get('product_url')}"):
                            # A ação de feedback agora também pode acionar o aprendizado
                            database.log_feedback(product.get('product_url'), user_profile, 'like')
                            st.toast("Obrigado! Suas preferências estão sendo ajustadas.", icon="🧠")
                        if feedback_cols[1].button("👎", key=f"dislike_{product.get('product_url')}"):
                            database.log_feedback(product.get('product_url'), user_profile, 'dislike')
                            st.toast("Entendido! Suas preferências estão sendo ajustadas.", icon="🤖")
        else:
            st.warning("Nenhum produto corresponde à sua busca. Tente outros termos.")
    else:
        st.info("Digite algo na barra de busca para encontrar produtos.")