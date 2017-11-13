# As is readily apparent, my code is an almost unchanged copy of
# oauth1_twitter_caching.py from lecture 9, up through line 208.

# I worked on this with Jacob Haspiel and Tyler Hoff,
# who helped me create the virtual environment and requirements.txt file.
# Tyler also gave me the dictionary warning on lines 211-212.

import requests_oauthlib
import webbrowser
import json
import secret_data # need properly formatted file, see example
from datetime import datetime

# CACHING SETUP
# --------------------------------------------------
# Caching constants
# --------------------------------------------------

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DEBUG = False
CACHE_FNAME = "cache_contents.json"
CREDS_CACHE_FILE = "creds.json"

# --------------------------------------------------
# Load cache files: data and credentials
# --------------------------------------------------
# Load data cache
try:
    with open(CACHE_FNAME, 'r') as cache_file:
        cache_json = cache_file.read()
        CACHE_DICTION = json.loads(cache_json)
except:
    CACHE_DICTION = {}

# Load creds cache
try:
    with open(CREDS_CACHE_FILE,'r') as creds_file:
        cache_creds = creds_file.read()
        CREDS_DICTION = json.loads(cache_creds)
except:
    CREDS_DICTION = {}

#---------------------------------------------
# Cache functions
#---------------------------------------------
def has_cache_expired(timestamp_str, expire_in_days=7):
    """Check if cache timestamp is over expire_in_days old"""
    # gives current datetime
    now = datetime.now()

    # datetime.strptime converts a formatted string into datetime object
    cache_timestamp = datetime.strptime(timestamp_str, DATETIME_FORMAT)

    # subtracting two datetime objects gives you a timedelta object
    delta = now - cache_timestamp
    delta_in_days = delta.days

    # now that we have days as integers, we can just use comparison
    # and decide if cache has expired or not
    if delta_in_days > expire_in_days:
        return True  # It's been longer than expiry time
    else:
        return False

def get_from_cache(identifier, dictionary):
    """If unique identifier exists in specified cache dictionary and has not expired, return the data associated with it from the request, else return None"""
    identifier = identifier.upper() # Assuming none will differ with case sensitivity here
    if identifier in dictionary:
        data_assoc_dict = dictionary[identifier]
        if has_cache_expired(data_assoc_dict['timestamp'],data_assoc_dict["expire_in_days"]):
            if DEBUG:
                print("Cache has expired for {}".format(identifier))
            # also remove old copy from cache
            del dictionary[identifier]
            data = None
        else:
            data = dictionary[identifier]['values']
    else:
        data = None
    return data

def set_in_data_cache(identifier, data, expire_in_days):
    """Add identifier and its associated values (literal data) to the data cache dictionary, and save the whole dictionary to a file as json"""
    identifier = identifier.upper()
    CACHE_DICTION[identifier] = {
        'values': data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT),
        'expire_in_days': expire_in_days
    }
    with open(CACHE_FNAME, 'w') as cache_file:
        cache_json = json.dumps(CACHE_DICTION)
        cache_file.write(cache_json)

def set_in_creds_cache(identifier, data, expire_in_days):
    """Add identifier and its associated values (literal data) to the credentials cache dictionary, and save the whole dictionary to a file as json"""
    identifier = identifier.upper() # make unique
    CREDS_DICTION[identifier] = {
        'values': data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT),
        'expire_in_days': expire_in_days
    }
    with open(CREDS_CACHE_FILE, 'w') as cache_file:
        cache_json = json.dumps(CREDS_DICTION)
        cache_file.write(cache_json)


# OAuth1 API Constants - vary by API
# Private data in a hidden secret_data.py file
CLIENT_KEY = secret_data.client_key
CLIENT_SECRET = secret_data.client_secret

# Specific to API URLs, not private
REQUEST_TOKEN_URL = "https://www.tumblr.com/oauth/request_token"
BASE_AUTH_URL = "https://www.tumblr.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://www.tumblr.com/oauth/access_token"

