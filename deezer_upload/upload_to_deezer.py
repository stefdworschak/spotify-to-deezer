import argparse
import json
import logging
import os
import sys
import re
import http.client
import http.server
import urllib.error
import urllib.parse
import urllib.request
import requests
import webbrowser
import time

import secrets

## CHANGE THESE VALUES
APPID = os.environ.get('DEEZER_CLIENT_ID', 'Env not set')
SECRET = os.environ.get('DEEZER_CLIENT_SECRET', 'Env not set')
USER_ID = os.environ.get('DEEZER_USER_ID', 'Env not set')
FILENAME = 'new_playlists.txt'

logger = logging.getLogger('error_log')
fh = logging.FileHandler('error_log.log')
fh.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)


## DO NOT CHANGE ANYTHING BELOW HERE
PORT=23412
_PLAYLIST_IMPORT = "Playlists to import"
playlist_names = []
selected_playlists = set()
deezer_playlists = []
longest_playlistcount = -1
jsoncont = {}
listitems = []
shouldparse = False
token = ""

## Authorize code
def authorize():
	existing_token = read_token()
	if existing_token:
		global token, shouldparse
		shouldparse = True
		token = existing_token
		return
	webbrowser.open('https://connect.deezer.com/oauth/auth.php?' + urllib.parse.urlencode({
		'app_id': APPID,
		'redirect_uri': 'http://127.0.0.1:{}/authfinish'.format(PORT),
		'perms': 'basic_access,manage_library,offline_access'
	}))

	# Start a simple, local HTTP server to listen for the authorization token... (i.e. a hack).
	server = _AuthorizationServer('127.0.0.1', PORT)
	try:
		while True:
			server.handle_request()
	except _Authorization as auth:
		get_actual_token(auth.access_token)

class _AuthorizationServer(http.server.HTTPServer):
	def __init__(self, host, port):
		http.server.HTTPServer.__init__(self, (host, port), _AuthorizationHandler)

	# Disable the default error handling.
	def handle_error(self, request, client_address):
		raise

class _AuthorizationHandler(http.server.BaseHTTPRequestHandler):
	def do_GET(self):
		# Read access_token and use an exception to kill the server listening...
		if self.path.startswith('/authfinish?'):
			self.send_response(200)
			self.send_header('Content-Type', 'text/html')
			self.end_headers()
			self.wfile.write(b'<script>close()</script>Thanks! You may now close this window.')
			raise _Authorization(re.search('code=([^&]*)', self.path).group(1))

		else:
			self.send_error(404)

	# Disable the default logging.
	def log_message(self, format, *args):
		pass

class _Authorization(Exception):
	def __init__(self, access_token):
		self.access_token = access_token

# the other one is actually a "code", so now get the real token
def get_actual_token(code):
	global token, shouldparse
	f = urllib.request.urlopen("https://connect.deezer.com/oauth/access_token.php?app_id="+APPID+"&secret="+SECRET+"&code="+code)
	fstr = f.read().decode('utf-8')

	if len(fstr.split('&')) != 2:
		return

	stri = fstr.split('&')[0].split('=')[1]
	token = stri
	with open('token.txt', 'w+') as f:
		f.write(stri)
	shouldparse = True
	return
	#raise Exception

def read_token():
	try:
		with open('token.txt', 'r') as f:
			token = f.read()
			f.close()
		return token
	except FileNotFoundError:
		return None

'''
	Add a playlist to Deezer with name
	return playlist ID
'''
def add_playlist(name):
	params = urllib.parse.urlencode({'title':name}).encode('UTF-8')
	url = 'https://api.deezer.com/user/me/playlists?access_token='+token
	f = urllib.request.urlopen(url, data=params)
	fstr = f.read().decode('utf-8')
	js = json.loads(fstr)
	if 'id' not in js:
		return -1
	else:
		return js['id']

'''
	Search a track on Deezer by ISRC number
	return Deezer ID of track
'''
def search_track(track):
	try:
		id_ = track['track']['external_ids']['isrc']
		url = 'https://api.deezer.com/track/isrc:'+id_+'?access_token='+token
		f = urllib.request.urlopen(url)
		fstr = f.read().decode('utf-8')
		js = json.loads(fstr)
		if 'error' in js:
			name_ = track['track']['name']
			artist_ = track['track']['artists'][0]['name']
			backup_track = backup_search(name_, artist_)
			if backup_track:
				print("+ ID not foung, but found backup track with name and artist")
				return backup_track[0]['id']
			return -1
		else:
			return js['id']
	except:
		return -1

def backup_search(name, artist):
	searchstring = f'artist:"{artist}" track:"{name}"'
	params = urllib.parse.quote_plus(searchstring)
	url = f'https://api.deezer.com/search?q={params}'
	backup_tracks = retrieve_deezer_data(url)
	return backup_tracks

