# app.py
import streamlit as st
import agent_core
import db_manager
import learning_engine
import os
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import pandas as pd
import time

# --- SETUP INICIAL ---
st.set_page_config(page_title="TrendIA", page_icon="🚀", layout="wide")

# Garante que o banco de dados e suas tabelas existam na primeira execução
db_manager.setup_database()

# Define um usuário padrão, já que removemos o sistema de login
SHARED_USERNAME = "default_user"

# --- Inicialização do Estado da Sessão ---
# Carrega os favoritos do usuário padrão do DB para a sessão ao iniciar o app
if 'user_favorites' not in st.session_state:
    st.session_state.user_favorites = db_manager.get_user_favorites(SHARED_USERNAME)
# Inicializa a lista de produtos gerados
if 'generated_products' not in st.session_state:
    st.session_state.generated_products = []


# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("🚀 TrendIA")
st.sidebar.caption("Controles do Agente de IA")

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

# Cria as três abas da interface
tab1, tab2, tab3 = st.tabs([
    "💡 Gerar e Classificar", 
    f"⭐ Favoritos ({len(st.session_state.user_favorites)})", 
    "📊 Histórico e Tendências"
])

# --- ABA 1: GERAR E CLASSIFICAR ---
with tab1:
    user_prompt = st.text_input("Descreva um conceito para gerar ideias:", placeholder="Ex: 'brindes para eventos de tecnologia'")
    if st.button("Gerar Novas Ideias", type="primary"):
        if user_prompt:
            with st.status("Iniciando a busca criativa...", expanded=True) as status:
                status.write("Passo 1: Enviando seu prompt para a IA (Gemini)...")
                ranked_products = agent_core.generate_and_rank_products(user_prompt, current_weights)
                st.session_state.generated_products = ranked_products
                
                if ranked_products:
                    time.sleep(1)
                    status.write("Passo 2: Analisando e organizando os resultados...")
                    db_manager.save_search_prompt(user_prompt)
                    time.sleep(1)
                    status.update(label="Busca concluída com sucesso!", state="complete", expanded=False)
                else:
                    status.update(label="Falha na geração!", state="error", expanded=True)
                    st.error("A IA não conseguiu gerar produtos. Verifique o terminal para erros ou tente um prompt diferente.")
        else:
            st.warning("Por favor, digite algo para gerar ideias.")

    if st.session_state.generated_products:
        st.subheader("Resultados Gerados e Classificados:")
        cols = st.columns(4)
        for i, product in enumerate(st.session_state.generated_products):
            col = cols[i % 4]
            with col.container(border=True, height=650):
                st.image(product.get('image_url', ''), use_container_width=True)
                st.subheader(product.get('title', ''))
                st.caption(product.get('description', ''))
                st.metric(label="Preço Estimado", value=f"R$ {product.get('price_brl', 0):.2f}")
                st.markdown("---")
                st.markdown(f"**Cliente Ideal:** *{product.get('marketing_persona', 'N/A')}*")
                st.markdown('<div style="margin-top: auto;"></div>', unsafe_allow_html=True)
                
                feedback_cols = st.columns(2)
                if feedback_cols[0].button("👍", key=f"like_{product['title']}_{i}"):
                    db_manager.log_feedback(product.get('product_url'), user_profile_option, 'like')
                    st.toast("Feedback positivo registrado!", icon="😊")

                if feedback_cols[1].button("⭐", key=f"fav_{product['title']}_{i}"):
                    product_id = db_manager.save_product_if_not_exists(product)
                    db_manager.add_favorite(SHARED_USERNAME, product_id)
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
            with col.container(border=True, height=600):
                st.image(product.get('image_url', ''), use_container_width=True)
                st.subheader(product.get('title', ''))
                st.caption(product.get('description', ''))
                st.metric(label="Preço Estimado", value=f"R$ {product.get('price_brl', 0):.2f}")
                st.markdown("---")
                st.markdown(f"**Cliente Ideal:** *{product.get('marketing_persona', 'N/A')}*")
                st.markdown('<div style="margin-top: auto;"></div>', unsafe_allow_html=True)

                if st.button("🗑️ Remover", key=f"rem_{product['title']}_{i}", use_container_width=True):
                    product_id = db_manager.save_product_if_not_exists(product)
                    db_manager.remove_favorite(SHARED_USERNAME, product_id)
                    st.session_state.user_favorites = db_manager.get_user_favorites(SHARED_USERNAME)
                    st.rerun()
                
                st.link_button("Buscar no Google", product.get('product_url', '#'), use_container_width=True)
    else:
        st.info("Você ainda não salvou nenhum produto.")

# --- ABA 3: HISTÓRICO E TENDÊNCIAS ---
with tab3:
    st.header("Análise de Buscas")

    with st.container(border=True):
        st.subheader("Histórico Recente")
        search_history = db_manager.get_search_history(limit=25)
        
        if search_history:
            for item in search_history:
                col_text, col_button = st.columns([0.9, 0.1])
                with col_text:
                    timestamp = pd.to_datetime(item['timestamp']).strftime('%d/%m/%Y %H:%M')
                    st.markdown(f"**`{item['prompt']}`** - *buscado em {timestamp}*")
                with col_button:
                    if st.button("🗑️", key=f"delete_history_{item['id']}", help="Excluir esta busca"):
                        db_manager.delete_search_item(item['id'])
                        st.toast("Busca removida do histórico!")
                        st.rerun()
            
            st.divider()
            
            if st.button("🧹 Limpar todo o histórico", use_container_width=True, type="secondary"):
                db_manager.clear_search_history()
                st.toast("Histórico de buscas limpo com sucesso!")
                st.rerun()
        else:
            st.write("Nenhuma busca no histórico ainda.")
    
    st.subheader("Nuvem de Tendências")
    all_prompts_text = db_manager.get_all_prompts_as_text()
    if all_prompts_text and all_prompts_text.strip():
        try:
            stopwords_base = set(STOPWORDS)
            palavras_proibidas = {
               'presente', 'presentes', 'para', 'ideia', 'ideias', 
                    'de', 'do', 'da', 'dos', 'das', 'com', 'um', 'uma',
                    'como', 'qual', 'ser', 'produtos', 'produto', 'que',
                    'seja', 'sejam', 'comprar', 'encontrar', 'dia', 'o', 
                    'a', 'anos', 'ano'
            }
            stopwords_completas = stopwords_base.union(palavras_proibidas)
            wordcloud = WordCloud(width=800, height=400, background_color='white', colormap='viridis', stopwords=stopwords_completas).generate(all_prompts_text)
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis("off")
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Não foi possível gerar a nuvem de palavras. Erro: {e}")
    else:
        st.write("Faça algumas buscas para gerar a sua nuvem de tendências.")
