import requests, lxml, json
from datetime import datetime
from bs4 import BeautifulSoup
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
from os import environ, path

W_CURR_DIR = path.dirname(__file__)



W_BILLBOARD_BASE_URL     = "https://www.billboard.com/charts"
W_SPOTIFY_BASE_URL       = "https://accounts.spotify.com"
W_PLAYLIST_FILE          = f"{W_CURR_DIR}/data/spotify_playlist.json"
W_TOP100_TRACKS_FILE     = f"{W_CURR_DIR}/data/top100_tracks.json"
W_SPOTIFY_TOKEN          = f"{W_CURR_DIR}/secret/token.txt"
W_SPOTIFY_USERNAME       = environ.get("SPOTIFY_USERNAME")
W_SPOTIFY_CLIENT_ID      = environ.get("SPOTIFY_CLIENT_ID")
W_SPOTIFY_CLIENT_SECRET  = environ.get("SPOTIFY_CLIENT_SECRET")


def is_valid_date_format(p_date_str: str, p_format : str):            
    # print("The original string is : " + str(p_date_str))        
    w_is_valid = True    
    # using try-except to check for truth value
    try:
        w_date = datetime.strptime(p_date_str, p_format)
        w_is_valid = bool(w_date)

        w_present = datetime.now()
        # print(w_present.date())
        # print(w_date.date())
        if w_date.date() > w_present.date():
            print("Date cannot be in the future.")
            w_is_valid = False
    except ValueError:
        w_is_valid = False
        # print("Not valid format")
    
    return w_is_valid

    
def create_spotify_auth() -> Spotify:
    
    w_auth_manager : SpotifyOAuth = SpotifyOAuth(client_id=W_SPOTIFY_CLIENT_ID,
                                                client_secret=W_SPOTIFY_CLIENT_SECRET,
                                                username=W_SPOTIFY_USERNAME,
                                                scope="playlist-modify-private",
                                                redirect_uri="http://example.com",
                                                show_dialog=True,
                                                cache_path=W_SPOTIFY_TOKEN) 
    w_spotify : Spotify = Spotify(auth_manager=w_auth_manager) 
    
    return w_spotify    
    
        

def  get_spotify_tracks_uri(p_travel_to : str,
                            p_top_100_songs: list, 
                            p_spotify      : Spotify):
    w_uris = []
    w_top_100_list= []
    w_top100_day = p_travel_to.split("-")
    w_year = w_top100_day[0]
    # print(w_year)    

    for song in p_top_100_songs:
        # print(song) 
        w_tracks_dict : dict = p_spotify.search(q=f"track:{song} year:{w_year}", type="track")
        # print(json.dumps(w_tracks_dict))#use json dump to get double quotes back        
        w_track_uri = None
        for key, track in w_tracks_dict.items():
            try:
                w_track_uri = track["items"][0]["uri"]
                w_uris.append(w_track_uri)
            except Exception as e:
                print(f"Track {song}, not found on spotify. Action:Skipped.")    
        
        w_new_song : json = {
                        "track" : song,
                        "date"  : p_travel_to,
                        "Spotify_uri" : w_track_uri 
                    }
        w_top_100_list.append(w_new_song)
        
    # print(w_top_100_list)
    if w_top_100_list:        
        with open(W_TOP100_TRACKS_FILE, mode="w") as f:
            json.dump(obj=w_top_100_list,fp=f,indent=4)       
            
    return w_uris


def get_existing_json_file_content(p_file_name) -> json:
    w_file_content = None
    try:
        with open(p_file_name, mode="r") as f:
            w_file_content : list = json.load(f)                          
    except Exception as e:
        print("No file found")
        w_file_content = None
    
    return w_file_content


def get_existing_playlist_uri(p_playlist_name : str, p_file_content: json) -> str:    
    w_playlist_uri = None
    try:
        w_playlist = p_file_content["playlist"]            
        if p_playlist_name in w_playlist:            
            w_playlist_uri = w_playlist[p_playlist_name]                   
    except Exception as e:
        print("No file uri found")
        w_playlist_uri = None
    
    return w_playlist_uri


