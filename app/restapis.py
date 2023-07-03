from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.shortcuts import redirect
import os
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
@api_view(['GET'])
def instagramapi(request):
    access_token = request.headers.get('Authorization')
    # Get User Instagram Id
    url = f"https://graph.facebook.com/v17.0/me/accounts?fields=instagram_business_account"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url,headers=headers)
    account_id = response.json().get('data')[0].get("instagram_business_account")["id"]

    accountinfo = getUserdata(account_id,access_token)
    media = getmedia(account_id,access_token) # Getting Media from end point
    return Response({"media":media,"account_info":accountinfo})


def getmedia(accountid,access_token):
    url = f"https://graph.facebook.com/v17.0/{accountid}/media?fields=id,ig_id,media_product_type,media_type,media_url,thumbnail_url,timestamp, username,like_count,comments_count,comments,caption"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url,headers=headers)
    # print(response.json())

    metric = {

        'metric':'engagement,impressions,reach'
    }

    i = 0
    data = {}
    for _ in response.json()['data']:
        # print(_)
        # Getting Insights of the media
        mediaid = _.get("id")
        print(mediaid)
        url = f"https://graph.facebook.com/{mediaid}/insights"
        insightsresponse = requests.get(url,headers=headers,params=metric)
        # print(insightsresponse.json())
        insightsdata = insightsresponse.json()["data"]
        # print(insightsdata)
        # break




        data_wrt_media = {}

        data_wrt_media['engaements'] = insightsdata[0]['values'][0]['value']
        data_wrt_media['impression'] = insightsdata[1]['values'][0]['value']
        data_wrt_media['reach'] = insightsdata[2]['values'][0]['value']
        print(data_wrt_media['engaements'])
        data_wrt_media['image'] = _.get('media_url')
        data_wrt_media['caption'] = _.get("caption")
        data_wrt_media['likes'] = _.get("like_count")
        data_wrt_media["comments_count"] = _.get("comments_count")
        if _.get("comments"):
            data_wrt_media['comments'] = _.get("comments")['data'][0]['text']



        data[f"image{i}"] = data_wrt_media
        i = i+1


    return data


def getUserdata(accountid,access_token):
    url = f"https://graph.facebook.com/v17.0/{accountid}?fields=username,follows_count,followers_count,profile_picture_url"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)
    return response.json()


def handle_uploaded_file(file):
    # Generate a unique file name or use the original file name
    file_name = "custom_file_name.jpg"

    # Save the file using Django's default storage
    file_path = default_storage.save(os.path.join(settings.MEDIA_ROOT, file_name), ContentFile(file.read()))

    # Obtain the URL of the saved file
    file_url = settings.MEDIA_URL + file_path[len(settings.MEDIA_ROOT):] + file_name

    return file_url



@api_view(['POST'])
def createpost(request):

    access_token = request.POST.get('access_token')
    account_id = request.POST.get("account_id")


    data = {
        'image_url': f'https://upload.wikimedia.org/wikipedia/commons/4/41/Sunflower_from_Silesia2.jpg',
        'caption': request.POST.get('caption')
    }

    url = f"https://graph.facebook.com/v17.0/{account_id}/media/"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.post(url,headers=headers,json=data)

    mediaid = response.json()['id']
    # print(response.json())


    url = f"https://graph.facebook.com/v17.0/{account_id}/media_publish"

    data = {
        'creation_id':mediaid
    }

    response = requests.post(url,headers=headers,data=data)

    # print(response.json())




    return redirect("instagram_redirect")

# Facebook Apis


@api_view(['GET'])
def facebookapi(request):
    access_token = request.headers.get('Authorization')
    page_id = request.query_params.get("page_id")
    # print(access_token)
    # print(page_id)
    # Get Page Picture

    url = f"https://graph.facebook.com/{page_id}?fields=picture{{url}},about,cover,description,followers_count,new_like_count,country_page_likes,name,fan_count"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url,headers=headers)

    # print(response.json())
    media = getfacebookmedia(page_id,access_token)
    context = {
        "image": response.json().get("picture").get("data").get("url"),
        "name":response.json().get("name"),
        "followers":response.json().get("followers_count"),
        "likes": response.json().get("fan_count")
    }

    return Response({"account_info":context,"media":media})


def getfacebookmedia(page_id,access_token):

    url = f"https://graph.facebook.com/{page_id}/?fields=published_posts{{full_picture,message,reactions{{type}},comments{{message, comments{{message}}, comment_count}}}}"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url,headers=headers)

    data = response.json()['published_posts']['data']


    context = {}

    i = 0
    for _ in data:



        dict = {}

        dict['full_image'] = _.get("full_picture")
        dict['message'] = _.get("message")
        dict['reaction_count'] = len(_.get("reactions").get("data")) if _.get("reactions") else None
        # Showing only one comment and one reply for now
        comments = {}
        comments['comment'] = _.get("comments").get("data")[0].get("message") if _.get("comments") else None
        dict['comment_count'] = (_.get("comments").get("data")[0].get("comment_count")+1) if comments['comment'] else 0
        comments['reply'] = _.get("comments").get("data")[0].get("comments").get("data")[0].get("message") if comments.get("comment") and _.get("comments").get("data")[0].get("comments") else None

        dict['comments'] = comments



        context[i] = dict
        # print(context[i])
        i = i+1





    return context


def createfacebookpost(request):
    # print("Hello")
    access_token = request.POST.get("p_access_token")
    page_id = request.POST.get("page_id")
    # print(page_id)
    url = f"https://graph.facebook.com/{page_id}/photos"

    data = {
        "url": "https://images.unsplash.com/photo-1583121274602-3e2820c69888?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1170&q=80",
        "caption":request.POST.get("caption")
    }

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.post(url,headers=headers,json=data)
    # print(response.json())
    return redirect("facebook_redirect")
