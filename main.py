import datetime
import requests
import telebot
import time
import json
import csv
from config import Config
from logger import setup_logger

class WebScraper:
    def __init__(self):
        self.logger = setup_logger()
        self.game = "Blaze Double"
        self.token = Config.TOKEN
        self.chat_id = Config.CHAT_ID
        self.url_API = Config.URL_API
        self.protection = Config.PROTECTION
        self.gales = Config.GALES
        self.bot = telebot.TeleBot(token=self.token, parse_mode="MARKDOWN", disable_web_page_preview=True)
        self.date_now = str(datetime.datetime.now().strftime("%d/%m/%Y"))
        self.check_date = self.date_now
        self.results_history = []
        self.win_results = 0
        self.loss_results = 0
        self.branco_results = 0
        self.max_hate = 0
        self.win_hate = 0
        self.count = 0
        self.analyze = True
        self.direction_color = "None"
        self.message_delete = False
        self.message_ids = []
        self.link = '[Clique aqui!](https://blaze-codigo.com/r/GlVKOG)'
        

    def start(self):
        check = []
        while True:
            try:
                self.date_now = str(datetime.datetime.now().strftime("%d/%m/%Y"))
                results = []
                time.sleep(1)
                response = requests.get(self.url_API, timeout=15)
                response.raise_for_status()
                json_data = json.loads(response.text)
                for i in json_data:
                    results.append(i['roll'])
                if check != results:
                    check = results
                    self.process_results(results)
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request exception: {e}")
                time.sleep(60)
            except Exception as e:
                self.logger.error(f"General error: {e}")

    def process_results(self, results):
        finalnum = results
        finalcor = []
        for i in results:
            if 1 <= i <= 7:
                finalcor.append("V")
            elif 8 <= i <= 14:
                finalcor.append("P")
            else:
                finalcor.append("B")

        self.logger.info(f"Últimos 10 números: {finalnum[0:10]}")
        self.logger.info(f"Últimas 10 cores: {finalcor[0:10]}")

        if not self.analyze:
            self.check_results(finalcor[0])
            return

        self.check_signal(finalcor)

    def check_signal(self, finalcor):
        with open(Config.CSV_PATH, newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                string = str(row[0])
                split_string = string.split("=")
                lista = split_string[0].split("-")
                aposta = list(split_string[1])
                count = 0
                sinal = True
                estrategias = lista[::-1]
                for i in estrategias:
                    if i == "X" or i == finalcor[count]:
                        pass
                    else:
                        sinal = False
                    count += 1
                if sinal:
                    self.logger.info(f"Sinal encontrado {estrategias}, {aposta[0]}")
                    self.send_signal(aposta[0])
                    return

    def send_signal(self, direction):
        self.direction_color = {
            'P': '⚫️',
            'V': '🔴',
            'B': '⚪️'
        }.get(direction, '⚫️')
        
        retries = 3
        for attempt in range(retries):
            try:
                self.bot.send_message(chat_id=self.chat_id, text=f"""
🎲 *ENTRADA CONFIRMADA!*
🎰 Apostar no {self.direction_color}
📱 *{self.game}*
🔗jogue aqui {self.link}
                """)
                self.analyze = False
                break  # Se a mensagem for enviada com sucesso, sair do loop
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Attempt {attempt + 1} - Request exception: {e}")
                time.sleep(5)  # Esperar um pouco antes de tentar novamente

    def check_results(self, result):
        if result == "B" and self.protection:
            self.martingale("BRANCO")
        elif result == "B" and not self.protection:
            self.martingale("PERDA")
        elif result != "B" and self.direction_color == "⚪️":
            self.martingale("PERDA")
        elif result == "V" and self.direction_color == "🔴":
            self.martingale("WIN")
        elif result == "V" and self.direction_color == "⚫️":
            self.martingale("PERDA")
        elif result == "P" and self.direction_color == "⚫️":
            self.martingale("WIN")
        elif result == "P" and self.direction_color == "🔴":
            self.martingale("PERDA")

    def martingale(self, result):
        if result == "WIN":
            self.logger.info("WIN")
            self.win_results += 1
            self.max_hate += 1
            self.send_message("✅✅✅ VITORIA! ✅✅✅")
        elif result == "PERDA":
            self.count += 1
            if self.count > self.gales:
                self.logger.info("PERDA")
                self.loss_results += 1
                self.max_hate = 0
                self.send_message("🚫🚫🚫 NÃO FOI DESTA VEZ🚫🚫🚫")
            else:
                self.logger.info(f"Vamos para o {self.count}ª gale!")
                self.alert_gale()
                return
        elif result == "BRANCO":
            self.logger.info("BRANCO")
            self.branco_results += 1
            self.max_hate += 1
            self.send_message("✅✅✅ BRANCO ✅✅✅")

        self.count = 0
        self.analyze = True
        self.show_results()
        self.restart()

    def alert_gale(self):
        self.message_ids = self.bot.send_message(self.chat_id, text=f"⚠️ Vamos para o {self.count}ª GALE").message_id
        self.message_delete = True

    def send_message(self, text):
        retries = 3
        for attempt in range(retries):
            try:
                self.bot.send_message(chat_id=self.chat_id, text=text)
                break
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Attempt {attempt + 1} - Request exception: {e}")
                time.sleep(15)

    def show_results(self):
        total_results = self.win_results + self.branco_results + self.loss_results
        if total_results != 0:
            win_percentage = 100 / total_results * (self.win_results + self.branco_results)
            branco_percentage = 100 / total_results * self.branco_results
        else:
            win_percentage = 0
            branco_percentage = 0
        self.win_hate = f"{win_percentage:,.2f}%"
        self.branco_hate = f"{branco_percentage:,.2f}%"
        self.bot.send_message(chat_id=self.chat_id, text=f"""
► PLACAR = ✅ {self.win_results} | ⚪️ {self.branco_results} | 🚫 {self.loss_results} 
► Consecutivas = {self.max_hate}
► Assertividade = {self.win_hate}
► Assertividade no Branco = {self.branco_hate}
 """)
        self.results_history.append({
            'date': datetime.datetime.now(),
            'win': self.win_results,
            'loss': self.loss_results,
            'branco': self.branco_results,
        })

    def restart(self):
        if self.date_now != self.check_date:
            self.logger.info("Reiniciando bot!")
            self.check_date = self.date_now
            self.bot.send_sticker(
                self.chat_id,
                sticker="CAACAgEAAxkBAAEBbJJjXNcB92-_4vp2v0B3Plp9FONrDwACvgEAAsFWwUVjxQN4wmmSBCoE",
            )
            self.show_results()
            self.win_results = 0
            self.loss_results = 0
            self.branco_results = 0
            self.max_hate = 0
            self.win_hate = 0
            self.branco_hate = 0
            time.sleep(10)
            self.bot.send_sticker(
                self.chat_id,
                sticker="CAACAgEAAxkBAAEBPQZi-ziImRgbjqbDkPduogMKzv0zFgACbAQAAl4ByUUIjW-sdJsr6CkE",
            )
            self.show_results()

if __name__ == "__main__":
    scraper = WebScraper()
    scraper.start()
