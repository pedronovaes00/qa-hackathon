import os
import json
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "ai")


def salvar_json(resultado: dict, url: str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    dados = {
        "teste": "Login com sucesso",
        "feature": "bdd/features/login.feature",
        "data_analise": datetime.now().isoformat(),
        "locators": resultado.get("locators", {}),
        "locator_names": resultado.get("locator_names", {}),
        "origem": resultado.get("origem", ""),
        "erro": resultado.get("erro", ""),
        "url": url,
    }

    caminho = os.path.join(OUTPUT_DIR, "ai_fix.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

    return caminho
