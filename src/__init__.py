#Ricorda! Stai usando la versione dei Driver per Chrome 83.0.4103.39
import json
import socket
import time

import requests
import urllib3
from selenium.webdriver import Chrome
import telegram_send
import argparse

stdErrFile = r'D:\\Marco\\Universita\\Progetti\\OutletPeugout\\stderr.txt'
sito = "https://webstore.peugeot.it/Cerca-per-categorie?lat=45.0607417&lng=7.528754299999999&LocationL=10098%20Rivoli%20TO%2C%20Italia&etd=0&mbd=1PP2S5P00000;&nbDisMax=20&GrTransmissionType=BVA00006&GrTransmissionTypeL=%20Automatico%20a%208%20Rapporti%20S&S&GrGrade=10000020;10001074&GrGradeL=&dst=100"
optional_desiderati = ['Drive Assist Plus','Sensori di Parcheggio', 'con Visiopark']
cars_json=r'D:\\Marco\\Universita\\Progetti\\OutletPeugout\\src\\cars.json'

parser = argparse.ArgumentParser()
parser.add_argument('--loop',action='store_true' ,help='Indicates if you want script always on')
parser.add_argument('--delay',dest='delay',help='indicates seconds of delay before running the loop')
parser.set_defaults(delay=1)
args = parser.parse_args()

def controlla_novita(nuova_auto):
    manda_tg = False
    if link in list_auto_old:
        if list_auto_old[link] != nuova_auto:
            manda_tg = True
        list_auto_old.pop(link)
    else:
        manda_tg = True
    list_auto_new[link] = nuova_auto
    if manda_tg:
        telegram_send.send(messages=[link])


def settings():
    # SETTINGS
    cookie_button = driver.find_element_by_xpath("/html/body/div[41]/div[4]/div[1]/a[1]")
    if cookie_button is not None:
        cookie_button.click()
    time.sleep(2)
    #scroll the page to load all the cars
    i=0
    while i<5:
        driver.execute_script("window.scrollBy(0,1000)")
        i+=1
        time.sleep(3)

def ha_optional_giusti(nuova_auto: dict, optional_che_vorrei):
    if 'GT Line' in nuova_auto['nome']:
        optional_che_vorrei.pop(1)
    list_bool = map(lambda opt: opt in nuova_auto['optional'], optional_che_vorrei)
    for bool in list_bool:
        if not bool:
            return False
    return True

def get_new_car(cars_json='cars.json'):
    global list_auto_old, list_auto_new, link
    print("Nuova ricerca auto")
    # GET INFO
    box_auto = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]")
    automobili = box_auto.find_elements_by_class_name('result')
    print("Trovate", str(len(automobili)),"auto da analizzare")
    list_auto_old = {}
    list_auto_new = {}
    try:
        with open(cars_json, 'r', encoding='UTF-8') as reader:
            list_auto_old = json.load(reader)
    except FileNotFoundError:
        with open(cars_json, 'x', encoding='UTF-8') as writer:
            writer.write(json.dumps({}))
    # pulsanti_pagina = box_auto.find_element_by_tag_name('footer').find_element_by_class_name('pagination').find_element_by_tag_name('ul').find_elements_by_tag_name('il')
    # altre_pagine = pulsanti_pagina[-1].find_element_by_tag_name('span')
    # prossima_pagina = 1
    # while altre_pagine is not None:
    n_auto = -1
    auto_left = True
    while auto_left or n_auto<len(automobili)-1:
        n_auto += 1
        try:
            info_box = automobili[n_auto].find_elements_by_tag_name('div')[1].find_elements_by_tag_name('div')[0].find_element_by_tag_name('header')
        except Exception as e: #non ci sono più auto
            auto_left = False
            continue
        if info_box is None:
            auto_left = False
            continue
        link = info_box.find_element_by_tag_name('h2').find_element_by_tag_name('a').get_attribute('href')
        nome = info_box.find_element_by_tag_name('h2').find_element_by_tag_name('a').text
        prezzo = automobili[n_auto].find_element_by_class_name("span8")
        prezzo = prezzo.find_element_by_class_name("price")
        prezzo = prezzo.find_element_by_tag_name("header")
        prezzo = prezzo.find_element_by_class_name("totalPrice")
        prezzo = prezzo.find_element_by_tag_name("strong")
        prezzo = prezzo.text
        #/html/body/div[1]/div/div[2]/div[5]
        #/html/body/div[1]/div/div[2]/div[3]/div[2]/div[2]/header/p[3]/strong
        # click per aprire lista optional
        info_box.find_elements_by_tag_name('p')[1].find_element_by_tag_name('a').click()
        time.sleep(2)
        # div[2]/div[1]/header/p[2]/div/div[2]
        optional = info_box.find_elements_by_tag_name('p')[1].find_element_by_tag_name('div').find_elements_by_tag_name('div')[1].text
        #/html/body/div[1]/div/div[2]/div[4]/div[2]/div[1]/header/p[2]/div/div[2]
        info_box.find_elements_by_tag_name('p')[1].find_element_by_tag_name('a').click()
        time.sleep(2)
        # controllo se aggiornare il db
        nuova_auto = {'nome': nome, 'optional': optional,"prezzo":prezzo}
        if ha_optional_giusti(nuova_auto, optional_desiderati.copy()):
            print(n_auto, '- Ho trovato questa auto come la vuoi tu', nuova_auto)
            controlla_novita(nuova_auto)
        # print('prossima pagina')
        # pulsanti_pagina[-2].find_element_by_tag_name('a').click()
        #time.sleep(2)
        # /div/div[2]/footer/div[2]/ul/li[4]/a

    with open(cars_json, 'w', encoding='UTF-8') as writer:
        writer.write(json.dumps(list_auto_new, indent=3))
    print("Fine ricerca")


def start_new_search(cars_json):
    global driver
    try:
        with Chrome() as driver:
            driver.get(sito)
            try:
                settings()
                get_new_car(cars_json)
            except Exception as e:
                with open(stdErrFile) as errFile:
                    print(e, file=errFile)
            # time.sleep(120)
    except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError):
        print("Errore di connessione")

#start
if __name__ == '__main__':
    with open(stdErrFile, 'w') as error:
        print("", file=error)
    if args.loop is not None and args.loop:
        try:
            time.sleep(int(args.delay))
            while True:
                start_new_search(cars_json)
                time.sleep(60*30)
        except Exception as e:
            with open(stdErrFile, 'w') as error:
                print(e, file=error)
            raise
    else:
        start_new_search(cars_json)
