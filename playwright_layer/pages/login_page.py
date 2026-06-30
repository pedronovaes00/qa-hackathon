from playwright.sync_api import Page, expect
from playwright_layer.locators.login_locators import LoginLocators

DELAY = 250

class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.locators = LoginLocators

    def abrir(self):
        self.page.goto(self.locators.URL)
        self.page.wait_for_timeout(DELAY)

    def deve_estar_visivel(self):
        expect(self.page.locator(self.locators.CAMPO_USUARIO)).to_be_visible()
        expect(self.page.locator(self.locators.CAMPO_SENHA)).to_be_visible()
        expect(self.page.locator(self.locators.BOTAO_SUBMIT)).to_be_visible()
        self.page.wait_for_timeout(DELAY)

    def preencher_usuario(self, usuario: str):
        self.page.fill(self.locators.CAMPO_USUARIO, usuario)
        self.page.wait_for_timeout(DELAY)

    def preencher_senha(self, senha: str):
        self.page.fill(self.locators.CAMPO_SENHA, senha)
        self.page.wait_for_timeout(DELAY)

    def submeter(self):
        self.page.click(self.locators.BOTAO_SUBMIT)
        self.page.wait_for_timeout(DELAY)

    def verificar_mensagem_sucesso(self):
        expect(self.page.locator(self.locators.MENSAGEM_SUCESSO)).to_have_text(self.locators.TEXTO_SUCESSO)
        self.page.wait_for_timeout(DELAY)
