import requests
import json
from lsutils import *
import random
import re
import urllib
from bs4 import BeautifulSoup

class Spotify:

	
	@staticmethod
	def auth_spotify():
		client = requests.Session()
		header = { "Content-Type" : "application/x-www-form-urlencoded"}
		response = client.post("https://accounts.spotify.com/api/token?grant_type=client_credentials&client_id=9aec8a4580a24f0681ba03f4ef149029&client_secret=72533dd2ce5b4394b65fbd894d3d90b2", headers=header)
		content = response.text

		#print("Res: " + content)
		if response.status_code == 200:
			jres = json.loads(content)
			LS_Utils.token = jres["access_token"]
			return True

		else:
			return False

	@staticmethod
	def get_from_playlist(genre, playlist_id):
		print("Getting songs from playlist. Genre: " + genre)
		header = { "Authorization" : "Bearer " + LS_Utils.token}
		client = requests.Session()

		song_list = []
		#Taking the frist two pages of 100 songs
		for i in range (0, 3):
			offset = i * 100
			full_url = LS_Utils.base_url + "/playlists/" + playlist_id + "/tracks?offset=" + str(offset) + "&limit=100"
			response = client.get(full_url, headers=header)
			if response.status_code == 200:
				jres = json.loads(response.text)
				songs = jres["items"]

				for song in songs:
					name = song["track"]["name"]
					artist = song["track"]["artists"][0]["name"]
					song_list.append(name + "§" + artist)
				
		if len(song_list) > 0:
			#Shuffling songs (so we probably won't get two songs from the same artist)
			random.shuffle(song_list)

			#Adding the first 100 songs into the db
			added = 0
			i = 0
			while added < 100:
				song_data = song_list[i].split("§")

				#Cleaning the title
				title = song_data[0].lower()
				title = re.sub("\\bremaster\\b|\bremix\\b|\\bremaster\\b|\\bremastered\\b|\\bremixed\\b|\\d{4}", "", title)
				title = re.sub("\\b\\s+\\b", " ", title)
				title = re.sub("\\((.*?)\\)", "", title)
				title = title.replace("-", "").replace("  ", " ")

				LS_Utils.cur.execute("SELECT * FROM songs WHERE title = ? and artist = ?", [title, song_data[1]])
				trovati = LS_Utils.cur.fetchall()

				if len(trovati) == 0 and "live" not in title and title.strip() != "":

					lyrics = Lyrics.get_lyrics(title.lower().strip(), song_data[1].lower().strip())

					if lyrics != "" :
						LS_Utils.cur.execute("INSERT INTO songs (title, artist, genre, lyrics) VALUES (?, ?, ?, ?)", [title, song_data[1], genre, lyrics])
						LS_Utils.con.commit()
						#print(title + " - " + song_data[1] + " inserted!")
						added += 1

				i += 1	

		else:
			print("Error 1 loading songs from spotify")
			print(response.content)

		print("\r\n")


class Lyrics:
	@staticmethod
	def get_lyrics(song, artist):
		title = song + " " + artist
		#1 Searching for the song
		x = requests.get("http://api.genius.com/search?q=" + urllib.parse.quote(title), headers={"Authorization" : "Bearer epFEa7cyyaflPeIO0YWND29W2_t6hWcE15iHjFIbM1h4-g6HYWRo-XRAl324Osa7"})
		j_res = json.loads(x.text)
		lyrics = ""
	
		#Getting the most significative word in the artist name
		art_kws = re.sub(r'[^\w]', ' ', artist).split(" ")
		ak = max(art_kws, key = len).lower()
			
		i = 0
		idx = None
		if len(j_res["response"]["hits"]) > 0:
			tmp_artist = j_res["response"]["hits"][i]["result"]["artist_names"].lower()
			while idx == None and i < len(j_res["response"]["hits"]):
				
				#Filtering the api results
				if "genius" not in tmp_artist and ak in tmp_artist.lower():
					idx = i
				else:
					tmp_artist = j_res["response"]["hits"][i]["result"]["artist_names"].lower()
					i += 1
	
		if idx != None:
			path = "https://genius.com" + j_res["response"]["hits"][i]["result"]["path"]

			#3 GET request to the song resource
			y = requests.get(path)

			#4 Parsing the response
			soup = BeautifulSoup(y.text)

			#5 Retrieving the lyrics
			ee = soup.find_all("div", {"data-lyrics-container" : "true"})

			lyrics = ""
			for x in ee:
				x = BeautifulSoup(str(x).replace("<br/>", " "), 'html.parser');
				lyrics += re.sub("\[.*?\]", "", x.text)

		return lyrics

	