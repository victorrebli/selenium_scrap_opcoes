from selenium import webdriver # for webdriver 
from selenium.webdriver.chrome.options import Options  # for suppressing the browser
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
import pandas as pd
from google.cloud import storage
import os
from datetime import datetime
import chromedriver_binary
from flask import Flask, send_file, request
from webdriver_manager.chrome import ChromeDriverManager
import json
import traceback

app = Flask(__name__)

storage_client = storage.Client()
bucket = storage_client.get_bucket("stock_opcoes")

COLS = ['TICKER','VENCIMENTO','DIAS_UTEIS', 'TIPO', 'FM',
        'MOD','STRIKE','A/I/OTM','ULTIMO','VAR_%', 'DATA/HORA',
        'NUM_DE_NEG','VOLUME_FINANCEIRO','VOL_IMPLICITA',
        'DELTA','GAMA','THETA_$','THETA_%','VEGA']

def _save_file(_data, _name):
    date_file = datetime.now().strftime("%d-%m-%Y-%H:%M")
    _name = f'{_name}_{date_file}.csv'
    blob = bucket.blob(f'write_p/{_name}')
    blob.upload_from_string(_data.to_csv(index=False, sep=';'), 'text/csv')
    print('Saved')
    

def main(LISTA):
    dat_final = dict()
    inicio = time.asctime(time.localtime(time.time()))
    port = 1024
    lista_all = dict()
    for idx, _ticker in enumerate(LISTA):
        _inicio = time.asctime(time.localtime(time.time()))
        print(f'{idx} de {len(LISTA)} Ticker: {_ticker}')

        tentativas = 0
        maximo = 5
        while tentativas < maximo:

            time.sleep(10)
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("window-size=1024,768")
            chrome_options.add_argument("--no-sandbox")

            print(f'Tentativa {tentativas + 1} de {5}')
            driver = webdriver.Chrome(ChromeDriverManager().install(),options=chrome_options)
            try:    
                driver.get(f'https://opcoes.net.br/opcoes/bovespa/{_ticker}')
            except:
                print('Entrou no except 1')
                tentativas += 1
                if tentativas >= maximo:
                    print(f'Não foi possivel obter nada desse ticker')
                    lista_all[_ticker] = 'Não foi possivel obter nada desse ticker'
                continue

            try:    
                driver.execute_script("document.querySelector('.fSetLiquidez.grade-bloco.immediate-collapse').style = 'display: block;'")
            except:
                print('Entrou no except 2')
                tentativas += 1  
                if tentativas >= maximo:
                    print(f'Não foi possivel obter nada desse ticker')
                    lista_all[_ticker] = 'Não foi possivel obter nada desse ticker'

                continue
            try:
                driver.find_element_by_xpath("//input[@id='todas']").click()
            except:
                print('Entrou no except 3')
                tentativas += 1
                if tentativas >= maximo:
                    print(f'Não foi possivel obter nada desse ticker')
                    lista_all[_ticker] = 'Não foi possivel obter nada desse ticker'
                continue  

            time.sleep(10)    
            try:
                items = driver.find_elements_by_xpath("//ul[@id = 'listavencimentos']//li[not(@class)]")
                print(f'len:{len(items)}')
                if len(items) == 0:
                    tentativas += 1
                    if tentativas >= maximo:
                        print(f'Não foi possivel obter nada desse ticker')
                        lista_all[_ticker] = 'Não foi possivel obter nada desse ticker'
                    continue

                var_0 = driver.find_element_by_class_name("dataTables_info").text[0:3]
                if int(var_0) != 0:
                    items[0].click()
                    try:
                         var_1 = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'dataTables_info')))
                         var_1 = var_1.text[0:3]
                    except:
                         traceback.print_exc()
                         tentativas += 1
                         if tentativas >= maximo:
                             print('Náo foi possivel obter nada desse ticker')
                             lista_all[_ticker] = 'Nao foi possivel obter nada desse ticker'
                         continue
                    if int(var_1) == 0:
                        for item in items:
                            item.click()

                    else:
                       items[0].click()
                       items[1].click()
                       for item in items:
                            item.click() 
                else:
                    for item in items:
                        item.click()
            except:
                traceback.print_exc()
                tentativas += 1
                if tentativas >= maximo:
                        print(f'Não foi possivel obter nada desse ticker')
                        lista_all[_ticker] = 'Não foi possivel obter nada desse ticker'
                continue 

            move = ActionChains(driver)
            sliders = driver.find_elements_by_xpath("//*[@id='strike-range']/span")
            valor = 1
            maximo = 0
            while True:
                    if maximo >= 30:
                        break
                    move.click_and_hold(sliders[0]).move_by_offset(-valor,0).release().perform()
                    if sliders[0].get_attribute('style') == 'left: 0%;':
                        break
                    valor += 3
                    maximo += 1

            valor = 1
            maximo = 0            
            while True:
                    if maximo >= 30:
                        break

                    move.click_and_hold(sliders[1]).move_by_offset(valor,0).release().perform()
                    if sliders[1].get_attribute('style') == 'left: 100%;':
                        break
                    valor += 3
                    maximo += 1    

            print(f'Qtd opções: {driver.find_element_by_class_name("dataTables_info").text}')
            print(f'Sucesso depois de {tentativas + 1} tentativas(s)')
            port += 1
            lista_all[_ticker] = driver.find_element_by_class_name("dataTables_info").text
            print('######################')
            break

        print('Coletando informacoes.....')    
        _dd = driver.find_element_by_class_name('fSetAtivoBase.grade-bloco')
        data_ab = _dd.find_element_by_xpath("//span[contains(@data-mkt-prop,'y')]").text
        dd = driver.find_element_by_class_name('dataTables_wrapper.no-footer')
        l=dd.find_elements_by_xpath ("//*[@id='tblListaOpc']/tbody/tr")

        dici_final = dict()
        for idx, i in enumerate(l):
            _dici_final = []
            for j in i.find_elements_by_tag_name('td'):
                _dici_final.append(j.text) 

            dici_final[idx] = _dici_final
        
        
        dat_full = pd.DataFrame.from_dict(dici_final, orient='index', columns=COLS)
        dat_full['data_collect_scrap'] = data_ab
        dat_full['FM'] = dat_full['FM'].apply(lambda x: 'sim' if x != '' else 'nao')
        _save_file(dat_full, _ticker)
        _fim = time.asctime(time.localtime(time.time()))
        print(f'Inicio: {_inicio} - Fim: {_fim}')
        
    
    fim = time.asctime(time.localtime(time.time()))
    print(f'Inicio_all: {inicio} - Fim_all: {fim}')    

@app.route("/", methods=["POST"])
def hello_world():
    if request.method == 'POST':

       request1 = request.get_data()
       try: 
           request_json = json.loads(request1.decode())
       except ValueError as e:
           print(f"Error decoding JSON: {e}")
           return "JSON Error", 400
       lista = request_json.get("lista") or "Nada"
       main(lista)

    return 'teste'

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=8080)



