# -*- coding: utf-8 -*-
"""
Created on Thu Jul 26 10:52:31 2018

@author: bradamante
"""


from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from SPARQLWrapper import SPARQLWrapper, JSON
from dbhelper import DBHelper

# da fare: la tastiera inline non vuole callback_data più lunghe di 64 -> creare una tabella con l'isbn per esempio (3 orette)
class libro:
	#più che altro per passare i dati tra le funzioni
	def __init__(self):
		self.telegram = "Non trovato"
		self.titolo = ""
		self.link = ""
		self.autore = ""
	def crea_telegram(self):
		self.telegram ="["+self.titolo+"]("+self.link.replace(")","%29")+")"
	def add_link(self, link):
		self.link=link
	def add_titolo(self, titolo):
		self.titolo=titolo
	def add_autore(self, autore):
		self.autore =autore

db = DBHelper()

TOKEN ="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

def Cerca_titolo(titolo):
	# qui arriva il titolo secco e ritorna un "libro"
	titolo=titolo.strip()
	risp=libro()
	sparql = SPARQLWrapper("http://it.dbpedia.org/sparql")
	#l'union serve per  libri che non hanno l'autore in catalogo
	# l'order by mi mette sopra il record con l'autore valorizzato se c'è
	q = """
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	SELECT DISTINCT ?book, ?autore WHERE{
	{{?book a <http://dbpedia.org/ontology/Book> } UNION{
	?book <http://it.dbpedia.org/property/autore> ?uso.
	?uso rdfs:label ?autore}}.
	?book <http://it.dbpedia.org/property/titolo> '''"""+titolo+"""'''@it }
	ORDER BY desc(?autore)"""
	sparql.setQuery(q)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	if  (len(results["results"]["bindings"]))>0:
		leng = len("http://it.dbpedia.org/resource/")
		dbpedia = results["results"]["bindings"][0]["book"]["value"]
		tit = titolo
		aut=""
		#controllo che si sia il campo autore, non sempre lo ho, vedi union sopra
		if(len(results["results"]["bindings"][0])>1):
			aut = results["results"]["bindings"][0]["autore"]["value"]
		risp.add_titolo(tit)
		risp.add_link("https://it.wikipedia.org/wiki/" + dbpedia[leng:])
		# vabbè non è il massimo ma per il 95% delle volte funziona
		risp.add_autore(aut)
		risp.crea_telegram()
	return risp


def Cerca_libro(titolo):
	#qui arriva una parte del titolo e ne ritorna una serie di completi
	titolo =titolo.strip()
	sparql = SPARQLWrapper("http://it.dbpedia.org/sparql")
	q = """
	SELECT DISTINCT ?book, ?titolo WHERE {
	?book a<http://dbpedia.org/ontology/Book> .
	?book <http://it.dbpedia.org/property/titolo> ?titolo
	FILTER regex(?titolo, '''"""+titolo+"""''', "i")
	}
	ORDER BY RAND()
	LIMIT 10"""
	sparql.setQuery(q)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	lista_titoli=[]
	if (len(results["results"]["bindings"]))>0:
		for result in results["results"]["bindings"]:
			tit = result["titolo"]["value"]
			lista_titoli.append(tit)
	return lista_titoli

def Cerca_autore(autore):
	#anche qua nulla di magico, arriva una parte di nome e ritorna una lista di nomi completi
	autore= autore.strip()
	sparql = SPARQLWrapper("http://it.dbpedia.org/sparql")
	q = """
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	SELECT DISTINCT ?autore WHERE {
	?book a <http://dbpedia.org/ontology/Book> .
	?book <http://it.dbpedia.org/property/autore> ?uso.
	?uso rdfs:label ?autore
	FILTER regex(?autore, '''"""+autore+"""''', "i")
	}
	ORDER BY RAND()
	LIMIT 10"""
	sparql.setQuery(q)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	lista_autori=[]
	if (len(results["results"]["bindings"]))>0:
		for result in results["results"]["bindings"]:
			tit = result["autore"]["value"]
			lista_autori.append(tit)
	return lista_autori

def Cerca_libro_autore(autore):
	#arriva un nome autore completo e ritorna una lista di suoi libri
	autore=autore.strip()
	sparql = SPARQLWrapper("http://it.dbpedia.org/sparql")
	q = """
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	SELECT DISTINCT ?book, ?titolo WHERE {
	?book a<http://dbpedia.org/ontology/Book> .
	?book <http://it.dbpedia.org/property/titolo> ?titolo.
	?book <http://it.dbpedia.org/property/autore>  ?autore.
	?autore rdfs:label '''"""+autore+"""'''@it
	}
	ORDER BY RAND()
	LIMIT 10"""
	sparql.setQuery(q)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	lista_titoli=[]
	if (len(results["results"]["bindings"]))>0:
		for result in results["results"]["bindings"]:
			tit = result["titolo"]["value"]
			lista_titoli.append(tit)
	return lista_titoli

