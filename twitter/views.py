import logging
from django.contrib import messages
from django.shortcuts import redirect, render
from requests import request
from requests_oauthlib import OAuth1Session
import os
import json
from django.http import JsonResponse, HttpResponse
from twitter.models import TwitterSchedulerModel
from datetime import datetime, timedelta
import arrow
from django.contrib.auth import authenticate, login as dj_login, logout
from django.contrib.auth.decorators import login_required

# Create your views here.

consumer_key = "PASTE_YOUR_CONSUMER_SECRET_HERE"
consumer_secret = "PASTE_YOUR_CONSUMER_SECRET_HERE"


def login(request):
    if request.method == 'POST':
        user = authenticate(username=request.POST["user_name"], password=request.POST["password"])
        if user is not None:
            dj_login(request, user)
            return redirect('/my-tweets')
        else:
            messages.info(request, 'invalid credentails')
            return redirect('/login')

    else:
        if request.user.is_authenticated:
            return redirect('/my-tweets')
        else:
            return render(request, 'login.html')

@login_required(login_url='/login', redirect_field_name='')
def postTweet(request):
    if request.method == 'POST':
        # Get the access token
        access_token_url = "https://api.twitter.com/oauth/access_token"
        oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=request.POST["resource_owner_key"],
            resource_owner_secret=request.POST["resource_owner_secret"],
            verifier=request.POST["otp"],
        )
        oauth_tokens = oauth.fetch_access_token(access_token_url)

        access_token = oauth_tokens["oauth_token"]
        access_token_secret = oauth_tokens["oauth_token_secret"]


        if request.POST['date']:
            dateList = request.POST['date'].split('-')
            timeList = request.POST['time'].split(':')
            tweetTime = datetime(int(dateList[0]), int(dateList[1]), int(
                dateList[2]), int(timeList[0]), int(timeList[1]), 0, 0)
          
            newTweet = TwitterSchedulerModel(
                tweet=request.POST["message"], tweet_at=tweetTime, sent=False, otp=request.POST["otp"],
                resource_owner_key=access_token, resource_owner_secret=access_token_secret, user=request.user )
        else:
            sendTweet(access_token,
                      access_token_secret, request.POST["otp"], request.POST["message"])

            newTweet = TwitterSchedulerModel(
                tweet=request.POST["message"], tweet_at=datetime.now(), sent=True, otp=request.POST["otp"],
                resource_owner_key=request.POST["resource_owner_key"], 
                resource_owner_secret=request.POST["resource_owner_secret"], user=request.user)

        newTweet.save()

        return redirect('/my-tweets')

    else:
        return render(request, 'post-tweet.html')


def generateTwitterVerifierUrl(request):

    if request.method == "POST":
        request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
        oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

        try:
            fetch_response = oauth.fetch_request_token(request_token_url)
        except ValueError:
            print(
                "There may have been an issue with the consumer_key or consumer_secret you entered."
            )

            return JsonResponse(
                {"message": "There may have been an issue with the consumer_key or consumer_secret you entered"},
                status=401)

        resource_owner_key = fetch_response.get("oauth_token")
        resource_owner_secret = fetch_response.get("oauth_token_secret")
        print("Got OAuth token: %s" % resource_owner_key)

        # Get authorization
        base_authorization_url = "https://api.twitter.com/oauth/authorize"
        authorization_url = oauth.authorization_url(base_authorization_url)
        

        return JsonResponse(
            {'authorization_url': authorization_url, 'resource_owner_secret': resource_owner_secret,
             'resource_owner_key': resource_owner_key, 'tweet_message': request.POST['message']}, status=200)
    else:
        return JsonResponse(
            {"message": "Request type error"}, status=401)

@login_required(login_url='/login', redirect_field_name='')
def showMyTweets(request):
    tweets = TwitterSchedulerModel.objects.filter(user=request.user)
    print('tweets ', tweets.values)
    return render(request, 'tweets.html', {'allTweets': tweets})


def sendTweet(access_token, access_token_secret, otp, message):
    print("token ", access_token, access_token_secret, otp)
    payload = {"text": message}
    

    # Make the request
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )

    # Making the request
    response = oauth.post(
        "https://api.twitter.com/2/tweets",
        json=payload,
    )

    if response.status_code != 201:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text)
        )

    print("Response code: {}".format(response.status_code))

    # Saving the response as JSON
    json_response = response.json()
    print(json.dumps(json_response, indent=4, sort_keys=True))
    return True


def sendScheduledTweets():
    time = datetime.now()
    print("called before", time)
    #TwitterSchedulerModel.objects.filter(id=20).delete()
    #TwitterSchedulerModel.objects.all().delete()
    tweets = TwitterSchedulerModel.objects.filter(
        sent=False, tweet_at__lte=time)
    print("count ", tweets.count())
    for tweet in tweets:
       
        sendTweet(tweet.resource_owner_key, tweet.resource_owner_secret, tweet.otp, tweet.tweet)
      
        tweet.sent = True
        tweet.save()

    tweets=[]
   # print("all Tweet send", tweets.query)




def home(request):
    return render(request, 'index.html')

def logout_view(request):
    logout(request)
    return redirect('/login')

