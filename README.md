# QA Hackathon

Assistente inteligente que corrige automaticamente seletores CSS quebrados em testes BDD com Playwright. Quando um teste falha por mudanca no DOM, o navegador analisa a pagina real, compara os seletores do arquivo de locators com os elementos encontrados na DOM e aplica a correcao. O Gemini fica como fallback quando a descoberta direta pela DOM nao for suficiente.

---

## Dependencias

```bash
cd qa-hackathon
pip install -r requirements.txt
python -m playwright install chromium
```

## Configurar chave Gemini

1. Copie o `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edite `.env` e coloque sua chave: `GEMINI_API_KEY=sua_chave_real`
3. Para nao subir sua chave no git acidentalmente:
   ```bash
   git update-index --skip-worktree .env
   ```

## Como testar

### 1. Ligar o servidor local

```bash
python app/servidor.py
```

Deixe rodando em segundo plano (http://localhost:3000).

### 2. Executar o teste

Em outro terminal:

```bash
python -m pytest bdd/ -v
```

O teste abre o navegador, preenche login e verifica a mensagem de sucesso.

**Nota:** O pytest finaliza automaticamente após os testes.

### 3. Simular um locator quebrado

Edite `playwright_layer/locators/login_locators.py` e troque um seletor por um valor inexistente:

```python
CAMPO_USUARIO = "#x-invalido"
```

Rode o teste de novo:

```bash
python -m pytest bdd/ -v
```

O teste falha, o navegador analisa a DOM da pagina, descobre o seletor certo (`#usuario`), mostra o resultado e **salva no JSON**.

### 4. Aplicar a correção

Após o teste falhar e gerar o JSON com as correções, execute:

```bash
python aplicar_correcao.py
```

O script mostra as correções, pergunta se quer aplicar, corrige automaticamente o arquivo e re-testa **com navegador visível**.

### 5. Multiplos locators quebrados

Quebre quantos quiser no `login_locators.py` — a IA corrige todos de uma vez na mesma analise.

---

## Scripts auxiliares

- `aplicar_correcao.py` — Aplica correções do JSON e re-testa com navegador visível

---

## Estrutura do projeto

```
qa-hackathon/
├── app/
│   ├── login.html              # Pagina de login (HTML real)
│   └── servidor.py             # Servidor HTTP local
├── bdd/
│   ├── features/
│   │   └── login.feature       # Cenario BDD
│   └── steps/
│       └── test_login_steps.py # Step definitions
├── playwright_layer/
│   ├── locators/
│   │   └── login_locators.py   # Seletores CSS (edite aqui pra testar)
│   └── pages/
│       └── login_page.py       # Page Object
├── analysis/
│   └── failure_handler.py      # Salva JSON com resultado
├── ai/
│   └── agent.py                # browser-use + Gemini
├── output/
│   └── ai/                     # JSON gerado (ai_fix.json)
├── conftest.py                 # Hook que dispara a analise
├── corretor.py                 # Aplica correcoes no arquivo
├── .env                        # Sua chave Gemini (versionado)
├── .env.example                # Modelo para .env
├── .gitignore
├── requirements.txt
└── pytest.ini
```

## Tecnologias

| Tecnologia | Papel |
|-----------|-------|
| Playwright | Automacao do navegador |
| pytest-bdd | Cenarios BDD |
| DOM + Playwright | Descoberta direta dos seletores corretos |
| Gemini (Google) | Fallback para casos em que a DOM nao basta |
