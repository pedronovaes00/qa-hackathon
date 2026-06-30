from pytest_bdd import scenarios, given, when, then
from playwright.sync_api import Page
from playwright_layer.pages.login_page import LoginPage

scenarios("../features/login.feature")


@given("que estou na página de login")
def abrir_pagina_login(page: Page):
    login_page = LoginPage(page)
    login_page.abrir()
    login_page.deve_estar_visivel()


@when('preencho o usuário "admin" e a senha "123456"')
def preencher_credenciais(page: Page):
    login_page = LoginPage(page)
    login_page.preencher_usuario("admin")
    login_page.preencher_senha("123456")


@when("submeto o formulário de login")
def submeter_login(page: Page):
    login_page = LoginPage(page)
    login_page.submeter()


@then("vejo a mensagem de sucesso")
def verificar_mensagem(page: Page):
    login_page = LoginPage(page)
    login_page.verificar_mensagem_sucesso()
