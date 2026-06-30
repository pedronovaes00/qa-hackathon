# language: pt

Funcionalidade: Login
  Como um usuário do sistema
  Quero fazer login no sistema
  Para acessar minha conta

  Cenário: Login com sucesso
    Dado que estou na página de login
    Quando preencho o usuário "admin" e a senha "123456"
    E submeto o formulário de login
    Então vejo a mensagem de sucesso
