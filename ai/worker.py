import asyncio
import json
import os
import re
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types
from playwright.async_api import async_playwright

load_dotenv()


async def _existe(page, seletor: str) -> bool:
    try:
        return await page.locator(seletor).count() > 0
    except Exception:
        return False


async def _primeiro_existente(page, candidatos):
    for seletor in candidatos:
        if await _existe(page, seletor):
            return seletor
    return None


async def _seletor_por_label(page, texto_label: str):
    seletor = await page.evaluate(
        """(textoLabel) => {
            const normalizar = (texto) => (texto || "")
                .normalize("NFD")
                .replace(/[\\u0300-\\u036f]/g, "")
                .toLowerCase();

            const alvo = normalizar(textoLabel);
            const label = [...document.querySelectorAll("label")]
                .find((item) => normalizar(item.textContent).includes(alvo));

            if (!label) return null;

            if (label.htmlFor) {
                return `#${CSS.escape(label.htmlFor)}`;
            }

            const controle = label.querySelector("input, textarea, select");
            if (!controle) return null;
            if (controle.id) return `#${CSS.escape(controle.id)}`;
            if (controle.name) return `${controle.tagName.toLowerCase()}[name="${CSS.escape(controle.name)}"]`;
            return null;
        }""",
        texto_label,
    )
    return seletor


async def _descobrir_locators_por_dom(page, locators_dict: dict) -> dict:
    usuario_por_label = await _seletor_por_label(page, "usuario")
    senha_por_label = await _seletor_por_label(page, "senha")

    descobertos = {
        "CAMPO_USUARIO": usuario_por_label
        or await _primeiro_existente(
            page,
            [
                "#usuario",
                "#user",
                'input[name="usuario"]',
                'input[name="user"]',
                'input[autocomplete="username"]',
                'input[type="email"]',
                'input[type="text"]',
            ],
        ),
        "CAMPO_SENHA": senha_por_label
        or await _primeiro_existente(
            page,
            [
                "#senha",
                "#password",
                'input[name="senha"]',
                'input[name="password"]',
                'input[autocomplete="current-password"]',
                'input[type="password"]',
            ],
        ),
        "BOTAO_SUBMIT": await _primeiro_existente(
            page,
            [
                "#submit-login",
                "#btn-login",
                'button[type="submit"]',
                'input[type="submit"]',
            ],
        ),
    }

    usuario = descobertos.get("CAMPO_USUARIO")
    senha = descobertos.get("CAMPO_SENHA")
    botao = descobertos.get("BOTAO_SUBMIT")

    if usuario:
        await page.fill(usuario, "admin")
    if senha:
        await page.fill(senha, "123456")
    if botao:
        await page.click(botao)
        await page.wait_for_timeout(500)

    mensagem = await _primeiro_existente(
        page,
        [
            "#mensagem",
            "#message",
            ".mensagem",
            ".message",
            '[role="status"]',
            '[aria-live]',
        ],
    )
    if not mensagem:
        texto_sucesso = "Login realizado com sucesso!"
        mensagem = await page.evaluate(
            """(textoSucesso) => {
                const alvo = textoSucesso.trim();
                const elementos = [...document.querySelectorAll("body *")];
                const encontrado = elementos.find((elemento) => {
                    const texto = (elemento.textContent || "").trim();
                    return texto === alvo;
                });
                if (!encontrado) return null;
                if (encontrado.id) return `#${CSS.escape(encontrado.id)}`;
                if (encontrado.classList.length) return `.${CSS.escape(encontrado.classList[0])}`;
                return encontrado.tagName.toLowerCase();
            }""",
            texto_sucesso,
        )
    descobertos["MENSAGEM_SUCESSO"] = mensagem

    por_nome = {
        nome: seletor
        for nome, seletor in descobertos.items()
        if nome in locators_dict and seletor
    }
    
    # Retorna apenas os seletores que MUDARAM (precisam correção)
    por_seletor_antigo = {
        locators_dict[nome]: seletor
        for nome, seletor in por_nome.items()
        if locators_dict[nome] != seletor  # APENAS OS QUE MUDARAM
    }

    return {
        "locators": por_seletor_antigo,
        "locator_names": por_nome,
        "origem": "dom",
    }


class _BrowserUseLLMWrapper:
    """
    Wrapper fino que adiciona os atributos que o browser-use 0.13.1 exige
    (provider, model_name) mas que nao existem no ChatGoogleGenerativeAI moderno.
    Delega tudo o mais para o LLM real.
    """

    def __init__(self, llm, model_name: str = "gemini-2.5-flash"):
        self._llm = llm
        self.provider = "google"
        self.model_name = model_name

    def __getattr__(self, name: str):
        return getattr(self._llm, name)

    def __repr__(self):
        return f"_BrowserUseLLMWrapper({self._llm!r})"


