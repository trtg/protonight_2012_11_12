import httplib2
import requests
import json

from flask import Flask,render_template,request,redirect,url_for,abort,session,jsonify
from flask_config import flask_secret_key
from youtube_credentials import youtube_client_id,youtube_client_secret
from twitter_credentials import twitter_consumer_key,twitter_consumer_secret
from twilio_credentials import twilio_account_id,twilio_token,twilio_source_number

from oauth2client.client import OAuth2WebServerFlow#google auth
from rauth.service import OAuth1Service,OAuth2Service
from apiclient.discovery import build#google api-client

from twilio.rest import TwilioRestClient

app = Flask(__name__,static_path='/static/')
#never enable this when externally visible
app.config['DEBUG']=True
app.config['SECRET_KEY']=flask_secret_key
#hack for demo purposes

#------------twilio------------------------------
client = TwilioRestClient(twilio_account_id, twilio_token)


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
#the scope specified here is full read/write as opposed to just
#youtube.readonly or youtube.upload
youtube_service =OAuth2Service(
        name='youtube',
        consumer_key=youtube_client_id,
        consumer_secret=youtube_client_secret,
        access_token_url='https://accounts.google.com/o/oauth2/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth')
#------------------------------------------------

@app.route('/')
def handle_main():
    app.logger.error(request.query_string)
    if session.get('youtube_allowed',None)==True: 
        youtube_allowed=1
    else:
        youtube_allowed=0

    return render_template('main_page.html',youtube_allowed=youtube_allowed)

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

@app.route('/twilio')
def handle_twilio():
    dest_number = request.args.get('dest')
    #FIXME maybe dynamically generate messages using query parameters instead 
    #of using one canned message?
    call = client.calls.create(to=dest_number, 
                           from_=twilio_source_number, 
                           url="http://www.quantifythat.com/static/message.xml",method="GET")
    print call.sid
    return ("called %s"%dest_number)


@app.route('/youtube_callback')
def handle_youtube_callback():
    app.logger.error('in handle_oauth')
    app.logger.error(request.args.get('code'))
    #data=dict(code=request.args.get('code'),redirect_uri='http://www.quantifythat.com/youtube_callback')
    data=dict(code=request.args.get('code'),redirect_uri='http://www.quantifythat.com/youtube_callback')
    if session.get('youtube_access_token',None) is None or session.get('youtube_refresh_token',None) is None:
        #access_token=youtube_service.get_access_token('POST',data=data).content['access_token']
        results=youtube_service.get_access_token('POST',data=data).content
        app.logger.error(results)
        #not getting a refresh token?!!!!
        app.logger.error('overwriting access token')
        session['youtube_access_token']=results['access_token']
        #session['youtube_refresh_token']=results['refresh_token']
        #app.logger.error('access token is ')
        #app.logger.error(results['access_token'])
        #app.logger.error('refresh token is ')
        #app.logger.error(results['refresh_token'])

    #FIXME set authorization state internally and just redirect to / so the user doesn't see cluttered URLs
    session['youtube_allowed']=True
    return redirect('/')

@app.route('/list_uploads')
def handle_list_uploads():
    #result = youtube_service.get('https://www.googleapis.com/youtube/v3/playlists',params=dict(access_token=session['youtube_access_token']).content
    
    params={'part':'snippet,status','mine':'True','access_token':session['youtube_access_token'],'maxResults':'50'}
    result = youtube_service.get('https://www.googleapis.com/youtube/v3/playlists',params=params).content
    app.logger.error('handle_list_uploads')
    app.logger.error(result)
    return jsonify(result)

@app.route('/list_items')
def handle_list_items():
    params={'part':'snippet','playlistId':'PLAVoytVaY-lG1z3d9uBNmsuHLJiUBG2Ie','access_token':session['youtube_access_token'],'maxResults':'50'}
    result = youtube_service.get('https://www.googleapis.com/youtube/v3/playlistItems',params=params).content
    app.logger.error('handle_list_items')
    app.logger.error(result)
    return jsonify(result)

@app.route('/create_playlist')
def handle_create_playlist():
    template_list={ 'snippet':{'title':'mylist','description':'how to play basketball'}, 'status':{'privacyStatus':'public'}}

    params={'part':'snippet,status','access_token':session['youtube_access_token'],'maxResults':'50'}
    headers={'Content-type':'application/json'}
    result = youtube_service.post('https://www.googleapis.com/youtube/v3/playlists',params=params,data=json.dumps(template_list),headers=headers).content
    app.logger.error('handle_list_items')
    app.logger.error(result)
    return jsonify(result)
 

#https://www.googleapis.com/youtube/v3/playlistItems
@app.route('/twitter_callback')
def handle_twitter_callback():
    app.logger.error('in twitter_callback')
    app.logger.error("oauth_token %s" % request.args.get('oauth_token'))
    app.logger.error("oauth_verifier %s" %request.args.get('oauth_verifier'))
    app.logger.error(request.query_string)
    return "in twitter_callback"

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
