import os
import subprocess
import sys
import re
import json

LOCATORS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "playwright_layer", "locators", "login_locators.py"
)
BDD_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "bdd"
)
FIX_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "output", "ai", "ai_fix.json"
)


def _ler_locators_atual() -> dict:
    with open(LOCATORS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def aplicar_todos(novos_locators: dict) -> bool:
    if not novos_locators:
        print("  Nenhum locator para aplicar.")
        return False

    conteudo = _ler_locators_atual()
    alteracoes = 0

    for antigo, novo in novos_locators.items():
        if antigo == novo:
            continue
        if antigo not in conteudo:
            print(f"  Locator '{antigo}' nao encontrado no arquivo (talvez ja foi corrigido).")
            continue

        conteudo = conteudo.replace(antigo, novo)
        print(f"  Locator corrigido: {antigo} -> {novo}")
        alteracoes += 1

    if alteracoes == 0:
        print("  Nenhuma alteracao necessaria.")
        return True

    with open(LOCATORS_PATH, "w", encoding="utf-8") as f:
        f.write(conteudo)

    print(f"  Total: {alteracoes} locator(es) corrigido(s)")
    return True


def aplicar_por_nome(novos_locators: dict) -> bool:
    if not novos_locators:
        return False

    conteudo = _ler_locators_atual()
    alteracoes = 0

    for nome, novo in novos_locators.items():
        padrao = re.compile(rf'(^\s*{re.escape(nome)}\s*=\s*)"([^"]*)"', re.MULTILINE)
        match = padrao.search(conteudo)

        if not match:
            print(f"  Constante '{nome}' nao encontrada no arquivo.")
            continue

        antigo = match.group(2)
        if antigo == novo:
            continue

        novo_literal = json.dumps(novo, ensure_ascii=False)
        conteudo = padrao.sub(lambda m: f"{m.group(1)}{novo_literal}", conteudo, count=1)
        print(f"  Locator corrigido: {nome}: {antigo} -> {novo}")
        alteracoes += 1

    if alteracoes == 0:
        print("  Nenhuma alteracao necessaria.")
        return True

    with open(LOCATORS_PATH, "w", encoding="utf-8") as f:
        f.write(conteudo)

    print(f"  Total: {alteracoes} locator(es) corrigido(s)")
    return True


def ler_fix_json() -> dict:
    if not os.path.exists(FIX_JSON):
        return {}
    with open(FIX_JSON, encoding="utf-8") as f:
        return json.load(f)


def validar(is_headed: bool = False) -> bool:
    print(f"\n  Re-testando com pytest...")
    print(f"  {'-' * 40}")

    cmd = [sys.executable, "-m", "pytest", BDD_PATH, "-v"]
    if is_headed:
        cmd.append("--headed")

    try:
        resultado = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            timeout=120  # 2 minutos de timeout
        )
    except subprocess.TimeoutExpired:
        print(f"\n  Timeout no teste. Use Ctrl+C e rode 'python cleanup.py' se travar.")
        return False

    print()
    if resultado.returncode == 0:
        print(f"  Teste validado com sucesso!")
        return True
    return False


def aplicar_e_validar(resultado: dict, is_headed: bool = False):
    locators_por_nome = resultado.get("locator_names", {})
    locators = resultado.get("locators", {})
    if not locators_por_nome and not locators:
        print("  Nenhum locator retornado pela analise.")
        return False

    aplicou = aplicar_por_nome(locators_por_nome) if locators_por_nome else aplicar_todos(locators)
    if aplicou:
        return validar(is_headed)

    return False
