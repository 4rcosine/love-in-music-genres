from lsutils import *
from dsfiller import *
from keir import *
from collections import Counter

class Engine:
	@staticmethod
	def init():
		LS_Utils.init()

	@staticmethod
	def load_songs():
		auth_ok = Spotify.auth_spotify()

		#Playlist IDs (ottenuti manualmente da API Spotify)
		#country love songs: 17WrF3wsE02f0B711n9Dfh
		#metal love songs: 2FoO2XYVPNX0KUsd6NztTT
		#rock love songs: 2dxs5cc0840GGtPNMb9XlR
		#rap love songs: 6boFF7YJUe9c0HT766C13Y
		#soul love songs: 0OdGRoh1ZB8KLzfH4Md4nf
		#pop love songs: 5GFrYhL7hDvT88XVgdthoO
		#blues love songs: 42suJfkKRdIUacrtVbHXnq


		if auth_ok:
			LS_Utils.cur.execute("SELECT count(*) as ct FROM songs")
			ds = LS_Utils.cur.fetchone()

			if ds[0] == 0:
				print("Getting songs")
				#Spotify.get_from_playlist("country", "17WrF3wsE02f0B711n9Dfh")
				#Spotify.get_from_playlist("metal", "2FoO2XYVPNX0KUsd6NztTT")
				#Spotify.get_from_playlist("rock", "2dxs5cc0840GGtPNMb9XlR")
				#Spotify.get_from_playlist("rap", "6boFF7YJUe9c0HT766C13Y")
				#Spotify.get_from_playlist("soul", "0OdGRoh1ZB8KLzfH4Md4nf")
				#Spotify.get_from_playlist("pop", "5GFrYhL7hDvT88XVgdthoO")
				#Spotify.get_from_playlist("blues", "42suJfkKRdIUacrtVbHXnq")

			else:
				print("Dataset is alredy populated. Please, reset the database if you want to retrieve songs from spotify again (check appendix)")

		else:
			print("Auth Failed. Check auth token")

	@staticmethod
	def load_lyrics():
		LS_Utils.cur.execute("SELECT * FROM songs WHERE lyrics = '' or lyrics is null")
		for element in LS_Utils.cur.fetchall():
			song = element[1].lower().strip()
			artist = element[2].lower().strip()

			lyrics = Spotify.get_lyrics(song, artist)
			if lyrics.strip() != "":
				print("Lyric found for " + song + " - " + artist + ". First words are " + lyrics[0:150] + "\n\n")

			else:
				print("Lyric NOT found for " + song + " - " + artist)
			LS_Utils.cur.execute("UPDATE songs SET lyrics = ? WHERE id = ?", [lyrics, element[0]])
			LS_Utils.con.commit()

	@staticmethod
	def load_w2v_keywords():
		LS_Utils.cur.execute("SELECT id, lyrics, title FROM songs WHERE keywords_w2v is null or keywords_w2v = ''")
		dataset = LS_Utils.cur.fetchall()

		W2V.init()
			
		for song in dataset:
			lyrics = song[1]
			words = W2V.get_most_relevant_words("love", lyrics)

			#print(str(song[0]) + " -> " + str(words) + "\n")
			LS_Utils.cur.execute("UPDATE songs SET keywords_w2v = ? WHERE id = ?", [ ';'.join(words), song[0] ] )
			LS_Utils.con.commit()
			print("Keywords for " + song[2] + " inserted!")

	@staticmethod
	def load_born_keywords():
		LS_Utils.cur.execute("SELECT lyrics, genre, title FROM songs ORDER BY id")
		dataset = LS_Utils.cur.fetchall()

		X = [ song[0] for song in dataset ]
		y = [ song[1] for song in dataset ]

		Born.init(X, y)

		#for i in range(0, len(X)):
		for i in range(0, 1):
			kw = Born.get_kw_from_sample(i, X[i], y[i])
			#print(str(kw) + "\n")

		for i in range(0, 1):
			kw = Born.get_kw_from_sample(i, X[i], y[i])
			#print(str(kw) + "\n")

	@staticmethod
	def load_tc_keywords():
		LS_Utils.cur.execute("SELECT lyrics, genre, title, id FROM songs WHERE keywords_tc is null or keywords_tc = '' ORDER BY id")
		dataset = LS_Utils.cur.fetchall()

		
		X = [ song[0] for song in dataset ]
		y = [ song[1] for song in dataset ]

		TC.init(X, y)

		for i in range(0, len(X)):
			kw = TC.get_kw_from_sample(X[i], y[i])
			
			LS_Utils.cur.execute("UPDATE songs SET keywords_tc = ? WHERE id = ?", [ ';'.join(kw), dataset[i][3] ] )
			LS_Utils.con.commit()
			print("Keywords for " + dataset[i][2] + " inserted! -> genre: " + y[i])

	@staticmethod
	def load_genre_kws():

		genres = ["blues", "country", "metal", "pop", "rap", "rock", "soul"]

		documents_w2v = []
		documents_tc = []

		for genre in genres:

			LS_Utils.cur.execute("SELECT id, keywords_w2v, keywords_tc FROM songs WHERE genre = ?", [ genre ])
			dataset = LS_Utils.cur.fetchall()

			keywords_w2v = []
			keywords_tc = []

			for song in dataset:
				keywords_w2v.extend(song[1].split(";"))
				keywords_tc.extend(song[2].split(";"))

			documents_w2v.append(" ".join(keywords_w2v))
			documents_tc.append(" ".join(keywords_tc))

		kws_w2v = Comparer.get_genre_keywords(documents_w2v, genres)
		kws_tc = Comparer.get_genre_keywords(documents_tc, genres)
			
		for i in range(0, len(genres)):
			LS_Utils.cur.execute("UPDATE genres SET top_kw_w2v = ?, top_kw_tc = ? WHERE genre = ?", [ ";".join(kws_w2v[genres[i]]), ";".join(kws_tc[genres[i]]), genres[i] ] )
			LS_Utils.con.commit()
			print("Keywords for " + genres[i] + " inserted!")

	@staticmethod
	def load_song_sentiment():
		ZS.init()
		
		LS_Utils.cur.execute("SELECT lyrics, genre, title, id FROM songs WHERE sentiment_zs = '' or sentiment_zs is null ORDER BY id")
		dataset = LS_Utils.cur.fetchall()

		for song in dataset:

			label = ZS.get_sentiment(song[0])
			LS_Utils.cur.execute("UPDATE songs SET sentiment_zs = ? WHERE id = ?", [ label, song[3] ])
			LS_Utils.con.commit()
			print("Song " + song[2] + " has been classified as " + label)

	@staticmethod
	def load_genre_sentiment():
		ZS.init()

		LS_Utils.cur.execute("SELECT id, top_kw_w2v, top_kw_tc, genre FROM genres")
		dataset = LS_Utils.cur.fetchall()

		for genre in dataset:

			kw_w2v = genre[1].split(";")
			kw_tc = genre[2].split(";")

			kw_w2v.sort()
			kw_tc.sort()

			label_w2v = ZS.get_sentiment(" ".join(kw_w2v))
			label_tc = ZS.get_sentiment(" ".join(kw_tc))

			LS_Utils.cur.execute("UPDATE genres SET sentiment_zs_w2v = ?, sentiment_zs_tc = ? WHERE id = ?", [ label_w2v, label_tc, genre[0] ])
			LS_Utils.con.commit()
			print("Genre " + genre[3] + " has been classified as " + label_w2v + " / " + label_tc + "\n\n")

	@staticmethod
	def compare_genre_keywords():
		#Getting keywords 
		LS_Utils.cur.execute("select genre, top_kw_w2v, top_kw_tc from genres")
		dataset = LS_Utils.cur.fetchall()

		genres = []
		kw_w2v = []
		kw_tc = []

		#Comparing keywords vertically (what are the unique keywords for each genre?)
		for genre in dataset:
			genres.append(genre[0])
			kw_w2v.append(genre[1].split(";"))
			kw_tc.append(genre[2].split(";"))

		guk_w2v = []
		guk_tc = []

		for i in range(0, len(genres)):
			
			cur_k_w2v = kw_w2v[i]
			cur_k_tc = kw_tc[i]

			for j in range(0, len(genres)):
				if i != j:
					cur_k_w2v = [ item for item in cur_k_w2v if item not in kw_w2v[j] ]
					cur_k_tc = [ item for item in cur_k_tc if item not in kw_tc[j] ]

			guk_w2v.append(cur_k_w2v)
			guk_tc.append(cur_k_tc)

		guk_w2v = list(zip(genres, guk_w2v))
		guk_tc = list(zip(genres, guk_tc))

		#Comparing keywords horizontally (w2v VS tc)
		common_words_rateo = []

		for i in range(0, len(genres)):
			
			all_words = set(kw_w2v[i] + kw_tc[i])
			common_words = set(kw_w2v[i]).intersection(kw_tc[i])
			common_words_rateo.append(len(common_words) / len(all_words))

		cwr_genres = list(zip(genres, common_words_rateo))

		#print(cwr_genres)

		return guk_w2v, guk_tc, cwr_genres

	@staticmethod
	def compare_sentiments():
		#Getting genre sentiment from the occurrency song sentiments
		LS_Utils.cur.execute("select sentiment_zs, genre, max(vc) from (select count(*) as vc, sentiment_zs, genre from songs group by sentiment_zs, genre order by genre) group by genre")
		dataset = LS_Utils.cur.fetchall()

		sentiments = dict()
		report = dict()

		for genre in dataset:
			sentiments[genre[1]] = list()
			sentiments[genre[1]].append(genre[0])

		#Getting genre sentiment from thw w2v and tc keywords
		LS_Utils.cur.execute("select * from genres")
		dataset = LS_Utils.cur.fetchall()

		for genre in dataset:
			sentiments[genre[1]].append(genre[4])
			sentiments[genre[1]].append(genre[5])


		num_genres = len(sentiments)

		report["w2v_vs_tc"] = sum([ (1 if sentiments[x][1] == sentiments[x][2] else 0) for x in sentiments ]) / num_genres
		report["songs_vs_w2v"] = sum([ (1 if sentiments[x][0] == sentiments[x][1] else 0) for x in sentiments ]) / num_genres
		report["songs_vs_tc"] = sum([ (1 if sentiments[x][0] == sentiments[x][2] else 0) for x in sentiments ]) / num_genres
		report["total"] = sum([ (1 if sentiments[x][0] == sentiments[x][1] and sentiments[x][1] == sentiments[x][2] else 0) for x in sentiments ]) / num_genres

		#print(report)
		return sentiments, report

	@staticmethod
	def reset_database():
		ch = input("You really want to erase all the database content? (type 'y' to confirm): ")

		if ch == "y":
			LS_Utils.backup_db()
			LS_Utils.reset_db()
			print("Database resetted successfully!")

		else:
			print("Nothing happened!")