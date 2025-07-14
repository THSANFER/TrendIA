def calcular_utilidade(inovacao, preco, total_opcoes):
    w1, w2, w3 = 0.5, 0.3, 0.2
    # Normalize valores
    inovacao_n = inovacao / 10
    preco_n = 1 - (preco / 1000)
    sobrecarga_n = min(total_opcoes / 10, 1)

    return (inovacao_n * w1) + (preco_n * w2) - (sobrecarga_n * w3)

def get_user_feedback(produtos):
    feedback = input("\nO resultado foi útil? (s/n): ")
    if feedback.lower() == "n":
        print("🔄 Buscando novas fontes ou reformulando a resposta...")
    else:
        print("🎯 Vamos sugerir preços e customizações baseadas nos resultados.")
