from prompt_handler import process_prompt
from product_agent import handle_request
from utils import get_user_feedback

def main():
    print("🚀 TrendIA - Criatividade que cabe no seu bolso\n")
    while True:
        prompt = input("Digite seu pedido ou 'sair': ")
        if prompt.lower() == "sair":
            confirm = input("Tem certeza que deseja sair? (s/n): ")
            if confirm.lower() == 's':
                break
            else:
                continue

        data_structured = process_prompt(prompt)
        response = handle_request(data_structured)
        print("\n📦 Resultados encontrados:\n")
        for idx, product in enumerate(response, 1):
            print(f"{idx}. {product['nome']} - R${product['preco']} - Inovação: {product['inovacao']}/10")

        get_user_feedback(response)

if __name__ == "__main__":
    main()