def save_playlist_uri_to_file(p_playlist_name, p_playlist_uri, p_playlist_file_cont):
    # print(p_playlist_name," - URI:",p_playlist_uri,' - Content:',p_playlist_file_cont)
    if p_playlist_file_cont == None or p_playlist_file_cont == "" or "playlist" not in p_playlist_file_cont:
        w_content : json =  {
                                "playlist":         
                                    {
                                    p_playlist_name:p_playlist_uri
                                    }        
                            }
    elif p_playlist_name in p_playlist_file_cont["playlist"]:
        print("Plalist is already in the file")
        w_content = None
    else:
        w_content = p_playlist_file_cont
        w_new_data : json = {p_playlist_name:p_playlist_uri}

        w_content["playlist"].update(w_new_data)
        # print(json.dumps(w_content, indent=4))    
        
    if w_content != None:
        with open(W_PLAYLIST_FILE, mode="w") as f:
            json.dump(obj=w_content,fp=f,indent=4)

    
    
def main() -> None:
    
    while True:
        try:
            w_travel_to = input("Which musical year do you want to travel to? (YYYY-MM-DD)\n")    
            if not is_valid_date_format(w_travel_to,"%Y-%m-%d"):
                raise ValueError("Invalid date format or period.")
            break
        except Exception as e:
            print(e)
                
    w_url = f"{W_BILLBOARD_BASE_URL}/hot-100/{w_travel_to}/"
    w_playlist_uri  = None 
    
    w_playlist_name = f"{w_travel_to} Billboard 100"
    w_playlist_desc = f"Billboard 100 songs for the week of {w_travel_to}"
    print(w_url)
    
    try:
        w_response = requests.get(w_url)
        w_response.raise_for_status()
        
        w_website_html = w_response.text    
        # print(w_website_html)
    except Exception as e:
        print("Check Network connection and try again.")
        return

    if not w_website_html:
        print("Fail to get Billboard data, check network and try again.")
        return

    w_soup = BeautifulSoup(w_website_html, "lxml")
    # print(w_soup.prettify)
    
    w_top_charts = w_soup.select("li ul li h3")
    # print(w_top_charts)
    w_top_100_songs = [song.getText().strip() for song in w_top_charts]    
    print(f"{len(w_top_100_songs)} tracks found")    
    
    if len(w_top_100_songs) == 0:
        print("No Tracks found for the date.")
        return
    
    w_spotify : Spotify = create_spotify_auth()
    w_current_user = w_spotify.current_user()
    # print(w_current_user)
    w_user_id       = w_current_user["id"]                
    
    w_playlist_file = get_existing_json_file_content(W_PLAYLIST_FILE)
    
    if w_playlist_file != None and w_playlist_file != "":
        w_playlist_uri = get_existing_playlist_uri(w_playlist_name, w_playlist_file)
        print(f"Found existing playlist uri {w_playlist_uri} for {w_playlist_name}")
    
        
    if w_playlist_uri == None or w_playlist_uri == "":
        w_playlist : dict = w_spotify.user_playlist_create( user        = w_user_id,
                                                            name        = w_playlist_name,
                                                            public      = False,
                                                            description = w_playlist_desc)
        w_playlist_uri = w_playlist["uri"]        
        save_playlist_uri_to_file(w_playlist_name, w_playlist_uri, w_playlist_file)            
            
    w_tracks_uri : list = get_spotify_tracks_uri(w_travel_to, w_top_100_songs, w_spotify)    
    if w_tracks_uri != "" and w_tracks_uri != None:
        w_spotify.user_playlist_add_tracks(user = w_user_id,playlist_id=w_playlist_uri,tracks=w_tracks_uri)    
        
    print("Playlist loading completed.")
        
        
if __name__ == "__main__":
    if not W_SPOTIFY_USERNAME or not W_SPOTIFY_CLIENT_ID  or not W_SPOTIFY_CLIENT_SECRET or not W_SPOTIFY_TOKEN:
        print("FAIL TO RUN:: Confirm all environment variable are set and try again.")
    else:
        main()