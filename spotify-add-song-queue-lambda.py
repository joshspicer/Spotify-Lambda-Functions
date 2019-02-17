import requests
import time
import boto3
import json

# Lambda function written by Josh Spicer <https://joshspicer.com/>

# REMEMBER TO REPLACE `<YOUR REFRESH TOKEN>` and `<YOUR SECRET>` with, well those values!
# Check my guide for how to do so: https://joshspicer.com/spotify-public-queue

# Connect the DynamoDB database
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Spotify-State')

refreshToken = '<YOUR REFRESH TOKEN>'

# Main Function -- SPOTIFY ADD PARTY QUEUE
def lambda_handler(event, context):

    # Get the id query parameter from AWS API gateway
    # This is the spotify song ID.
    if validateInput(event["queryStringParameters"]['id']):
        songID = event["queryStringParameters"]['id']
    else:
        return {'statusCode': 400, 'headers': {'Access-Control-Allow-Origin' : "*", 'content-type': 'application/json'}, 'body': json.dumps({'status': "Error!"})}


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

    # Post the inputted song to a very specific playlist
    r = requests.post('https://api.spotify.com/v1/users/joshspicer37/playlists/0OBq0h6EjCmaPXjeCB4IlM/tracks?uris=' + songID, headers=headers)

    # Return if the process was a success.
    if r.status_code == 201:
        return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin' : "*", 'content-type': 'application/json'}, 'body': json.dumps({'status': "Success!"})}
    else:
        return {'statusCode': 400, 'headers': {'Access-Control-Allow-Origin' : "*", 'content-type': 'application/json'}, 'body': json.dumps({'status': "Error!"})}




# Only called if the current accessToken is expired (on first visit after ~1hr)
def refreshTheToken(refreshToken):

    clientIdClientSecret = 'Basic <YOUR SECRET>'
    data = {'grant_type': 'refresh_token', 'refresh_token': refreshToken}

    headers = {'Authorization': clientIdClientSecret}
    p = requests.post('https://accounts.spotify.com/api/token', data=data, headers=headers)

    spotifyToken = p.json()

    # Place the expiration time (current time + almost an hour), and access token into the DB
    table.put_item(Item={'spotify': 'prod', 'expiresAt': int(time.time()) + 3200, 'accessToken': spotifyToken['access_token']})

def validateInput(input):
    tmp = input.split(":")
    return len(tmp) == 3 and tmp[0] == 'spotify' and tmp[1] == 'track' and tmp[2].isalnum()