def Cerca_genere(bot, update, genere_in):
	# invia un messaggio e relativa tastiera con i libri di un genere
	chat = update.message.chat_id
	genere = genere_in.strip()
	if (genere.find("orror")!=-1):
		#serve per unificare il genere orrore a Horror
		genere="orror"
	sparql = SPARQLWrapper("http://it.dbpedia.org/sparql")
	q = """
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	SELECT DISTINCT ?book, ?titolo WHERE {
	?book a<http://dbpedia.org/ontology/Book> .
	?book <http://it.dbpedia.org/property/titolo> ?titolo.
	?book <http://it.dbpedia.org/property/tipo>  ?tipo.
	FILTER regex(?tipo, '''"""+genere+"""''', "i")
	}
	ORDER BY RAND()
	LIMIT 10"""
	sparql.setQuery(q)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	if (len(results["results"]["bindings"]))>0:
		keyboard=[]
		for result in results["results"]["bindings"]:
			tit = result["titolo"]["value"]
			if (len(tit)<60):
				#la tastiera inline non vuole callback_data più lunghe di 64
				keyboard.append([InlineKeyboardButton(tit, callback_data=tit)])
		message = "scegli il titolo"
		reply_markup = InlineKeyboardMarkup(keyboard)
		update.message.reply_text(message, reply_markup=reply_markup)
	else:
		message = genere_in + " non trovato"
		update.message.reply_text(message)

def Testo(bot, update):
	#serve per unificare tasti e messaggi scritti a mano
	text = update.message.text
	Testo_glob(bot, update, text)

def Testo_glob(bot, update, text):
	#qui arrivano i testi senza funzioni: titoli o porzioni di titoli
	chat = update.message.chat_id
	#si carica tutti i titoli di quella chat in una lista
	items = db.get_titoli(chat)
	if text in items:
		#se lo trova lo elimina e propone gli altri da eliminare
		db.delete_item(text, chat)
		items = db.get_titoli(chat)
		if (len(items)>0):
			keyboard=[]
			for item in items:
				if (len(item)<60):
					# 60 caratteri del callback_data
					keyboard.append([InlineKeyboardButton(item, callback_data=item)])
			reply_markup = InlineKeyboardMarkup(keyboard)
			message = text + " eliminato \n Seleziona il prossimo libro da eliminare"
			update.message.reply_text(message , reply_markup=reply_markup)
		else:
			message = text + " eliminato"
			update.message.reply_text(message)
	else:
		#se non ce l'ho cerca il titolo secco
		libri=Cerca_titolo(text)
		if (libri.telegram !='Non trovato'):
			# se lo trova spara fuori il link a wikipedia
			db.add_item(chat, libri.titolo, libri.autore, libri.link, libri.telegram)
			update.message.reply_markdown(libri.telegram)
		else:
			#se non lo trova lo tratta come titolo parziale
			titoli = Cerca_libro(text)
			if (len(titoli)>0):
				#trovato qualcosa
				message = "scegli il titolo"
				keyboard=[]
				for titolo in titoli:
					if (len(titolo)<60):
						#solito discorso dei 64 caratteri
						keyboard.append([InlineKeyboardButton(titolo, callback_data=titolo)])
				reply_markup = InlineKeyboardMarkup(keyboard)
				update.message.reply_text(message, reply_markup=reply_markup)

			else:
				message = "Non ho trovato nulla"
				update.message.reply_text(message)

def Start(bot, update):
	#si comincia così, la tastiera è sempre visibile se no la Marta si lamenta
	keyboard= [
	["/lista", "/wiki","/genere"],
	["/cancella","/aiuto"]
	]
	reply_markup = ReplyKeyboardMarkup(keyboard)
	update.message.reply_text("lista dei libri!",reply_markup=reply_markup)

def Aiuto(bot, update):
	update.message.reply_text("""scrivi un titolo o parte di esso per aggiungerlo
	riscrivi il titolo o /cancella per eliminare i vari elementi
	scrivi /lista per avere la lista semplice dei libri inseriti
	scrivi /wiki per avere la lista con i link dei libri inseriti
	scrivi /autore e un autore per libri di quell'autore
	e /genere per scegliere un genere tra quelli proposti.
	Per ora non sono gestiti i titoli più lunghi di 60 caratteri""")

def Lista(bot, update):
	# da una lista senza link ma se c'è mette l'autore
	items = db.get_autore_titolo(update.message.chat_id)
	if (len(items)>0):
		for item in items:
			update.message.reply_text(item[1]+" - "+item[0])
	else:
		message = "La lista è vuota"
		update.message.reply_text(message)

def Wiki(bot, update):
	#semplice semplice ritorna il markdown
	items = db.get_message(update.message.chat_id)
	if (len(items)>0):
		for item in items:
			update.message.reply_markdown(item)
	else:
		message = "Non ho libri in lista"
		update.message.reply_text(message)

