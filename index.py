import json
import asyncio
from time import sleep
from playwright.async_api import async_playwright
import os
import sys
import sqlite3

CREDENTIALS_FILE = "credentials.json"
LOGIN_URL = "https://safracontrol.souagrosolucoes.com.br/invoices/list"

lista_de_chaves = []

# Carregar credenciais salvas ou pedir pro usuário
def load_credentials():
    try:
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        user = input("Usuário: ")
        password = input("Senha: ")
        creds = {"user": user, "password": password}
        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(creds, f)
        return creds
    
async def login(page, creds):
# Preencher campos de login (ajustar os seletores depois)
    await page.fill("#email", creds["user"])
    await page.fill("#password", creds["password"])
    sleep(1)
    await page.click(".antd-pro-pages-user-login-components-login-index-submit")

    # Esperar redirecionamento (ajustar conforme necessário)
    await page.wait_for_load_state("networkidle")

    # await page.goto("https://safracontrol.souagrosolucoes.com.br/invoices/list")
    await page.click("div.ant-card.ant-card-bordered.ant-card-hoverable.css-kiyw7i")
    sleep(10)

def pastaNome(nota, cliente):
    nome_pasta = "downloads/" + nota + "_" + cliente
    # Verifique se a pasta já existe
    if not os.path.exists(nome_pasta):
        # Crie a pasta
        os.mkdir(nome_pasta)
        print(f"Pasta '{nome_pasta}' criada com sucesso!")
    else:
        print(f"A pasta '{nome_pasta}' já existe.")
    return nome_pasta

def initdb():
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notas (
            id INTEGER PRIMARY KEY,
            chave_acesso VARCHAR(255) NOT NULL,
            success BOOLEAN
        )
    ''')
    conn.commit()
    conn.close()

def insert_nota(chave_acesso, success):
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM notas WHERE chave_acesso = ?', (chave_acesso,))
    exists = cursor.fetchone()
    if not exists:
        cursor.execute('''
            INSERT INTO notas (chave_acesso, success)
            VALUES (?, ?)
        ''', (chave_acesso, success))
        conn.commit()
    conn.close()

def lista_notas():
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    cursor.execute('SELECT chave_acesso FROM notas WHERE success = 0')
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def marcar_nota_sucesso(chave_acesso):
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE notas SET success = 1 WHERE chave_acesso = ?', (chave_acesso,))
    conn.commit()
    conn.close()

async def run():
    initdb()    

    creds = load_credentials()
    os.makedirs("chrome_profile", exist_ok=True)  # pasta onde o perfil será guardado

    if lista_de_chaves:
        for item in lista_de_chaves:
            print(f"Chave de acesso: {item}")
            insert_nota(str(item), False)

    # Iniciar Playwright

    lista = lista_notas()

    async with async_playwright() as p:
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir="chrome_profile",
            channel="chrome",  # <- força usar o Chrome instalado
            headless=False,     # <- mostra o navegador
            accept_downloads=True,
            args=[
                "--disable-popup-blocking",
                "--disable-download-notification"
            ]
        )
        page = await browser_context.new_page()

        for item in lista:

            print(f"Iniciando processo para a chave: {item}")

            await page.goto(LOGIN_URL)

            await page.wait_for_selector("input#nfeKey.ant-input.css-kiyw7i")

            sleep(2)

            await page.fill("input#nfeKey.ant-input.css-kiyw7i", item)

            sleep(1)

            await page.keyboard.press("Enter")

            sleep(10)

            await page.wait_for_selector("tbody.ant-table-tbody")

            last_row = page.locator("tr.ant-table-row.ant-table-row-level-0").first

            options_cell = last_row.locator(
                "td.ant-table-cell.ant-table-cell-fix-right.ant-table-cell-fix-right-first"
            )

            await options_cell.scroll_into_view_if_needed()
            await options_cell.hover()

            await options_cell.get_by_role("img", name="eye").click()
            sleep(10)

            await page.wait_for_selector("div.ant-descriptions-view")
            itens_da_nota = await page.query_selector_all("td.ant-descriptions-item span.ant-descriptions-item-content")
            print(f"Total de itens encontrados: {len(itens_da_nota)}")

            valores = []
            for s in itens_da_nota:
                texto = await s.text_content()
                if texto:
                    valores.append(texto.strip())

            numero_nota = valores[0]
            nome_cliente = valores[2]
            chave_acesso_nota = valores[12]
            print("Chave de acesso da nota no portal:", chave_acesso_nota)
            print(numero_nota)
            print(nome_cliente)

            if chave_acesso_nota != item:
                print(f"⚠ A chave de acesso da nota ({chave_acesso_nota}) não corresponde à chave pesquisada ({item}). Pulando...")
                sys.exit

            nome_pasta = pastaNome(numero_nota, nome_cliente)

            await page.click('div#rc-tabs-0-tab-attachedFiles.ant-tabs-tab-btn')

            sleep(5)

            await page.wait_for_selector("div.ant-table.ant-table-middle.css-kiyw7i.ant-table-fixed-column.ant-table-scroll-horizontal.ant-table-has-fix-right")
            rows = await page.query_selector_all("div.ant-table-has-fix-right div.ant-table-content table tbody.ant-table-tbody tr.ant-table-row.ant-table-row-level-0")

            print(f"Total de arquivos encontrados: {len(rows)}")
            
            for index, row in enumerate(rows, start=1):
                download_btn = await row.query_selector("button.ant-btn-icon-only >> svg[data-icon='download']")
                if download_btn:
                    print(f"Baixando arquivo {index}...")
                    # Clica no botão de download e aguarda o evento de download
                    async with page.expect_download() as download_info:
                        await download_btn.click()

                    download = await download_info.value
                    print(download)
                    # Nome sugerido pelo servidor (o mesmo do Chrome normal)
                    nome_arquivo = download.suggested_filename
                    caminho = os.path.join(nome_pasta, nome_arquivo)

                    await download.save_as(caminho)
                    print(f"✔ Arquivo salvo.")

                    marcar_nota_sucesso(item)
                    print(f"✔ Nota atualizada no banco de dados.")

                else:
                    print(f"⚠ Nenhum botão de download encontrado na linha {index}")
            
            print(f"Finalizando esta chave")
            print(f"Indo para a próxima")

        print(f"Fim")
        #Adicionar uma função para criar um zip da pasta downloads.

        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(run())
