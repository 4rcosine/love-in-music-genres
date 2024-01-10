import sqlite3
import sys
import os
import shutil
from datetime import datetime

class LS_Utils:

	base_url = ""
	token = ""
	app_path = ""
	db_path = ""
	con, cur = None, None
	
	@staticmethod
	def init():
		if getattr(sys, 'frozen', False):
			LS_Utils.app_path = os.path.dirname(sys.executable)
		elif __file__:
			LS_Utils.app_path = os.path.dirname(__file__)

		LS_Utils.base_url = "https://api.spotify.com/v1"
		LS_Utils.db_path = LS_Utils.app_path + "\\resources\\lovesongs.db"
		LS_Utils.con = sqlite3.connect(LS_Utils.db_path)
		LS_Utils.cur = LS_Utils.con.cursor()

	@staticmethod
	def backup_db():
		current_datetime = datetime.now()
		s_datetime = current_datetime.strftime("%Y%m%d_%H%M%S")
		backup_name = "lovesongs_backup_" + s_datetime + ".db"
		shutil.copy2(LS_Utils.db_path,  LS_Utils.app_path + "\\resources\\backups\\" + backup_name)

	@staticmethod
	def reset_db():
		LS_Utils.cur.execute("DELETE FROM songs")
		LS_Utils.cur.execute("UPDATE genres SET top_kw_w2v = NULL, top_kw_tc = NULL, sentiment_zs_w2v = NULL, sentiment_zs_tc = NULL")
		LS_Utils.con.commit()