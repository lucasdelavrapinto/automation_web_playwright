# Automação Web

Essa foi feita para automatizar o processo de configuração do dos roteador, habilitando o bloqueio de acesso a internet.

Para utilizar, basta executar o comando `python3 index.py` e aguardar.

# Como funciona

O script utiliza o Playwright para acessar a página de login do roteador e executar os comandos necessários para habilitar o bloqueio de acesso a internet.

# Como instalar

Instale o Playwright:

`pip3 install playwright`

# CRON

Para executar o script automaticamente, você pode usar o CRON, como exemplo:

`59 23 * * * python3 index.py` que irá executar o script todos dias as 23:59.

---

# Tarefas

[] no final gerar um zip da pasta downloads