'''
	Get the user's Deezer playlists to prevent double entries. Will recusively fetch more, as they are limited to about 35 lists per call.
	return titles of existing playlists (yadda, yadda, string compare, I know...)
'''
def get_deezer_playlists(next):
	url = ''
	existing = []
	if next == -1:
		url = 'https://api.deezer.com/user/me/playlists?access_token='+token

	else:
		url = next
	f = urllib.request.urlopen(url)
	fstr = f.read().decode('utf-8')
	js = json.loads(fstr)
	if 'data' not in js:
		return -1
	else:
		existing = []
		for d in js['data']:
			existing.append(d['title'])
		if 'next' in js:
			existing.extend(get_deezer_playlists(js['next']+'?access_token='+token))
		return existing

'''
	Batch add tracks to a Deezer playlist with <playlistid>
	return 1 if okay, -1 if not
'''
def add_tracks(playlistid, tracklist):
	tracklist = list(set(tracklist))
	strlist = ','.join(str(e) for e in tracklist)
	params = urllib.parse.urlencode({'songs':strlist}).encode('UTF-8')
	url = 'https://api.deezer.com/playlist/'+str(playlistid)+'/tracks?access_token='+token
	f = urllib.request.urlopen(url, data=params)
	fstr = f.read().decode('utf-8')
	if fstr == "true":
		return 1
	else:
		logger.error("Error adding tracks: " + fstr)
		return -1


def retrieve_deezer_data(deezer_api_url):
	data = []
	next_page = True
	while next_page:
		response = requests.get(deezer_api_url+'?token={token}').json()
		if response.get('error'):
			logger.error(response)
			next_page = False
			return
		data += response.get('data')
		if response.get('next'):
			deezer_api_url = response.get('next')
		else:
			next_page = False
	return data


def find_playlist(playlist_name, user_id):
	playlists_url = f'https://api.deezer.com/user/{user_id}/playlists'
	playlists = retrieve_deezer_data(playlists_url)
	if not playlists:
		time.sleep(.5)
		return find_playlist(playlist_name, user_id)
	return get_safely([playlist for playlist in playlists
			if playlist.get('title') == playlist_name], 0)


def get_safely(l, idx):
	try:
		return l[idx]
	except IndexError:
		return None


def check_track_is_added(track_id, playlist):
	tracks = retrieve_deezer_data(playlist.get('tracklist'))
	return bool(len([track for track in tracks
				if track.get('id') == track_id]))


'''
	WORK IT HARDER
		MAKE IT BETTER
			DO IT FASTER
				MAKES US STRONGER
'''
def start_import():
	# work work, gotta work!
	print("Importing "+str(len(selected_playlists))+ " playlist(s) to Deezer")
	existing_lists = get_deezer_playlists(-1)
	global jsoncont

	for li in jsoncont:
		#only use selected Playlists that do not exist on deezer
		playlist_exists = bool(len([li['name'] for exli in existing_lists if exli in li['name']]))
		if playlist_exists:
			playlist = find_playlist(li['name'], USER_ID)
			id_ = playlist.get('id')

		track_ids = []
		for trk in li['tracks']:
			if 'isrc' not in trk['track']['external_ids']:
				logger.error("Track has no ISRC code; skipping adding track")
				continue
			
			trid = search_track(trk)
			if trid > -1:
				if playlist_exists and check_track_is_added(trid, playlist):
					print("- Not adding track, track already added "+trk['track']['name'])
				else:
					track_ids.append(trid)
					print("+ Found track "+trk['track']['name'])
			else:
				logger.error("Unavailable track "+trk['track']['name']+" ["+trk['track']['external_ids']['isrc']+"] on playlist '" + li['name'] + "'")
				print("- Unavailable track "+trk['track']['name']+" ["+trk['track']['external_ids']['isrc']+"]")

		if len(track_ids) > 0:
			if not playlist_exists:
				print("Creating playlist "+li['name']+" ...")
				id_ = add_playlist(li['name'])
			else:
				print("Adding to playlist "+li['name']+" ...")

			if id_ == -1:
				continue

			resp = add_tracks(id_, track_ids)
			if resp == -1:
				print("! Error adding tracks")
			else:
				print("Added "+str(len(track_ids))+" tracks to "+li['name'])
	print("~~ Finished! ~~")

'''
	Reads the file from disk
'''
def readfile():
	global longest_playlistcount, jsoncont
	parser = argparse.ArgumentParser(description='Imports your Spotify playlists to Deezer. By default, opens a browser window '
		+ 'to authorize the Deezer Web API')
	parser.add_argument('file', help='output filename', nargs='?')
	args = parser.parse_args()

	if args.file is None:
		args.file = FILENAME

	with (open(args.file, 'r', encoding='utf-8')) as f:
		jsoncont = json.load(f)

	for plist in jsoncont:
		playlist_names.append({'name':plist['name'], 'id':plist['id'], 'count':len(plist['tracks'])})
		selected_playlists.add(plist['id'])
		if len(plist['tracks']) > longest_playlistcount:
			longest_playlistcount = len(plist['tracks'])


def main():
	readfile()
	authorize()
	if shouldparse:
		start_import()
	else:
		print("Error authenticating. Try again!")


if __name__ == '__main__':
	main()
