import os
import sys
import re
import subprocess
import time
import signal
from urllib.request import urlopen

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

import pytest

# Flag global para controlar timeout do teardown
_BROWSER_INSTANCES = []

LOCATORS_PATH = os.path.join(
    project_root,
    "playwright_layer", "locators", "login_locators.py"
)
APP_URL = "http://localhost:3000/login.html"


def _app_esta_no_ar() -> bool:
    try:
        with urlopen(APP_URL, timeout=1) as resposta:
            return resposta.status == 200
    except Exception:
        return False


@pytest.fixture(scope="session", autouse=True)
def servidor_local():
    if _app_esta_no_ar():
        yield
        return

    processo = subprocess.Popen(
        [sys.executable, os.path.join(project_root, "app", "servidor.py")],
        cwd=project_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for _ in range(30):
        if _app_esta_no_ar():
            break
        time.sleep(0.2)
    else:
        processo.terminate()
        raise RuntimeError("Servidor local nao subiu em http://localhost:3000")

    yield

    processo.terminate()
    try:
        processo.wait(timeout=5)
    except subprocess.TimeoutExpired:
        processo.kill()


def _ler_locators() -> dict:
    with open(LOCATORS_PATH, "r", encoding="utf-8") as f:
        conteudo = f.read()
    matches = re.findall(r'(\w+)\s*=\s*"([^"]+)"', conteudo)
    ignorar = {"URL", "TEXTO_SUCESSO"}
    return {nome: seletor for nome, seletor in matches if nome.isupper() and nome not in ignorar}


def _processar_analise(url: str, pytest_config=None):
    locators_dict = _ler_locators()
    try:
        from ai.agent import analisar_sync
        resultado = analisar_sync(url, locators_dict)

        from analysis.failure_handler import salvar_json
        caminho_json = salvar_json(resultado, url)

        locators_por_nome = resultado.get("locator_names", {})
        locators = resultado.get("locators", {})
        if not locators_por_nome and not locators:
            print("Nao foi possivel obter sugestao da IA.")
            erro = resultado.get("erro", "")
            if erro:
                print(f"Erro: {erro}")
            print(f"JSON salvo em: {caminho_json}")
            return False

        # Salva resultado e encerra (nao aplica correcao automaticamente)
        print(f"Analise concluida!")
        print(f"JSON salvo em: {caminho_json}")
        return False

    except Exception as e:
        print(f"Erro durante analise: {e}")
        return False


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        if report.passed:
            print("\nTESTE FINALIZADO COM SUCESSO!\n")

        if report.failed:
            error_text = str(report.longrepr)
            if "Timeout" in error_text or "Error" in error_text:
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__

                print("\n" + "="*60)
                print("TESTE FALHOU")
                print("="*60)
                print()
                
                # Nao precisa fechar browser manualmente - pytest-playwright faz isso
                # automaticamente no teardown
                
                print("Iniciando analise automatica...\n")
                
                recuperado = _processar_analise(APP_URL, item.config)
                if recuperado:
                    report.outcome = "passed"
                    report.longrepr = None


# @pytest.hookimpl(trylast=True)
# def pytest_sessionfinish(session, exitstatus):
#     """
#     Hook chamado ao final da sessao de testes.
#     Mata processos Chrome travados para evitar o hang.
#     """
#     import psutil
#     
#     # Mata processos chrome/playwright travados (silenciosamente)
#     try:
#         for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
#             try:
#                 name = proc.info['name'].lower() if proc.info['name'] else ''
#                 cmdline_list = proc.info['cmdline'] or []
#                 cmdline = ' '.join(cmdline_list).lower()
#                 
#                 # Identifica processos do Playwright/Chrome
#                 if ('chrome' in name or 'msedge' in name) and ('remote-debugging' in cmdline or 'user-data-dir' in cmdline):
#                     try:
#                         proc.kill()
#                     except:
#                         pass
#             except (psutil.NoSuchProcess, psutil.AccessDenied):
#                 pass
#     except Exception:
#         pass
#     
#     # Força exit imediato para evitar hang no teardown do pytest-playwright
#     os._exit(exitstatus)