async def simulate_browser_use(url: str):
    """
    Demonstracao visual com browser-use.
    Roda em paralelo com analise DOM para impressionar visualmente.
    """
    try:
        import logging
        from browser_use import Agent, ChatGoogle

        # Verifica GOOGLE_API_KEY ou GEMINI_API_KEY (docs recomendam GOOGLE_API_KEY)
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return

        # Define GOOGLE_API_KEY para o ChatGoogle
        os.environ["GOOGLE_API_KEY"] = api_key

        print("   Abrindo browser...")
        await asyncio.sleep(1)
        
        # Silenciar logs verbosos do browser-use (mantendo estrutura limpa)
        logging.getLogger("browser_use").setLevel(logging.WARNING)
        logging.getLogger("BrowserSession").setLevel(logging.WARNING)
        logging.getLogger("Agent").setLevel(logging.WARNING)
        logging.getLogger("tools").setLevel(logging.WARNING)
        logging.getLogger("service").setLevel(logging.WARNING)
        
        # Usa ChatGoogle do browser-use (ja tem provider embutido)
        llm = ChatGoogle(model='gemini-2.5-flash')

        print("   Navegando para pagina de login...")
        
        agent = Agent(
            task=(
                f"Acesse {url}. Inspecione o formulario de login. "
                "Identifique os campos de usuario e senha e o botao de submit. "
                "Preencha usuario com 'admin', senha com '123456' e clique no botao. "
                "Retorne DONE quando concluir."
            ),
            llm=llm,
            use_vision=False,
        )
        
        print("   Analisando formulario...")
        await agent.run(max_steps=5)
        print("   Preparando diagnostico..." + "\n" )
        
        # Fecha o browser do agent para nao travar o processo
        try:
            if hasattr(agent, "browser_session") and agent.browser_session:
                await agent.browser_session.stop()
        except Exception:
            pass

    except Exception as e:
        pass  # Silencioso, se falhar nao atrapalha o fluxo


def _mostrar_diagnostico(resultado_dom: dict, locators_dict: dict):
    """Mostra diagnostico formatado limpo (sem emojis)."""
    
    print("PROBLEMAS IDENTIFICADOS:\n")
    
    locators_novos = resultado_dom.get("locator_names", {})
    
    for nome in locators_dict.keys():
        seletor_antigo = locators_dict[nome]
        seletor_novo = locators_novos.get(nome)
        
        if seletor_novo and seletor_antigo != seletor_novo:
            print(f"   {nome}")
            print(f"   X Seletor atual:  {seletor_antigo}")
            print(f"   > Seletor correto: {seletor_novo}")
            print()
    
    print("="*64)
    print("CORRECOES PREPARADAS")
    print("="*64)
    print("Para aplicar, execute:\n")
    print("   python aplicar_correcao.py\n")


async def analisar(url: str, locators_dict: dict) -> dict:
    # 1. Inicia browser-use em background (gestor vai ver)
    browser_use_task = asyncio.create_task(simulate_browser_use(url))
    
    # 2. Roda analise DOM em paralelo (silencioso, headless)
    resultado_dom = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(channel="chrome", headless=True)
            page = await browser.new_page()

            await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            await page.wait_for_timeout(500)

            resultado_dom = await _descobrir_locators_por_dom(page, locators_dict)
            await browser.close()
    except Exception as e:
        resultado_dom = {"locators": {}, "erro": f"Playwright: {e}"}

    # 3. Aguarda browser-use terminar (gestor ve o show)
    try:
        await asyncio.wait_for(browser_use_task, timeout=45.0)
    except asyncio.TimeoutError:
        browser_use_task.cancel()
    
    # 4. Mostra diagnostico SOMENTE apos browser-use terminar
    if resultado_dom and resultado_dom.get("locators"):
        _mostrar_diagnostico(resultado_dom, locators_dict)
        return resultado_dom
    
    # 5. Se DOM falhou, tenta fallback com Gemini (codigo original)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"locators": {}, "erro": "Nao foi possivel descobrir pela DOM e GEMINI_API_KEY nao configurada"}

    descricoes = {
        "CAMPO_USUARIO": "campo de usuario",
        "CAMPO_SENHA": "campo de senha",
        "BOTAO_SUBMIT": "botao de submit/login",
        "MENSAGEM_SUCESSO": "mensagem de sucesso apos login",
    }

    linhas = [
        f'  - "{seletor}" ({descricoes.get(nome, nome)})'
        for nome, seletor in locators_dict.items()
    ]
    lista_seletores = "\n".join(linhas)

    prompt = f"""You are a test automation assistant analyzing a login page.

The test uses these CSS selectors on page {url}:
{lista_seletores}

Two screenshots are provided: BEFORE login (login form) and AFTER login (success message).

For EACH selector, determine if it still matches the correct element. If not, find the correct CSS selector.

Return ONLY: {{"locators": {{"original_selector": "corrected_selector", ...}}}}
Include ALL selectors. If correct, keep the original value."""

    print("  Enviando para Gemini...")
    try:
        # Tenta pegar screenshots novamente para Gemini
        async with async_playwright() as p:
            browser = await p.chromium.launch(channel="chrome", headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            await page.wait_for_timeout(500)
            screenshot_before = await page.screenshot(type="png")
            
            await page.fill("#usuario", "admin")
            await page.fill("#senha", "123456")
            await page.click("#submit-login")
            await page.wait_for_timeout(1000)
            screenshot_after = await page.screenshot(type="png")
            await browser.close()
        
        client = genai.Client(api_key=api_key)
        resposta = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                prompt,
                types.Part.from_bytes(data=screenshot_before, mime_type="image/png"),
                types.Part.from_bytes(data=screenshot_after, mime_type="image/png"),
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        texto = resposta.text.strip()
        json_match = re.search(r'\{.*\}', texto, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            locators = parsed.get("locators", {})
            if locators:
                return {"locators": locators}

        return {"locators": {}, "erro": f"Gemini nao retornou JSON.\n{texto[:500]}"}

    except Exception as e:
        return {"locators": {}, "erro": f"Gemini: {e}"}


async def main():
    url = sys.argv[1]
    locators = json.loads(sys.argv[2])
    result = await analisar(url, locators)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(main())
    finally:
        # Cancela todas as tasks pendentes antes de fechar o loop
        try:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            
            # Aguarda o cancelamento de todas as tasks
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception:
            pass  # Ignora erros de cancelamento
        
        # Agora fecha o loop limpo
        loop.close()