def Cancella(bot, update):
	#lui non fa altro che proporre una tastiera con la lista di libri
	#cliccando sopra a uno è come riscrivere un titolo
	items = db.get_titoli(update.message.chat_id)
	if (len(items)>0):
		message = "Seleziona il libro da eliminare"
		keyboard=[]
		for item in items:
			if (len(item)<60):
				keyboard.append([InlineKeyboardButton(item, callback_data=item)])
		reply_markup = InlineKeyboardMarkup(keyboard)
		update.message.reply_text(message , reply_markup=reply_markup)
	else:
		message = "Non ho libri da eliminare"
		update.message.reply_text(message)

def Autore_secco(bot, update, autore):
	#chiamato in due casi: uso la tastiera per scegliere un autore tra quelli proposti
	#                      trovo solo un autore che contiene la stringa inserita
	print(autore)
	titoli = Cerca_libro_autore(autore)
	print(titoli)
	if (len(titoli)>0):
		update.message.reply_text(autore)
		message = "Seleziona un libro"
		keyboard=[]
		for titolo in titoli:
			if (len(titolo)<60):
				keyboard.append([InlineKeyboardButton(titolo, callback_data=titolo)])
		reply_markup = InlineKeyboardMarkup(keyboard)
		update.message.reply_text(message, reply_markup=reply_markup)
	else:
		message = "Non libri per questo autore"
		update.message.reply_text(message)


def Autore(bot, update, args):
	# ritorna o una lista di autori oppure di libri se ne trova solo uno
	#inizializzo autore perchè se non passo args si spacca tutto poi
	autore=""
	#ricreo le stringhe spezzate da telegram
	for parola in args:
		autore = autore + " " + parola
	if (len(autore)>0):
		#cerca autori con quel nome
		autori=Cerca_autore(autore)
		if (len(autori)==1):
			#se ne trova uno cerca i libri di quell'autore
			Autore_secco(bot,update,autori[0])
		elif (len(autori)>0):
			#altrimenti propone una serie di nomi e praticamente ritorna a chiamre questa funzione
			message = "scegli l'autore"
			autori_send=[]
			for autore_uso in autori:
				autori_send.append([InlineKeyboardButton(autore_uso, callback_data="/autore "+autore_uso)])
			reply_markup = InlineKeyboardMarkup(autori_send)
			update.message.reply_text(message, reply_markup=reply_markup)
		else:
			message = "Non ho trovato nulla"
			update.message.reply_text(message)
	else:
		message = "Inserisci il nome di un autore dopo /autore"
		update.message.reply_text(message)

def Genere(bot, update, args):
	# se scrivo il genere cerco con quel genere se no li propongo io
	#inizializzo genere perchè se non passo args si spacca tutto poi
	genere =""
	for parola in args:
		genere = genere + " " + parola
	if (len(genere)>0):
		Cerca_genere(bot, update, genere)
	else:
		message = "Seleziona il genere"
		keyboard=[[InlineKeyboardButton("Giallo", callback_data="/genere Giallo"),InlineKeyboardButton("Per ragazzi", callback_data="/genere Per ragazzi")],
		[InlineKeyboardButton("Fantascienza", callback_data="/genere Fantascienza"),InlineKeyboardButton("Fantasy", callback_data="/genere Fantasy")],
		[InlineKeyboardButton("Thriller", callback_data="/genere Thriller"),InlineKeyboardButton("Horror", callback_data="/genere Horror")],
		[InlineKeyboardButton("Romanzo", callback_data="/genere Romanzo"),InlineKeyboardButton("Umoristico", callback_data="/genere Umoristico")],
		[InlineKeyboardButton("Rosa", callback_data="/genere Rosa"),InlineKeyboardButton("Saggio", callback_data="/genere Saggio")]
		]
		reply_markup = InlineKeyboardMarkup(keyboard)
		update.message.reply_text(message , reply_markup=reply_markup)


def Button(bot, update):
	#gestisco le tastiere inline
	text = update.callback_query.data
	if text.startswith("/autore"):
		Autore_secco(bot, update.callback_query, text[7:])
	elif text.startswith("/genere"):
		Cerca_genere(bot, update.callback_query, text[7:])
	else:
		Testo_glob(bot, update.callback_query, text)




def main():
	db.setup()
	updater = Updater(TOKEN)
	dp = updater.dispatcher
	#gestisco i comandi /qualcosa CommandHandler("comandoRicevuto",funzioneDaLanciare,possibileArgomento)
	dp.add_handler(CommandHandler("start", Start))
	dp.add_handler(CommandHandler("lista", Lista))
	dp.add_handler(CommandHandler("wiki", Wiki))
	dp.add_handler(CommandHandler("cancella", Cancella))
	dp.add_handler(CommandHandler("aiuto", Aiuto))
	dp.add_handler(CommandHandler("genere", Genere, pass_args=True))
	dp.add_handler(CommandHandler("autore", Autore, pass_args=True))
	#gestisco le tastiere inline
	dp.add_handler(CallbackQueryHandler(Button))
	#gestisco il testo secco
	dp.add_handler(MessageHandler(Filters.text, Testo))
	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		exit()
