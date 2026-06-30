# QA Hackathon

Assistente inteligente que corrige automaticamente seletores CSS quebrados em testes BDD com Playwright. Quando um teste falha por mudanca no DOM, o navegador analisa a pagina real, compara os seletores do arquivo de locators com os elementos encontrados na DOM, com base na execução feita pelo Browser Use e aplica a correção.

## Dependencias


cd qa-hackathon
pip install -r requirements.txt
python -m playwright install chromium

## Como testar

### 1. Ligar o servidor local

python app/servidor.py

### 2. Executar o teste

Em outro terminal:

python -m pytest bdd/ -v 

### 4. Aplicar a correção

python aplicar_correcao.py

## Tecnologias

| Tecnologia | Papel |
|-----------|-------|
| Playwright | Automacao do navegador |
| pytest-bdd | Cenarios BDD |
| Browser Use| Base Auxiliasr para correções |
| DOM + Playwright | Descoberta direta dos seletores corretos |
| Gemini (Google) | Fallback para casos em que a DOM nao basta |
