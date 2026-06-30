import json
import os
import subprocess as sp
import sys

from dotenv import load_dotenv

load_dotenv()


def analisar_sync(url: str, locators_dict: dict) -> dict:
    try:
        worker = os.path.join(os.path.dirname(os.path.abspath(__file__)), "worker.py")
        locators_json = json.dumps(locators_dict, ensure_ascii=False)

        proc = sp.Popen(
            [sys.executable, worker, url, locators_json],
            stdout=sp.PIPE,
            stderr=sp.STDOUT,
            text=True,
            bufsize=1,
        )

        linhas_saida = []
        try:
            for linha in proc.stdout:
                linha_limpa = linha.strip()
                if not linha_limpa.startswith("{"):
                    print(linha, end="")
                linhas_saida.append(linha_limpa)
            proc.wait(timeout=180)
        except sp.TimeoutExpired:
            proc.kill()
            print("  Analise excedeu o tempo. Abortando.")
            return {"locators": {}, "erro": "Timeout"}

        if proc.returncode != 0:
            return {"locators": {}, "erro": f"Codigo de saida: {proc.returncode}"}

        if not linhas_saida:
            return {"locators": {}, "erro": "Saida vazia."}

        for linha in reversed(linhas_saida):
            if linha.startswith("{"):
                return json.loads(linha)

        return {"locators": {}, "erro": "JSON nao encontrado."}

    except sp.TimeoutExpired:
        print("  Analise excedeu o tempo. Abortando.")
        return {"locators": {}, "erro": "Timeout"}
    except Exception as e:
        print(f"  Erro na analise: {e}")
        import traceback
        traceback.print_exc()
        return {"locators": {}, "erro": str(e)}
