from playwright.sync_api import Page

class LoginLocators:
    URL = "http://localhost:3000/login.html"

    CAMPO_USUARIO = "#usuario"
    CAMPO_SENHA = "#senha"
    BOTAO_SUBMIT = "#submit-login"
    MENSAGEM_SUCESSO = "#mensagem"
    TEXTO_SUCESSO = "Login realizado com sucesso!"


