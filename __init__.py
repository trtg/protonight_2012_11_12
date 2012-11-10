from flask import Flask,render_template,request,redirect,url_for,abort,session,jsonify
from oauth2client.client import OAuth2WebServerFlow#google auth
from youtube_credentials import youtube_client_id,youtube_client_secret
from twitter_credentials import twitter_consumer_key,twitter_consumer_secret
from rauth.service import OAuth1Service
from apiclient.discovery import build#google api-client
import httplib2
import requests
import json

app = Flask(__name__,static_path='/static/')
#never enable this when externally visible
app.config['DEBUG']=True

#------------twitter------------------------------
twitter_service=OAuth1Service(
                name='twitter',
                consumer_key=twitter_consumer_key,
                consumer_secret=twitter_consumer_secret,
                request_token_url='https://api.twitter.com/oauth/request_token',
                access_token_url='https://api.twitter.com/oauth/access_token',
                authorize_url='https://api.twitter.com/oauth/authorize',
                header_auth=True)


#-------------youtube-------------------------
flow = OAuth2WebServerFlow(client_id=youtube_client_id,
                           client_secret=youtube_client_secret,
                           scope='https://www.googleapis.com/auth/youtube.readonly',
                           redirect_uri='http://www.quantifythat.com/youtube_callback')
#------------------------------------------------


@app.route('/')
def handle_main():
    app.logger.error(request.query_string)
    userid = request.args.get('fbuser')
    if userid is None:
        userid=0

    return render_template('main_page.html',fbuser=userid)

@app.route('/connect.html')
@app.route('/connect')
def handle_connect():
    return render_template('connect.html')

@app.route('/layout')
def handle_layout():
    return render_template('layout.html')

@app.route('/learn.html')
@app.route('/learn')
def handle_learn():
    return render_template('learn.html')

@app.route('/youtube_callback')
def handle_youtube_callback():
    app.logger.error('in handle_oauth')
    app.logger.error(request.args.get('code'))
    request.args.get('code')
    credentials = flow.step2_exchange(request.args.get('code'))
    youtube= build('youtube','v3',http=credentials.authorize(httplib2.Http()))

    #get the id of your uploads playlist by listing your channels
    channels_response = youtube.channels().list(mine="", part="contentDetails").execute()
    app.logger.error(channels_response)
    #just grabbing first item for now
    uploads_list_id= channels_response['items'][0].get('contentDetails').get('relatedPlaylists').get('uploads')
    app.logger.error("uploads_list_id is %s"% uploads_list_id)

    #list the contents of your uploads playlist
    next_page_token=""
    app.logger.error('playlistId=%s',uploads_list_id)
    playlist_items_response = youtube.playlistItems().list(playlistId=uploads_list_id,part="snippet",maxResults=50,pageToken=next_page_token).execute()
    app.logger.error(playlist_items_response)
    #now render_template something useful with the json here
    return jsonify(playlist_items_response)

@app.route('/twitter_callback')
def handle_twitter_callback():
    app.logger.error('in twitter_callback')
    app.logger.error("oauth_token %s" % request.args.get('oauth_token'))
    app.logger.error("oauth_verifier %s" %request.args.get('oauth_verifier'))
    app.logger.error(request.query_string)
    return "in twitter_callback"

#chris.jason@espn.com
@app.route('/start_youtube')
def handle_start_youtube():
    app.logger.error('in start_youtube')
    auth_uri = flow.step1_get_authorize_url()
    app.logger.error('auth_uri is %s'% auth_uri)
    app.logger.error(auth_uri)
    return redirect(auth_uri)

@app.route('/start_twitter')
def handle_start_twitter():
   request_token,request_token_secret = twitter_service.get_request_token(method='GET',params={'oauth_callback':'http://www.quantifythat.com/twitter_callback'})
   authorize_url=twitter_service.get_authorize_url(request_token) 
   return redirect(authorize_url)

if __name__ == '__main__':
    app.run()
