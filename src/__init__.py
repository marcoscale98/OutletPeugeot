#Ricorda! Stai usando la versione dei Driver per Chrome 83.0.4103.39
import json
import socket
import time

import requests
import urllib3
from selenium.webdriver import Chrome
from selenium.common.exceptions import NoSuchElementException
import telegram_send
import argparse
from urllib3.util import parse_url

DEBUG=False
stdErrFile = r'D:\\Marco\\Universita\\Progetti\\OutletPeugout\\stderr.txt'
sito = "https://webstore.peugeot.it/Cerca-per-categorie?lat=45.0607417&lng=7.528754299999999&LocationL=10098%20Rivoli%20TO%2C%20Italia&etd=0&mbd=1PP2S5P00000;&nbDisMax=20&GrTransmissionType=BVA00006&GrTransmissionTypeL=%20Automatico%20a%208%20Rapporti%20S&S&GrGrade=10000020;10001074&GrGradeL=&dst=210&MinPrice=&MaxPrice=20900"
optional_desiderati = ['Drive Assist Plus','Sensori di Parcheggio', 'con Visiopark']
cars_json=r'D:\\Marco\\Universita\\Progetti\\OutletPeugout\\src\\cars.json'

parser = argparse.ArgumentParser()
parser.add_argument('--loop',action='store_true' ,help='Indicates if you want script always on')
parser.add_argument('--delay',dest='delay',help='indicates seconds of delay before running the loop')
parser.set_defaults(delay=1)
args = parser.parse_args()

def controlla_novita(nuova_auto, carNum):
    manda_tg = False
    if carNum in list_auto_old:
        auto = list_auto_old[carNum]
        if auto['nome'] != nuova_auto['nome'] or auto['optional'] != nuova_auto['optional'] or auto['prezzo'] != nuova_auto['prezzo']:
            manda_tg = True
        list_auto_old.pop(carNum)
    else:
        manda_tg = True
    list_auto_new[carNum] = nuova_auto
    if manda_tg:
        messaggio = "<a href='{0}'>{1} al prezzo di: {2}</a>".format(nuova_auto['link'],nuova_auto['nome'],nuova_auto['prezzo'])
        telegram_send.send(messages=[messaggio],parse_mode="html")


def settings():
    # SETTINGS
    try: #check connessione
        driver.find_element_by_xpath("/html/body").find_element_by_id("main-frame-error")
        print("Errore di connessione")
        return False
    except NoSuchElementException as e:
        pass
    try:
        cookie_button = driver.find_element_by_xpath("/html/body/div[41]/div[4]/div[1]/a[1]")
        cookie_button.click()
        time.sleep(2)
    except NoSuchElementException:
        pass
    scrool_page()
    return True


def scrool_page():
    # scroll the page to load all the cars
    i = 0
    while i < 10:
        driver.execute_script("window.scrollBy(0,1000)")
        i += 1
        time.sleep(4)


def ha_optional_giusti(nuova_auto: dict, optional_che_vorrei):
    if 'GT Line' in nuova_auto['nome']:
        optional_che_vorrei.pop(1)
        optional_che_vorrei.pop(1)
    list_bool = map(lambda opt: opt in nuova_auto['optional'], optional_che_vorrei)
    for bool in list_bool:
        if not bool:
            return False
    return True

def get_new_car(cars_json='cars.json'):
    global list_auto_old, list_auto_new
    print("Nuova ricerca auto")
    # GET INFO

    list_auto_old = {}
    list_auto_new = {}
    try:
        with open(cars_json, 'r', encoding='UTF-8') as reader:
            list_auto_old = json.load(reader)
    except FileNotFoundError:
        with open(cars_json, 'x', encoding='UTF-8') as writer:
            writer.write(json.dumps({}))

    # while altre_pagine is not None:
    n_auto = -1
    n_page = 0
    auto_left = True
    page_left = True
    # while page_left:
    #     box_auto = analizza_pagina_auto(auto_left, n_auto, n_page)
    #     page_left = change_page(box_auto)
    # #end while
    analizza_pagina_auto(auto_left, n_auto, n_page)
    with open(cars_json, 'w', encoding='UTF-8') as writer:
        writer.write(json.dumps(list_auto_new, indent=3))
    print("Fine ricerca")


