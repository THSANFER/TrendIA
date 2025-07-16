# app.py
import streamlit as st
import agent_core
import db_manager
import learning_engine
import os

# --- SETUP INICIAL ---
st.set_page_config(page_title="TrendIA", page_icon="🚀", layout="wide")

# Garante que o banco de dados e suas tabelas existam
db_manager.setup_database()

# <<< MUDANÇA PRINCIPAL: Usamos um nome de usuário fixo para todos os favoritos >>>
SHARED_USERNAME = "default_user"

# --- Inicialização do Estado da Sessão ---
# Carrega os favoritos do usuário padrão do DB para a sessão ao iniciar o app
if 'user_favorites' not in st.session_state:
    st.session_state.user_favorites = db_manager.get_user_favorites(SHARED_USERNAME)
if 'generated_products' not in st.session_state:
    st.session_state.generated_products = []


# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("🚀 TrendIA")
st.sidebar.caption("Controles do Agente de IA")

# O sistema de aprendizado agora está associado ao perfil, não a um usuário logado
user_profile_option = st.sidebar.selectbox(
    "Selecione seu perfil de busca:",
    ("Equilibrado", "Foco em Inovação", "Foco em Custo-Benefício")
)

learned_weights = learning_engine.get_user_weights(user_profile_option)
st.sidebar.subheader("Ajuste Fino da Busca Atual:")
weight_innovation = st.sidebar.slider("Prioridade para Inovação (w1)", 0.0, 1.0, learned_weights['w1'], 0.05)
weight_price = st.sidebar.slider("Prioridade para Custo-Benefício (w2)", 0.0, 1.0, learned_weights['w2'], 0.05)
current_weights = {"w1": weight_innovation, "w2": weight_price}
st.sidebar.divider()
st.sidebar.subheader("Aprendizado Contínuo")
if st.sidebar.button("Atualizar Perfil com Feedbacks"):
    with st.spinner("Analisando feedbacks..."):
        learning_engine.update_weights_from_feedback()
    st.sidebar.success("Seu perfil de busca foi atualizado!")
    st.rerun()


# --- ÁREA PRINCIPAL COM ABAS ---
st.title("Gerador de Ideias de Produtos com IA")
st.caption("Suas ideias favoritas agora ficam salvas permanentemente!")

tab1, tab2 = st.tabs(["💡 Gerar e Classificar", f"⭐ Favoritos Salvos ({len(st.session_state.user_favorites)})"])

# --- ABA 1: GERAR E CLASSIFICAR ---
with tab1:
    user_prompt = st.text_input("Descreva um conceito para gerar ideias:", placeholder="Ex: 'brindes para eventos de tecnologia'")
    if st.button("Gerar Novas Ideias", type="primary"):
        if user_prompt:
            model = agent_core.configure_llm()
            if model:
                with st.spinner("Aguarde, a IA está trabalhando..."):
                    # Supondo que você tenha a função 'generate_and_rank_products' em agent_core
                    ranked_products = agent_core.generate_and_rank_products(user_prompt, current_weights)
                    st.session_state.generated_products = ranked_products
            else:
                st.warning("Por favor, digite algo para gerar ideias.")

    if st.session_state.generated_products:
        st.subheader("Resultados Gerados e Classificados:")
        cols = st.columns(4)
        for i, product in enumerate(st.session_state.generated_products):
            col = cols[i % 4]
            with col.container(border=True, height=600):
                st.image(product.get('image_url', ''), use_container_width=True)
                st.subheader(product.get('title', ''))
                st.caption(product.get('description', ''))
                st.metric(label="Preço Estimado", value=f"R$ {product.get('price_brl', 0):.2f}")
                st.markdown('<div style="margin-top: auto;"></div>', unsafe_allow_html=True)
                
                feedback_cols = st.columns(2)
                if feedback_cols[0].button("👍", key=f"like_{product['title']}_{i}"):
                    # O log de feedback ainda pode usar o perfil selecionado
                    db_manager.log_feedback(product.get('product_url'), user_profile_option, 'like')
                    st.toast("Feedback positivo registrado!", icon="😊")

                if feedback_cols[1].button("⭐", key=f"fav_{product['title']}_{i}"):
                    # Usa o SHARED_USERNAME para salvar no DB
                    product_id = db_manager.save_product_if_not_exists(product)
                    db_manager.add_favorite(SHARED_USERNAME, product_id)
                    # Atualiza a lista de favoritos na sessão para refletir a mudança
                    st.session_state.user_favorites = db_manager.get_user_favorites(SHARED_USERNAME)
                    st.toast("Salvo nos Favoritos!", icon="⭐")
                    st.rerun()
                
                st.link_button("Buscar no Google", product.get('product_url', '#'), use_container_width=True)
    else:
        st.info("Digite um tema acima e clique no botão para começar.")


# --- ABA 2: MEUS FAVORITOS ---
with tab2:
    st.header("Seus Produtos Salvos")
    if st.session_state.user_favorites:
        cols_fav = st.columns(4)
        for i, product in enumerate(st.session_state.user_favorites):
            col = cols_fav[i % 4]
            with col.container(border=True, height=550):
                st.image(product.get('image_url', ''), use_container_width=True)
                st.subheader(product.get('title', ''))
                st.caption(product.get('description', ''))
                st.metric(label="Preço Estimado", value=f"R$ {product.get('price_brl', 0):.2f}")
                st.markdown('<div style="margin-top: auto;"></div>', unsafe_allow_html=True)

                if st.button("🗑️ Remover", key=f"rem_{product['title']}_{i}", use_container_width=True):
                    # Usa o SHARED_USERNAME para remover do DB
                    product_id = db_manager.save_product_if_not_exists(product)
                    db_manager.remove_favorite(SHARED_USERNAME, product_id)
                    # Atualiza a lista de favoritos na sessão
                    st.session_state.user_favorites = db_manager.get_user_favorites(SHARED_USERNAME)
                    st.rerun()
                
                st.link_button("Buscar no Google", product.get('product_url', '#'), use_container_width=True)
    else:
        st.info("Você ainda não salvou nenhum produto.")
