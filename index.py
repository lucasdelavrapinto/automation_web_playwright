import json
import asyncio
from time import sleep
from playwright.async_api import async_playwright

CREDENTIALS_FILE = "credentials.json"
LOGIN_URL = "http://192.168.1.1/"  # depois você troca pelo seu

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

async def run():
    creds = load_credentials()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Acessar página de login
        await page.goto(LOGIN_URL)

        # Preencher campos de login (ajustar os seletores depois)
        await page.fill("#Frm_Username", creds["user"])
        await page.fill("#Frm_Password", creds["password"])
        sleep(1)
        await page.click("#LoginId")

        # Esperar redirecionamento (ajustar conforme necessário)
        await page.wait_for_load_state("networkidle")

        await page.click("#internet")
        sleep(1)
        await page.click("#security")
        sleep(1)
        await page.click("#filterCriteria")
        sleep(1)
        await page.click("#MacFilterEnable1") #LIGAR BLOQUEIO DE INTERNET
        # await page.click("#MacFilterEnable0") #DESLIGAR BLOQUEIO DE INTERNET
        sleep(1)
        await page.click("#Btn_apply_FirewallConf")
      
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
