# -*- coding: utf-8 -*-
"""
Created on Thu Jul 26 10:17:31 2018

@author: bradamante
"""

import psycopg2
import os


class DBHelper:
	# due cosette da mettere a posto in futuro: capire perche non funzionano i %s e le funzioni interne (problema di ignoranza tempo indefinito)
	def __init__(self, dbname="todo.sqlite"):
		self.DATABASE_URL = os.environ['DATABASE_URL']
		self.conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')


	def setup(self):
		# se non c'è mi crea la mia bella tabellina con utente, libro, autore, il link a wiki e il testo markdown
		print("creating table")
		stm = "CREATE TABLE IF NOT EXISTS items (owner text, titolo text, autore text, link text, telegram text)"
		cur = self.conn.cursor()
		cur.execute(stm)
		cur.close()
		self.conn.commit()
		stm ="CREATE INDEX IF NOT EXISTS itemIndex ON items (titolo ASC)"
		cur = self.conn.cursor()
		cur.execute(stm)
		cur.close()
		self.conn.commit()
		stm = "CREATE INDEX IF NOT EXISTS ownIndex ON items (owner ASC)"
		cur = self.conn.cursor()
		cur.execute(stm)
		cur.close()
		self.conn.commit()


	def add_item(self, owner, titolo, autore, link,telegram):
		stm = "INSERT INTO items (owner,titolo, autore, link, telegram) VALUES ($$"+str(owner)+"$$,$$"+titolo+"$$,$$"+autore+"$$,$$"+link+"$$,$$"+telegram+"$$)"
		cur = self.conn.cursor()
		cur.execute(stm)
		cur.close()
		self.conn.commit()

	def delete_item(self, titolo, owner):
		stm = "DELETE FROM items WHERE titolo = $$"+titolo + "$$ AND owner = $$"+str(owner)+"$$"
		cur = self.conn.cursor()
		cur.execute(stm)
		cur.close()
		self.conn.commit()

	def get_titoli(self, owner):
		stmt = "SELECT titolo FROM items WHERE owner =$$"+str(owner)+"$$"
		cur = self.conn.cursor()
		cur.execute(stmt)
		row = cur.fetchall()
		cur.close()
		return [x[0] for x in row]

	def get_autore_titolo(self,owner):
		stmt = "SELECT autore, titolo FROM items WHERE  owner =$$"+str(owner)+"$$"
		cur = self.conn.cursor()
		cur.execute(stmt)
		row = cur.fetchall()
		cur.close()
		return row


	def get_message(self, owner):
		# ritorna il markdown
		stmt = "SELECT telegram FROM items WHERE owner =$$"+str(owner)+"$$"
		cur = self.conn.cursor()
		cur.execute(stmt)
		row = cur.fetchall()
		cur.close()
		return [x[0] for x in row]
