import requests
import time
import boto3
import json

# Lambda function written by Josh Spicer <https://joshspicer.com/>

# REMEMBER TO REPLACE `<YOUR REFRESH TOKEN>` and `<YOUR SECRET>` with, well those values!
# Check my guide for how to do so: https://joshspicer.com/spotify-now-playing

# Connect the DynamoDB database
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Spotify-State')

refreshToken = '<YOUR REFRESH TOKEN>'

# Main Function -- WHAT AM I LISTENING TO?
def lambda_handler(event, context):

    # Defaults
    response = "Josh isn't listening to Spotify right now."
    songName = 'n/a'
    artistName = 'n/a'
    isPlaying = False

    # See if "expiresAt" indeed indicates we need a new token.
    # Spotify access tokens last for 3600 seconds.
    dbResponse = table.get_item(Key={'spotify': 'prod'})
    expiresAt = dbResponse['Item']['expiresAt']

    # If expired....
    if expiresAt <= time.time():
        refreshTheToken(refreshToken)

    dbResponse = table.get_item(Key={'spotify': 'prod'})
    accessToken = dbResponse['Item']['accessToken']

    headers = {'Authorization': 'Bearer ' + accessToken, 'Content-Type': 'application/json', 'Accept': 'application/json'}

    r = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=headers)

    # Try currently playing
    try:
        songName = r.json()['item']['name']
        isPlaying = r.json()['is_playing']
        artistName = r.json()['item']['artists'][0]['name']
        if isPlaying:
            response = "Josh is currently listening to " + songName + " by " + artistName + " on spotify."
    except:
        pass

    # If Josh isn't listening to music, get his last played song.
    if not isPlaying:
        try:
            r2 = requests.get('https://api.spotify.com/v1/me/player/recently-played', headers=headers)
            songName = r2.json()['items'][0]['track']['name']
            artistName = r2.json()['items'][0]['track']['artists'][0]['name']
            response = "Josh last listened to " + songName + " by " + artistName + " on spotify."
        except:
            pass


    return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin' : "*", 'content-type': 'application/json'},
    'body': json.dumps({'songName': songName, 'isPlaying': isPlaying, 'artistName': artistName, 'response': response})}


# Only called if the current accessToken is expired (on first visit after ~1hr)
def refreshTheToken(refreshToken):

    clientIdClientSecret = 'Basic <YOUR SECRET>'
    data = {'grant_type': 'refresh_token', 'refresh_token': refreshToken}

    headers = {'Authorization': clientIdClientSecret}
    p = requests.post('https://accounts.spotify.com/api/token', data=data, headers=headers)

    spotifyToken = p.json()

    # Place the expiration time (current time + almost an hour), and access token into the DB
    table.put_item(Item={'spotify': 'prod', 'expiresAt': int(time.time()) + 3200, 'accessToken': spotifyToken['access_token']})
