import os
from os.path import join, exists, getctime, basename
from json import loads
from time import sleep
from locale import setlocale, LC_TIME
from datetime import date
from pandas import read_csv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire.webdriver import ChromeOptions, Chrome

# Define a configuração de localidade globalmente
setlocale(LC_TIME, 'pt_BR.UTF-8')

class BaixarRelatorio:
    DATE_FORMAT = '%d_%m_%Y'
    
    def __init__(self, BASE_FOLDER=r'C:\Users\alpaula\Documents\9-Pé-de-meia\Pé-de-meia-dezembro',tipoBase='TRANSPORTE', credenciaisPath='credenciais.producao.txt'):
        self.BASE_FOLDER = BASE_FOLDER
        self.tipoBase = tipoBase
        self.credenciais = self._carregar_credenciais(credenciaisPath)
        self.proxy = self.credenciais['proxies']
        self.usuario = self.credenciais["Seges"]['login']
        self.senha = self.credenciais["Seges"]['senha']
        self.refresh = True

    def _carregar_credenciais(self, credenciaisPath):
        """Carrega as credenciais de um arquivo JSON."""
        with open(credenciaisPath, "r") as arquivo:
            return loads(arquivo.read().replace("'", '"'))

    def _generate_file_paths(self, base_dir):
        """Gera os caminhos completos para os arquivos Excel e CSV com base na data atual e tipo de base."""
        date_str = date.today().strftime(self.DATE_FORMAT)
        excel_path = join(base_dir, f"Excel_BASE_{self.tipoBase}_{date_str}.xlsx")
        csv_path = join(base_dir, f"csv_BASE_{self.tipoBase}_{date_str}.csv")
        return excel_path, csv_path

    def verifica_arquivos_existem(self, base_dir):
        """Verifica se os arquivos Excel e CSV já existem no diretório especificado."""
        excel_path, csv_path = self._generate_file_paths(base_dir)
        files = [join(base_dir, f) for f in os.listdir(base_dir)]
        return not (excel_path in files and csv_path in files)

    def esperar_por_downloads(self, download_directory):
        """Espera até que todos os arquivos tenham sido completamente baixados, monitorando arquivos temporários."""
        while not any([filename.endswith('.crdownload') for filename in os.listdir(download_directory)]):
	        pass
        while any(f.endswith('.crdownload') for f in os.listdir(download_directory)):
            pass
			
    def renomear_arquivo(self, base_dir):
        """Renomeia e converte o arquivo mais recente baixado em formatos Excel e CSV."""
        files = [join(base_dir, f) for f in os.listdir(base_dir) if not f.endswith('.crdownload')]
        if files:
            last_file = max(files, key=getctime)
            excel_path, csv_path = self._generate_file_paths(base_dir)

            # Salvar nos formatos Excel e CSV
            df = read_csv(last_file, dtype={1: str})
            df.to_excel(excel_path, index=False)
            df.to_csv(csv_path, sep=',', encoding='utf-8-sig', index=False)
            os.remove(last_file)
            print(f"Saved: {excel_path} \n{csv_path}")

    def criar_pasta(self, caminho):
        """Cria um diretório se ele ainda não existir."""
        if not exists(caminho):
            os.makedirs(caminho)
            print(f"A pasta '{caminho}' foi criada.")
        else:
            print(f"A pasta '{caminho}' já existe.")

    def configurar_diretorios(self):
        """Configura o diretório de destino para downloads com base no mês e ano atuais."""
        mes = date.today().strftime('%B').capitalize()
        ano = date.today().year
        mes_nome = f"{date.today().month:02} - {mes}"

        ano_dir = join(self.BASE_FOLDER, str(ano))
        download_Folder = join(ano_dir, f"{mes_nome}\\{self.tipoBase}")

        self.criar_pasta(ano_dir)
        self.criar_pasta(download_Folder)

        self.downloadFolder = download_Folder

    def baixar_relatorio(self, url):
        """Realiza o download do relatório, espera a conclusão e converte para os formatos desejados."""
        self.configurar_diretorios()
        
        # Verifica se o download é necessário
        if self.verifica_arquivos_existem(self.downloadFolder):
            chrome_options = ChromeOptions()
            prefs = {
                "download.default_directory": self.downloadFolder,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)

            seleniumwire_options = {'proxy': self.proxy}

            # Gerenciamento seguro do navegador
            self.navegador = Chrome(options=chrome_options, seleniumwire_options=seleniumwire_options)
            self.navegador.set_page_load_timeout(1800)

            try:
                self.navegador.get(url)
                wait = WebDriverWait(self.navegador, 10)
                wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="user_login"]'))).send_keys(self.usuario)
                wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="user_password"]'))).send_keys(self.senha)
                wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="new_user"]/div[3]/input'))).click()
                self.esperar_por_downloads(self.downloadFolder)
                sleep(0.15)
            finally:
                self.navegador.quit()
                self.renomear_arquivo(self.downloadFolder)