def get_tokens(client_key=CLIENT_KEY, client_secret=CLIENT_SECRET,request_token_url=REQUEST_TOKEN_URL,base_authorization_url=BASE_AUTH_URL,access_token_url=ACCESS_TOKEN_URL,verifier_auto=False):
    oauth_inst = requests_oauthlib.OAuth1Session(client_key,client_secret=client_secret)

    fetch_response = oauth_inst.fetch_request_token(request_token_url)

    # Using the dictionary .get method in these lines
    resource_owner_key = fetch_response.get('oauth_token')
    resource_owner_secret = fetch_response.get('oauth_token_secret')

    auth_url = oauth_inst.authorization_url(base_authorization_url)
    # Open the auth url in browser:
    webbrowser.open(auth_url) # For user to interact with & approve access of this app -- this script

    # Deal with required input, which will vary by API
    if verifier_auto:  # if the input is default (True), like Twitter
        verifier = input("Please input the verifier:  ")
    else:
        redirect_result = input("Paste the full redirect URL here:  ")
        oauth_resp = oauth_inst.parse_authorization_response(redirect_result) # returns a dictionary -- you may want to inspect that this works and edit accordingly
        verifier = oauth_resp.get('oauth_verifier')

    # Regenerate instance of oauth1session class with more data
    oauth_inst = requests_oauthlib.OAuth1Session(client_key, client_secret=client_secret, resource_owner_key=resource_owner_key, resource_owner_secret=resource_owner_secret, verifier=verifier)

    oauth_tokens = oauth_inst.fetch_access_token(access_token_url) # returns a dictionary

    # Use that dictionary to get these things
    # Tuple assignment syntax
    resource_owner_key, resource_owner_secret = oauth_tokens.get('oauth_token'), oauth_tokens.get('oauth_token_secret')

    return client_key, client_secret, resource_owner_key, resource_owner_secret, verifier

def get_tokens_from_service(service_name_ident, expire_in_days=7): # Default: 7 days for creds expiration
    creds_data = get_from_cache(service_name_ident, CREDS_DICTION)
    if creds_data:
        if DEBUG:
            print("Loading creds from cache...")
            print()
    else:
        if DEBUG:
            print("Fetching fresh credentials...")
            print("Prepare to log in via browser.")
            print()
        creds_data = get_tokens()
        set_in_creds_cache(service_name_ident, creds_data, expire_in_days=expire_in_days)
    return creds_data

def create_request_identifier(url, params_diction):
    sorted_params = sorted(params_diction.items(),key=lambda x:x[0])
    params_str = "_".join([str(e) for l in sorted_params for e in l]) # Make the list of tuples into a flat list using a complex list comprehension
    total_ident = url + "?" + params_str
    return total_ident.upper() # Creating the identifier

def get_data_from_api(request_url, service_ident, params_diction, expire_in_days=7):
    """Check in cache, if not found, load data, save in cache and then return that data"""
    ident = create_request_identifier(request_url, params_diction)
    data = get_from_cache(ident,CACHE_DICTION)
    if data:
        if DEBUG:
            print("Loading from data cache: {}... data".format(ident))
    else:
        if DEBUG:
            print("Fetching new data from {}".format(request_url))

        # Get credentials
        client_key, client_secret, resource_owner_key, resource_owner_secret, verifier = get_tokens_from_service(service_ident)

        # Create a new instance of oauth to make a request with
        oauth_inst = requests_oauthlib.OAuth1Session(client_key, client_secret=client_secret,resource_owner_key=resource_owner_key,resource_owner_secret=resource_owner_secret)
        # Call the get method on oauth instance
        # Work of encoding and "signing" the request happens behind the sences, thanks to the OAuth1Session instance in oauth_inst
        resp = oauth_inst.get(request_url,params=params_diction)
        # Get the string data and set it in the cache for next time
        data_str = resp.text
        data = json.loads(data_str)
        set_in_data_cache(ident, data, expire_in_days)
    return data