def analizza_pagina_auto(auto_left, n_auto, n_page):
    box_auto = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]")
    automobili = box_auto.find_elements_by_class_name('result')
    print("Trovate", str(len(automobili)), "auto da analizzare nella pagina numero", n_page)
    n_page += 1
    while auto_left or n_auto < len(automobili) - 1:
        n_auto += 1
        link = ""
        try:
            info_box = automobili[n_auto].find_elements_by_tag_name('div')[1].find_elements_by_tag_name('div')[
                0].find_element_by_tag_name('header')
        except Exception as e:  # non ci sono più auto
            auto_left = False
            continue
        try:
            # Trova info di link, prezzo e nome auto
            link = info_box.find_element_by_tag_name('h2').find_element_by_tag_name('a').get_attribute('href')
            info_link = parse_url(link)
            carNum = info_link.url.split("carNum")[1].split('&', maxsplit=1)[0].split("=")[1]
            nome = info_box.find_element_by_tag_name('h2').find_element_by_tag_name('a').text
            prezzo = automobili[n_auto].find_element_by_class_name("span8")
            prezzo = prezzo.find_element_by_class_name("price")
            prezzo = prezzo.find_element_by_tag_name("header")
            prezzo = prezzo.find_element_by_class_name("totalPrice")
            prezzo = prezzo.find_element_by_tag_name("strong")
            prezzo = prezzo.text
        except NoSuchElementException:
            print("Non ho trovato il link, nome o prezzo per l'auto numero", n_auto)
            continue
        # click per aprire lista optional
        try:
            optional_trovati = False
            optional=""
            while not optional_trovati:
                info_box.find_elements_by_tag_name('p')[1].find_element_by_tag_name('a').click()
                time.sleep(2)
                # div[2]/div[1]/header/p[2]/div/div[2]
                optional = info_box.find_elements_by_tag_name('p')[1].find_element_by_tag_name('div').find_elements_by_tag_name('div')[1].text
                if optional != "Caricamento in corso":
                    optional_trovati = True
                # /html/body/div[1]/div/div[2]/div[4]/div[2]/div[1]/header/p[2]/div/div[2]
                info_box.find_elements_by_tag_name('p')[1].find_element_by_tag_name('a').click()
                time.sleep(2)
        except NoSuchElementException:  # no optional
            optional = ""

        # controllo se aggiornare il db
        nuova_auto = {'nome': nome, 'optional': optional, "prezzo": prezzo, "link": link}
        if ha_optional_giusti(nuova_auto, optional_desiderati.copy()):
            print(n_auto, '- Ho trovato questa auto come la vuoi tu', nuova_auto)
            controlla_novita(nuova_auto, carNum)
    # end while
    return box_auto


def change_page(box_auto):
    try:
        pulsanti_pagina = box_auto.find_elements_by_xpath("/footer/div[2]/ul/il")
        # /html/body/div[1]/div/div[2]/footer/div[2]/ul/il
        pulsanti_pagina[-2].find_element_by_tag_name('a').click()
        print("Ho cambiato pagina")
        time.sleep(2)
        scrool_page()
        return True
    except NoSuchElementException:
        return False


def start_new_search(cars_json):
    global driver
    try:
        with Chrome() as driver:
            driver.get(sito)
            ok = settings()
            if not ok:
                return
            get_new_car(cars_json)
    except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError):
        print("Errore di connessione")
    except Exception:
        if DEBUG:
            raise

#start
if __name__ == '__main__':
    if args.loop is not None and args.loop:
        try:
            time.sleep(int(args.delay))
            while True:
                start_new_search(cars_json)
                time.sleep(60*30)
        except Exception as e:
            with open(stdErrFile, 'a') as error:
                print(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()),e, file=error)
            if DEBUG:
                raise
    else:
        start_new_search(cars_json)
