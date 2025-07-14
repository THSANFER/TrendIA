def process_prompt(prompt):
    prompt = prompt.lower()
    data = {
        "nicho": "produtos personalizados para eventos",
        "idade": None,
        "genero": None,
        "preco_maximo": None,
    }

    if "feminino" in prompt:
        data["genero"] = "feminino"
    if "masculino" in prompt:
        data["genero"] = "masculino"
    if "anos" in prompt:
        import re
        match = re.findall(r"(\d+)\s*anos", prompt)
        if match:
            data["idade"] = int(match[0])
    if "reais" in prompt:
        match = re.findall(r"(\d+)\s*reais", prompt)
        if match:
            data["preco_maximo"] = int(match[0])

    return data