if __name__ == "__main__":
    if not CLIENT_KEY or not CLIENT_SECRET:
        print("You need to fill in client_key and client_secret in the secret_data.py file.")
        exit()
    if not REQUEST_TOKEN_URL or not BASE_AUTH_URL:
        print("You need to fill in this API's specific OAuth2 URLs in this file.")
        exit()

    # Invoke functions
    tumblr_search_baseurl = "http://api.tumblr.com/v2/blog/starwarsmemes.tumblr.com/posts"
    tumblr_search_params = {"api_key": CLIENT_KEY, "notes_info": True}
    tumblr_result = get_data_from_api(tumblr_search_baseurl, "Tumblr", tumblr_search_params) # Default expire_in_days
    print("\n" + "CACHE READY" + "\n")


    # When delving into the dictionary: tumblr_result["response"]["posts"]
    # (DO NOT INCLUDE ["values"] KEY)


    # get data from posts on starwarsmemes.tumblr.com
    all_posts = tumblr_result["response"]["posts"]
    all_posts_dct_lst = []
    for post in all_posts:
        post_dct = {}
        post_dct["post_url"] = post["post_url"]
        post_dct["post_type"] = post["type"]
        post_dct["note_count"] = post["note_count"]
        like_count = 0
        reblog_count = 0
        for note in post["notes"]:
            if note["type"] == "like":
                like_count = like_count + 1
            elif note["type"] == "reblog":
                reblog_count = reblog_count + 1
        post_dct["like_count"] = like_count
        post_dct["reblog_count"] = reblog_count
        all_posts_dct_lst.append(post_dct)

    # write CSV file about posts' popularity
    try:
        csv_popularity = open("post_popularity.csv", "r")
        csv_popularity.close()
        print("POPULARITY CSV FILE ALREADY WRITTEN" + "\n")
    except:
        all_posts_dct_lst_sorted = sorted(all_posts_dct_lst, key = lambda x: x["note_count"], reverse = True)
        csv_popularity = open("post_popularity.csv", "w")
        csv_popularity.write("POST URL, POST TYPE, NOTES, LIKES, REBLOGS\n")
        for post_dct in all_posts_dct_lst_sorted:
            csv_popularity.write('"{}",'.format(post_dct["post_url"]))
            csv_popularity.write('"{}",'.format(post_dct["post_type"]))
            csv_popularity.write('"{}",'.format(post_dct["note_count"]))
            csv_popularity.write('"{}",'.format(post_dct["like_count"]))
            csv_popularity.write('"{}",'.format(post_dct["reblog_count"]))
            csv_popularity.write("\n")
        csv_popularity.close()
        print("POPULARITY CSV FILE WRITTEN" + "\n")

    # write CSV file about posts' types
    try:
        csv_types = open("post_types.csv", "r")
        csv_types.close()
        print("POST TYPE CSV ALREADY WRITTEN" + "\n")
    except:
        type_count_dct = {}
        photo_count = 0
        chat_count = 0
        text_count = 0
        other_count = 0
        for post in all_posts_dct_lst:
            if post["post_type"] == "photo":
                photo_count = photo_count + 1
            elif post["post_type"] == "chat":
                chat_count = chat_count + 1
            elif post["post_type"] == "text":
                text_count = text_count + 1
            else:
                other_count = other_count + 1
        type_count_dct["photo"] = photo_count
        type_count_dct["chat"] = chat_count
        type_count_dct["text"] = text_count
        type_count_dct["other"] = other_count
        type_count_dct_keys = type_count_dct.keys()
        type_count_dct_keys_sorted = sorted(type_count_dct_keys, key = lambda x: type_count_dct[x], reverse = True)
        csv_types = open("post_types.csv", "w")
        csv_types.write("POST TYPE, NUMBER OF POSTS\n")
        for post_type in type_count_dct_keys_sorted:
            csv_types.write('"{}",'.format(post_type))
            csv_types.write('"{}",'.format(type_count_dct[post_type]))
            csv_types.write("\n")
        csv_types.close()
        print("POST TYPE CSV FILE WRITTEN" + "\n")
