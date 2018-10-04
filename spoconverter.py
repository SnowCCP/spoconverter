import spotipy
import spotipy.util as util
import configparser
import urllib.request
import urllib.parse
import re
import os

def get_spotify_token():
	config = configparser.ConfigParser()
	config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
	token = util.oauth2.SpotifyClientCredentials(
		config["Credentials"]["client_id"],
		config["Credentials"]["client_secret"])
	return token.get_access_token()
	
def get_playlist_info(token, URI, name):
	user = URI.split(":")[2]
	playlist_id = URI.split(":")[4]
	sp = spotipy.Spotify(token)
	tracks = sp.user_playlist_tracks(user, playlist_id, limit=100, offset=0)
	if name is None:
		name = sp.user_playlist(user, playlist_id, fields="name")["name"]
	return tracks, name
	
def create_dir(directory):
	if directory is not None:
		if not os.path.exists(directory):
			os.makedirs(directory)
		return directory
	else:
		if not os.path.exists(os.path.join(os.path.dirname(__file__), "playlists/")):
			os.makedirs(os.path.join(os.path.dirname(__file__), "playlists/"))
		return os.path.join(os.path.dirname(__file__), "playlists/")

def get_youtube_url(track_name, artist):
	# https://www.codeproject.com/Articles/873060/Python-Search-Youtube-for-Video
	query_string = urllib.parse.urlencode({"search_query": track_name + "-" + artist})
	html_content = urllib.request.urlopen("http://www.youtube.com/results?" + query_string)
	search_results = re.findall(r'href=\"\/watch\?v=(.{11})', html_content.read().decode())
	return "http://www.youtube.com/watch?v=" + search_results[0]
	
def get_track_data(track, youtube=False):
	name = track["name"]
	artist = track['artists'][0]['name']
	dic = {"%name%": name, "%artist%": artist}
	if youtube:
		dic["%yt%"] = get_youtube_url(name, artist)
	return dic
	
def get_tracks_data(tracks, youtube=False):
	tracks_data = []
	for item in tracks['items']:
		tracks_data.append(get_track_data(item['track'], youtube))
	return tracks_data
		
def tracks_to_text(tracks, format=None, youtube=False):
	if format is not None:
		pattern = format
	elif youtube:
		pattern = "%yt%"
	else:
		pattern = "%name% - %artist%"
	tracks_text = []
	for track in tracks:
		text = pattern
		for i, j in track.items():
			text = text.replace(i, j)
		tracks_text.append(text)
	return tracks_text
	
def write_tracks(directory, file_name, tracks, start=None):
	f = open(directory + file_name + ".txt", "w+", encoding="utf-8")
	if start is not None:
		f.write(start + "\n")
	for track in tracks:
		f.write(track + "\n")
	f.close()

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"URI",
		help="URI of the playlist.")
	parser.add_argument(
		"-n", "--name",
		help="name for the output file")
	parser.add_argument(
		"-d", "--directory",
		help="directory to store the output file")
	parser.add_argument(
		"-yt", "--youtube",
		help="parse name and artist to youtube link (pretty slow and blocked when use in bulk)",
		action="store_true")
	parser.add_argument(
		"-s", "--start",
		help="add text at the start of the output file")
	parser.add_argument(
		"-f", "--format",
		help="format of the output track")
	args = parser.parse_args()

	cache_token = get_spotify_token()	
	tracks, file_name = get_playlist_info(cache_token, args.URI, args.name)
	directory = create_dir(args.directory)
	tracks_data = get_tracks_data(tracks, youtube=args.youtube)
	tracks_text = tracks_to_text(tracks_data, format=args.format, youtube=args.youtube)
	write_tracks(directory, file_name, tracks_text, args.start)
