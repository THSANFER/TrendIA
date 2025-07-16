# app.py
import streamlit as st
import agent_core
import database
import learning_engine

st.set_page_config(page_title="TrendIA Híbrido", page_icon="🚀", layout="wide")

if 'generated_products' not in st.session_state:
    st.session_state.generated_products = []

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("🚀 TrendIA")
st.sidebar.caption("Controles do Agente de IA")

user_profile = st.sidebar.selectbox(
    "Selecione a forma da pesquisa:",
    ("Muita Inovação", "Mais Inovação", "Meio a Meio", "Mais Custo Benefício", "Muito Custo Benefício")
)

# Carrega os pesos aprendidos ou padrão
learned_weights = learning_engine.get_user_weights(user_profile)

# Sliders para ajuste fino em tempo real, com o padrão vindo do aprendizado
st.sidebar.subheader("Ajuste a busca atual:")
weight_innovation = st.sidebar.slider(
    "Prioridade para Inovação (w1)", 0.0, 1.0, learned_weights['w1'], 0.05
)
weight_price = st.sidebar.slider(
    "Prioridade para Custo-Benefício (w2)", 0.0, 1.0, learned_weights['w2'], 0.05
)
current_weights = {"w1": weight_innovation, "w2": weight_price}

st.sidebar.divider()
st.sidebar.subheader("Aprendizado Contínuo")
if st.sidebar.button("Atualizar Perfil com Feedbacks"):
    with st.spinner("Analisando feedbacks..."):
        learning_engine.update_weights_from_feedback()
    st.sidebar.success("Perfil atualizado!")
    st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("Gerador de Ideias de Produtos com IA")
user_prompt = st.text_input(
    "Descreva um conceito, tema ou público para gerar ideias:",
    placeholder="Ex: 'presentes de natal para gamers' ou 'produtos de casa inteligentes e baratos'"
)

if st.button("Gerar Novas Ideias", type="primary"):
    if user_prompt:
        with st.spinner("Aguarde, o Gemini está criando e nosso Agente está classificando..."):
            ranked_products = agent_core.generate_and_rank_products(user_prompt, current_weights)
            st.session_state.generated_products = ranked_products
            
            # Salva os produtos gerados no histórico para o aprendizado futuro
            if ranked_products:
                database.save_products(ranked_products)
    else:
        st.warning("Por favor, digite algo para gerar ideias.")

# --- EXIBIÇÃO DOS RESULTADOS ---
if st.session_state.generated_products:
    st.subheader("Resultados Gerados e Classificados:")
    
    # Re-classifica os produtos se os sliders forem movidos
    ranked_products_display = sorted(
        st.session_state.generated_products,
        key=lambda p: (p.get('innovation_score', 0) * current_weights['w1']) + ((1 - p.get('price_brl', 0) / 200) * current_weights['w2']),
        reverse=True
    )

    cols = st.columns(4)
    for i, product in enumerate(ranked_products_display):
        col = cols[i % 4]
        with col:
            with st.container(border=True):
                st.image(product.get('image_url', ''), use_container_width =True)
                st.subheader(product.get('title', ''))
                st.caption(product.get('description', ''))
                st.metric(label="Preço Estimado", value=f"R$ {product.get('price_brl', 0):.2f}")
                
                # Feedback
                feedback_cols = st.columns(2)
                if feedback_cols[0].button("👍", key=f"like_{product.get('product_url')}"):
                    database.log_feedback(product.get('product_url'), user_profile, 'like')
                    st.toast("Feedback positivo registrado!", icon="😊")
                if feedback_cols[1].button("👎", key=f"dislike_{product.get('product_url')}"):
                    database.log_feedback(product.get('product_url'), user_profile, 'dislike')
                    st.toast("Feedback negativo registrado.", icon="🙁")
                
                st.link_button("Buscar no Google", product.get('product_url', '#'), use_container_width=True)
else:
    st.info("Digite um tema acima e clique no botão para começar.")
