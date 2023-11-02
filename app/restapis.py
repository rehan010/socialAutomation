import asyncio
import time
from io import BytesIO
import datetime

import pytz
from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

import os
from .models import *
from PIL import Image
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.models import SocialToken
from django.shortcuts import redirect
import requests
from django.http import JsonResponse
from urllib.parse import quote, urlparse,parse_qs, urlencode

from django.db.models import Q ,Sum

import pytz

import json
from django.conf import settings
import httpx


import string
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


@api_view(['GET'])
def instagramapi(request):
    access_token = request.headers.get('Authorization')
    # Get User Instagram Id
    url = f"https://graph.facebook.com/v17.0/me/accounts?fields=instagram_business_account"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)
    account_id = response.json().get('data')[0].get("instagram_business_account")["id"]

    accountinfo = getUserdata(account_id, access_token)
    media = getmedia(account_id, access_token)  # Getting Media from end point
    return Response({"media": media, "account_info": accountinfo})


def getmedia(accountid, access_token):
    url = f"https://graph.facebook.com/v17.0/{accountid}/media?fields=id,ig_id,media_product_type,media_type,media_url,thumbnail_url,timestamp, username,like_count,comments_count,comments,caption"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    # response.json())

    metric = {

        'metric': 'engagement,impressions,reach'
    }

    i = 0
    data = {}
    for _ in response.json()['data']:
        # _)
        # Getting Insights of the media
        mediaid = _.get("id")
        # mediaid)
        url = f"https://graph.facebook.com/{mediaid}/insights"
        insightsresponse = requests.get(url, headers=headers, params=metric)
        # insightsresponse.json())
        insightsdata = insightsresponse.json()["data"]
        # insightsdata)
        # break

        data_wrt_media = {}

        data_wrt_media['engaements'] = insightsdata[0]['values'][0]['value']
        data_wrt_media['impression'] = insightsdata[1]['values'][0]['value']
        data_wrt_media['reach'] = insightsdata[2]['values'][0]['value']
        # data_wrt_media['engaements'])
        data_wrt_media['image'] = _.get('media_url')
        data_wrt_media['caption'] = _.get("caption")
        data_wrt_media['likes'] = _.get("like_count")
        data_wrt_media["comments_count"] = _.get("comments_count")
        if _.get("comments"):
            data_wrt_media['comments'] = _.get("comments")['data'][0]['text']

        data[f"image{i}"] = data_wrt_media
        i = i + 1

    return data


def fb_social_action_data_organizer(elements, headers):
    data = []
    if elements:
        for element in elements:
            text = element['message']
            comment_urn = element['id']
            if element and len(elements) > 0:
                actor = element["from"]['id']
                name = element['from']['name']
                url = f"https://graph.facebook.com/{actor}?fields=picture{{url}}"

                response_3 = requests.get(url=url, headers=headers)

                if "picture" in response_3.json():

                    display_image = response_3.json().get('picture')['data']['url']
                else:
                    display_image = ''

                obj = {'name': name, "profile_image": display_image, "text": text, 'user_id': actor,
                       "comment_urn": comment_urn}
                urls = []
                if element.get('attachment'):
                    attachment = element.get('attachment')
                    if attachment.get('type') == "photo":
                        # obj['urls'] = attachment.get('media').get('image').get('src')
                        urls.append(attachment.get('media').get('image').get('src'))

                    elif attachment.get('type') == "video_inline":
                        # obj['urls'] = attachment.get('media').get('source')
                        urls.append(attachment.get('media').get('source'))

                obj['urls'] = urls
                obj['liked'] = element.get('user_likes')

                if element.get('comments'):
                    comments = element.get('comments').get('data')
                    obj['next'] = element.get('comments')['paging'].get('next')
                    obj['replies'] = fb_social_action_data_organizer(comments, headers)


                data.append(obj)

            else:
                obj = {'name': "", "profile_image": "", "text": "", "comment_urn": "", 'user_id': '', "urls": []}
                obj['replies'] = {}
                data.append(obj)
    return data


def fb_socialactions(post_urn, access_token, page_id):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    url = f"https://graph.facebook.com/v17.0/{page_id}?fields=picture{{url}}"

    response = requests.get(url=url, headers=headers)

    profile_picture_url = response.json()['picture']['data']['url']

    try:
        url = f"https://graph.facebook.com/{post_urn}?fields=likes.summary(true),comments.summary(true),post_id"
        response = requests.get(url=url, headers=headers)
        response_json = response.json()
        if response_json.get('post_id') == None:
            raise Exception("Response not Valid")

        post = Post_urn.objects.get(urn=post_urn)
        org_id = post.org.org_id
        post.urn = org_id + "_" + response_json.get('post_id')
        post.save()
        post_urn = post.urn
    except Exception as e:
        url = f"https://graph.facebook.com/{post_urn}?fields=reactions.summary(true),comments.filter(stream).summary(true)"
        response = requests.get(url=url, headers=headers)
        response_json = response.json()
    t_likes = response_json.get("reactions", {}).get("summary", {}).get("total_count", {})
    t_comments = response_json.get("comments", {}).get("summary", {}).get("total_count", {})
    try:
        post = Post_urn.objects.get(urn=post_urn)
        post.post_likes = t_likes
        post.post_comments = t_comments
        post.save()
    except Exception as e:
        e
    url = f"https://graph.facebook.com/{post_urn}/comments?fields=message,created_time,from,reactions,attachment,user_likes,comments.order(reverse_chronological).limit(1){{message,created_time,from,reactions,attachment,user_likes,comments{{message, created_time,from, reactions, attachment,user_likes}}}}&order=reverse_chronological&limit=5"

    #     comments{message,created_time,from}  field to get replies
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url=url, headers=headers)
    response_json2 = response.json()

    elements = response_json2.get("data")
    next = None
    if len(elements) > 0:
        next = response_json2.get('paging',{}).get('next')

    data = fb_social_action_data_organizer(elements, headers)


    return t_likes, t_comments, data, profile_picture_url,next


def insta_social_actions_data_organizer(elements, headers):
    data = []
    if elements:
        for element in elements:
            text = element["text"]
            comment_urn = element['id']
            if element and len(elements) > 0:
                name = element['from']['username']

                actor = element.get('user', {}).get('id')

                if actor:
                    url = f"https://graph.facebook.com/v17.0/{actor}?fields=profile_picture_url"
                    response_2 = requests.get(url=url, headers=headers)
                    response_json_2 = response_2.json()

                    if "profile_picture_url" in response_json_2:
                        display_image = response_json_2.get("profile_picture_url")
                    else:
                        display_image = ""
                else:
                    display_image = ""

                obj = {'name': name, "profile_image": display_image, "text": text, 'comment_urn': comment_urn}

                if element.get('replies'):
                    replies = element.get('replies').get('data')
                    obj['next'] = element.get('replies').get('paging',{}).get('next')
                    obj['replies'] = insta_social_actions_data_organizer(replies, headers)

                data.append(obj)
            else:
                obj = {'name': "", "profile_image": "", "text": "", "comment_urn": "", "replies": ""}
                data.append(obj)
    return data


def insta_socialactions(post_urn, access_token, user_id):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    url = f"https://graph.facebook.com/{user_id}?fields=profile_picture_url"

    response = requests.get(url=url, headers=headers)

    profile_picture_url = response.json().get('profile_picture_url')

    url = f"https://graph.facebook.com/{post_urn}?fields=like_count,comments_count"

    response = requests.get(url=url, headers=headers)

    response_json = response.json()

    t_likes = response_json.get("like_count")

    t_comments = response_json.get("comments_count")

    form = Post_urn.objects.get(urn=post_urn)
    form.post_likes = t_likes
    form.post_comments = t_comments
    form.save()

    url = f"https://graph.facebook.com/v17.0/{post_urn}/comments/?fields=from,text,like_count,media,user,replies.order(reverse_chronological).limit(1){{like_count,from,text,user}}&order=reverse_chronological&limit=5"

    response = requests.get(url=url, headers=headers)

    response_json_1 = response.json()

    elements = response_json_1.get("data")
    next = None
    if len(elements) > 0:
        next = response_json_1.get('paging',{}).get('next')
    data = insta_social_actions_data_organizer(elements, headers)

    return t_likes, t_comments, data, profile_picture_url, next

def getUserdata(accountid, access_token):
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

    response = requests.post(url, headers=headers, json=data)

    mediaid = response.json()['id']
    # response.json())

    url = f"https://graph.facebook.com/v17.0/{account_id}/media_publish"

    data = {
        'creation_id': mediaid
    }

    response = requests.post(url, headers=headers, data=data)

    # response.json())

    return redirect("instagram_redirect")


# Facebook Apis


@api_view(['GET'])
def facebookapi(request):
    access_token = request.headers.get('Authorization')
    page_id = request.query_params.get("page_id")
    # access_token)
    # page_id)
    # Get Page Picture

    url = f"https://graph.facebook.com/{page_id}?fields=picture{{url}},about,cover,description,followers_count,new_like_count,country_page_likes,name,fan_count"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    # response.json())
    media = getfacebookmedia(page_id, access_token)
    context = {
        "image": response.json().get("picture").get("data").get("url"),
        "name": response.json().get("name"),
        "followers": response.json().get("followers_count"),
        "likes": response.json().get("fan_count")
    }

    return Response({"account_info": context, "media": media})


def getfacebookmedia(page_id, access_token):
    url = f"https://graph.facebook.com/{page_id}/?fields=published_posts{{full_picture,message,reactions{{type}},comments{{message, comments{{message}}, comment_count}}}}"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

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
        dict['comment_count'] = (_.get("comments").get("data")[0].get("comment_count") + 1) if comments[
            'comment'] else 0
        comments['reply'] = _.get("comments").get("data")[0].get("comments").get("data")[0].get(
            "message") if comments.get("comment") and _.get("comments").get("data")[0].get("comments") else None

        dict['comments'] = comments

        context[i] = dict
        # context[i])
        i = i + 1

    return context


def createfacebookpost(request):
    # "Hello")
    access_token = request.POST.get("p_access_token")
    page_id = request.POST.get("page_id")
    # page_id)
    url = f"https://graph.facebook.com/{page_id}/photos"

    data = {
        "url": "https://images.unsplash.com/photo-1583121274602-3e2820c69888?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1170&q=80",
        "caption": request.POST.get("caption")
    }

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.post(url, headers=headers, json=data)
    # response.json())
    return redirect("facebook_redirect")


def facebook_page_data(accesstoken, userid):
    url = "https://graph.facebook.com/v17.0/me/accounts?fields=access_token,id,name,picture{url}"

    headers = {
        "Authorization": f"Bearer {accesstoken}"
    }

    response = requests.get(url, headers=headers)
    response = response.json().get('data')

    for page in response:
        picture = page.pop('picture')
        page['profile_picture_url'] = picture.get('data').get('url') if picture.get('data') else ''
        page['user'] = userid

    return response


def get_linkedin_user_data(accesstoken,id):
    url = "https://api.linkedin.com/v2/me"

    payload = {}
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Authorization': 'Bearer ' + accesstoken,
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    data = {}
    details = {}

    if response.status_code == 200:
        response = response.json()
        first_name = response['firstName']['localized']['en_US']
        last_name = response['lastName']['localized']['en_US']
        job = response['localizedHeadline']
        name = first_name + "" + last_name
        data['Personal Information'] = [{"Name": name} , {"Job": job}]
        url = "https://api.linkedin.com/v2/clientAwareMemberHandles?q=members&projection=(elements*(primary,type,handle~))"

        headers = {
            'X-Restli-Protocol-Version': '2.0.0',
            'Linkedin-Version': '202304',
            'Authorization': 'Bearer ' + accesstoken,
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code == 200:
            response = response.json()
            if 'elements' in response and isinstance(response['elements'], list) and len(response['elements']) > 0:
                element = response['elements'][0]
                if 'handle~' in element and isinstance(element['handle~'], dict) and 'emailAddress' in element[
                    'handle~']:
                    data['Contact Information'] = [{"Email":element['handle~']['emailAddress'] }]

        url = "https://api.linkedin.com/v2/people/(id:" + id + ")?projection=(id,firstName,lastName,profilePicture(displayImage~:playableStreams))"

        payload = {}
        headers = {
            'LinkedIn-Version': '202304',
            'X-Restli-Protocol-Version': '2.0.0',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + accesstoken,
            'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4546:u=53:x=1:i=1689164560:t=1689211004:v=2:sig=AQFTaVIUWiQvbWucAVvFtIY0AKWyBlpL"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lidc="b=OB01:s=O:r=O:a=O:p=O:g=5300:u=1:x=1:i=1689164320:t=1689250720:v=2:sig=AQG5yzvdOIb42jeJLKgJispG3AzPSMcJ"'
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        response = response.json()
        if 'profilePicture' in response:
            display_image = response['profilePicture']['displayImage~']['elements'][0]['identifiers'][0][
                'identifier']
            details['profile_picture'] = display_image

        details['details'] = data

        return details
    else:
        data = {}

        return data





def get_instagram_user_data(accesstoken, userid):
    url = "https://graph.facebook.com/v17.0/me/accounts?fields=instagram_business_account"

    headers = {
        "Authorization": f"Bearer {accesstoken}"
    }

    response = requests.get(url, headers=headers)
    accounts = []

    for _ in response.json().get('data'):
        if _.get("instagram_business_account"):
            id = _.get("instagram_business_account")["id"]

            try:
                url = f"https://graph.facebook.com/v17.0/{id}?fields=name,profile_picture_url,username"
                response = requests.get(url, headers=headers)
                response = response.json()
                response['user'] = userid
                accounts.append(response)

            except Exception as e:
                # e)
                e

    return accounts


def fb_video_post(data, images, post_model, sharepage):
    # post = {
    #     "url": images[0].image_url,
    #     "caption": post_model.post
    # }
    payload = {
        'description': post_model.post,
    }
    video_path = os.path.join(settings.BASE_DIR, "media/" + str(images[0].image))
    # video_path)

    files = {'source': open(video_path, 'rb')}

    url = f"https://graph-video.facebook.com/v10.0/{data['page_id']}/videos"

    headers = {
        "Authorization": f"Bearer {data['page_access_token']}"
    }

    response = requests.post(url, files=files, data=payload, headers=headers, verify=False)

    # response = requests.post(url, headers=headers, json=post)
    response_data = response.json()

    post_id = response_data.get('id')

    post_urn = Post_urn.objects.create(org=sharepage, urn=post_id)
    post_urn.save()

    post = PostModel.objects.get(id=post_model.id)

    post.post_urn.add(post_urn)
    post.save()


def instagram_post_single_media(page_id, access_token, media, post, page):

    url = f"https://graph.facebook.com/v17.0/{page_id}/media/"
    # url)
    data = {
        "caption": post.post
    }

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    if media[0].image.name.endswith('.mp4'):
        data['video_url'] = media[0].image_url
        data['media_type'] = 'VIDEO'
    else:
        data['image_url'] = media[0].image_url


    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 400:
        post.status = 'FAILED'
        post.save()
        return

    try:
        mediaid = response.json().get('id')
        if mediaid is None:
            raise KeyError
    except KeyError:
        post.status = 'FAILED'
        post.save()
        return
    # "media id is",mediaid,response.json())

    if data.get('media_type') == 'VIDEO':
        while True:
            # "Waiting for 10s till the media is created"
            time.sleep(10)
            check_url = f"https://graph.facebook.com/v17.0/{mediaid}?fields=status_code,status,id"

            response = requests.request("GET", url=check_url, headers=headers)
            status = response.json().get("status_code")

            if status == "FINISHED":
                break
            elif status == "ERROR" or status == "FATAL":
                post.status = 'FAILED'
                post.save()
                return
            else:
                pass

    url = f"https://graph.facebook.com/v17.0/{page_id}/media_publish"

    data = {
        'creation_id': mediaid
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        response = response.json()
        post_id = response.get('id')
        # "Post id is ",post_id,response)
        post_urn = Post_urn.objects.create(org=page, urn=post_id)
        post_urn.save()
        post.post_urn.add(post_urn)
        # "Post Successfull Created"
        post.published_at = timezone.now()
        if post.status == 'SCHEDULED' or post.status == 'DRAFT' or post.status == 'PROCESSING':
            post.status = 'PUBLISHED'
            post.publish_check = True
        post.save()

    else:
        post.status = 'FAILED'
        post.save()


def linkdein(access_token_string):
    url = "https://api.linkedin.com/v2/organizationalEntityAcls?q=roleAssignee"

    payload = {}
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Authorization': 'Bearer ' + access_token_string,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4543:u=51:x=1:i=1688454620:t=1688474844:v=2:sig=AQEPLNOkmN73V6fYvS7fD8W9CViGJ3hF"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lang=v=2&lang=en-us'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    response = response.json()
    targets = [element['organizationalTarget'] for element in response['elements']]
    data = targets
    ids = [item.split(':')[-1] for item in data]

    id = ','.join(ids)

    url = f"https://api.linkedin.com/v2/organizations?ids=List({id})"

    payload = {}
    headers = {
        'LinkedIn-Version': '202304',
        'X-Restli-Protocol-Version': '2.0.0',
        'Authorization': 'Bearer ' + access_token_string,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4543:u=51:x=1:i=1688456448:t=1688474844:v=2:sig=AQGzRecgKiUECgv05uH2KHFxISD6bd_d"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4543:u=51:x=1:i=1688398890:t=1688474844:v=2:sig=AQHKhaANXQC9mWny3X46qeX8AAsrtxOQ"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lang=v=2&lang=en-us'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    response = response.json()


def save_image_from_url(image_url):
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    image = image.convert('RGB')
    image_buffer = BytesIO()
    image.save(image_buffer, format='JPEG', optimize=True, quality=85)
    image_buffer.seek(0)

    content_file = ContentFile(image_buffer.getvalue())

    return content_file


def get_file_extension(content_type):
    mime_to_extension = {
        'image/jpeg': 'jpg',  # JPEG image
        'image/png': 'png',  # PNG image
        'image/gif': 'gif',  # GIF image
        'video/mp4': 'mp4',  # MP4 video

    }

    return mime_to_extension.get(content_type, 'unknown')


def getmediaid(image, data, post):
    url = f"https://graph.facebook.com/{data['page_id']}/photos?published=false&temporary=true"

    headers = {
        "Authorization": f"Bearer {data['page_access_token']}"
    }

    data = {
        "url": image.image_url
    }

    response = requests.post(url, headers=headers, data=data)
    return response.json()


def create_fb_post(page_id, access_token, media, post, sharepage):
    data = {
        'page_id': page_id,
        'page_access_token': access_token
    }
    if media:
        result = clean_file(media)
        update_images = result[1]
        video = result[0]
        if video != None:
            video = media
            facebook_post_video(data, video, post, sharepage)
        else:
            images = update_images
            facebook_post_multiimage(data, images, post, sharepage)

    else:
        facebook_post_multiimage(data, [], post, sharepage)


def facebook_post_multiimage(data, images, post, sharepage):
    url = f"https://graph.facebook.com/{data['page_id']}/feed"
    data_post = {
        "message": post.post
    }
    headers = {
        "Authorization": f"Bearer {data['page_access_token']}"
    }
    # i = 0
    if len(images) != 0:
        for _ in range(len(images)):
            try:
                response_id = getmediaid(images[_], data, post).get("id")
                if response_id is None:
                    raise KeyError
            except KeyError:
                post.status = 'FAILED'
                post.save()
                return
            images[_].image_posted = response_id
            images[_].save()
            data_post[f"attached_media[{_}]"] = f'{{"media_fbid": "{response_id}"}}'


    response = requests.post(url, headers=headers, data=data_post)


    if response.status_code == 200:

        response = response.json()

        try:
            post_id = response.get("id")
            if post_id is None:
                raise KeyError
        except KeyError:
            post.status = 'FAILED'
            post.save()
            return

        # post_id
        post_urn = Post_urn.objects.create(org=sharepage, urn=post_id)
        post_urn.save()
        post.post_urn.add(post_urn)
        post.published_at = timezone.now()
        if post.status in ['SCHEDULED', 'DRAFT', 'PROCESSING']:
            post.status = 'PUBLISHED'
            post.publish_check = True
        post.save()
    else:
        post.status = 'FAILED'
        post.save()


def create_insta_post(page_id, access_token, media, post, page):
    if media:
        if len(media) > 1:

            instagram_multi_media(page_id, access_token, media, post, page)
        else:
            instagram_post_single_media(page_id, access_token, media, post, page)
    else:
        post.status = 'FAILED'
        post.save()
        return


def facebook_post_video(data, video, post, sharepage):
    page_id = data['page_id']

    url = f"https://graph.facebook.com/{page_id}/videos"
    headers = {
        "Authorization": f"Bearer {data['page_access_token']}"
    }
    data_post = {
        'description': post.post
    }
    if len(video) != 0:
        data_post['file_url'] = video[0].image_url
    response = requests.post(url, headers=headers, data=data_post)
    if response.status_code == 200:

        response = response.json()

        try:
            post_id = response.get('id')
            if post_id is None:
                raise KeyError
        except KeyError:
            post.status = 'FAILED'
            post.save()
            return

        post_urn = Post_urn.objects.create(org=sharepage, urn=post_id)
        post_urn.save()

        post.post_urn.add(post_urn)
        post.published_at = timezone.now()

        if post.status == 'SCHEDULED' or post.status == 'DRAFT' or post.status == 'PROCESSING':
            post.status = 'PUBLISHED'
            post.publish_check = True
        post.save()
    else:
        post.status = 'FAILED'
        post.save()


def get_instagram_image_id(image, page_id, access_token):
    url = f"https://graph.facebook.com/v17.0/{page_id}/media?is_carousel_item=true"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    data_post = {
        "image_url": image.image_url
    }

    # data_post = {
    #     "image_url":"https://messangel.caansoft.com/uploads/social_prefrences/image/1691750723366-homepage-seen-computer-screen_CvuwFmi.jpg"
    # }

    response = requests.post(url, headers=headers, data=data_post)
    # response.json())
    return response.json()


def get_instagram_video_id(video, page_id, access_token):
    url = f"https://graph.facebook.com/v17.0/{page_id}/media?is_carousel_item=true"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    data_post = {
        'video_url': {video.image_url},
        'media_type': 'VIDEO',
    }
    # data_post)
    # data_post = {
    #     'video_url':"https://messangel.caansoft.com/uploads/social_prefrences/video/1691750720923-send_WqThsJC.mp4",
    #     'media_type':'VIDEO',
    # }

    response = requests.post(url, headers=headers, data=data_post)
    # response.json())
    return response.json()


def get_instagram_media_id(data_post, headers, page_id):
    # "Getting Media id")
    url = f"https://graph.facebook.com/v17.0/{page_id}/media?media_type=CAROUSEL"

    response = requests.request("POST", url, headers=headers, data=data_post)

    if response.json().get('id'):
        return response
    else:
        # response.json())
        # "Sleeping For 30s till data arrive")
        time.sleep(30)
        response = get_instagram_media_id(data_post, headers, page_id)

    return response


def instagram_multi_media(page_id, access_token, media, post, page):
    is_video = False
    childern_list = []
    for image in media:
        childern_id = None
        if image.image.name.endswith('.mp4'):
            try:
                childern_id = get_instagram_video_id(image, page_id, access_token).get('id')
                is_video = True
                if childern_id is None:
                    raise KeyError
            except KeyError:
                post.status = 'FAILED'
                post.save()
                return
        else:
            try:
                childern_id = get_instagram_image_id(image, page_id, access_token).get('id')

                if childern_id is None:
                    raise KeyError
            except KeyError:
                post.status = 'FAILED'
                post.save()
                return

        childern_list.append(childern_id)

    headers = {
        "Authorization": f"Bearer {access_token}",
        'Content-Type': 'application/json',
    }
    data_post = json.dumps({
        "caption": post.post,
        "children": ",".join(childern_list)
    })
    # data_post)

    media_id = get_instagram_media_id(data_post, headers, page_id).json().get('id')
    if media_id is None:
        post.status = 'FAILED'
        post.save()
        return

    # media_id)
    if is_video:
        while True:
            # "Waiting for 10s till the media is created")
            time.sleep(10)
            check_url = f"https://graph.facebook.com/v17.0/{media_id}?fields=status_code,status,id"

            response = requests.request("GET", url=check_url, headers=headers)
            # response.json())
            status = response.json().get("status_code")
            # status)
            if status == "FINISHED":
                break
            elif status == "ERROR" or status == "FATAL":
                post.status = 'FAILED'
                post.save()
                return
            else:
                pass

    url_2 = f"https://graph.facebook.com/v17.0/{page_id}/media_publish"

    data_post_2 = {
        "creation_id": media_id
    }

    response_2 = requests.post(url_2, headers=headers, data=data_post_2)
    if response_2.status_code == 200:
        response_2 = response_2.json()
        post_id = response_2.get('id')
        post_urn = Post_urn.objects.create(org=page, urn=post_id)
        post_urn.save()
        post.post_urn.add(post_urn)
        post.published_at = timezone.now()
        if post.status == 'SCHEDULED' or post.status == 'DRAFT' or post.status == 'PROCESSING':
            post.status = 'PUBLISHED'
            post.publish_check = True
        post.save()
    else:
        post.status = 'FAILED'
        post.save()


def create_l_multimedia(images, org_id, access_token_string, clean_file,
                        get_video_urn, image_m, upload_video, post_video_linkedin,
                        org, get_img_urn, upload_img, post_single_image_linkedin,
                        post, post_linkedin):
    if images:
        result = clean_file(images)
        video_file = result[0]
        updated_image_list = result[1]

        if video_file != None:
            response = get_video_urn(org_id, access_token_string)
            if response.status_code == 200:
                response_json = response.json()
                image_urn = response_json['value']['asset']
                upload_url = \
                    response_json['value']['uploadMechanism'][
                        'com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest'][
                        'uploadUrl']
                for a in image_m.images.all():
                    a.image_urn = image_urn
                    a.save()

                response = upload_video(upload_url, video_file)
                if response.status_code == 201:
                    response = post_video_linkedin(image_urn, access_token_string, org_id, post)
                    if response.status_code == 201:
                        post_id_value = response.headers.get('x-restli-id')
                        post_urn, created = Post_urn.objects.get_or_create(org=org, urn=post_id_value)
                        if created:
                            post_urn.urn = post_id_value
                            post_urn.org = org
                            post_urn.save()
                        post.post_urn.add(post_urn)
                        post.published_at = timezone.now()
                        if post.status == 'SCHEDULED' or post.status == 'DRAFT' or post.status == 'PROCESSING':
                            post.status = 'PUBLISHED'
                            post.publish_check = True

                        post.save()
                        # "Video Posted successfully.")
                    else:
                        post.status = 'FAILED'
                        post.save()
                    # else:
                    # "Post Failed" + response.status_code)

            else:
                pass

                # "Video did not Register")

        if len(updated_image_list) != 0:
            image_list = []

            for a in image_m.images.all():
                if not a.is_mp4_file():
                    image_file = a.image
                    response = get_img_urn(org_id, access_token_string)
                    if response.status_code == 200:
                        response_json = response.json()
                        upload_url = response_json['value']['uploadUrl']
                        image_urn = response_json['value']['image']
                        a.image_urn = image_urn
                        a.save()
                        image_list.append({'id': image_urn, 'altText': 'test'})

                        response = upload_img(upload_url, image_file, access_token_string)
                        # if response.status_code == 201:
                        #     "Image successfully uploaded to LinkedIn.")

            count = 0
            for image in image_list:
                # image)
                if 'id' in image:
                    count += 1

            if count < 2:
                image_list = image_list[0]
                response = post_single_image_linkedin(access_token_string, org_id, post, image_list)
                # "Response ", response.json())
                if response.status_code == 201:

                    post_id_value = response.headers.get('x-restli-id')
                    post_urn, created = Post_urn.objects.get_or_create(org=org, urn=post_id_value)
                    if created:
                        post_urn.urn = post_id_value
                        post_urn.org = org
                        post_urn.save()
                    post.post_urn.add(post_urn)
                    post.published_at = timezone.now()
                    if post.status == 'SCHEDULED' or post.status == 'DRAFT' or post.status == 'PROCESSING':
                        post.status = 'PUBLISHED'
                        post.publish_check = True

                    post.save()
                    # "Video Posted successfully.")
                else:
                    post.status = 'FAILED'
                    post.save()

            else:
                response = post_linkedin(image_list, post, org_id, access_token_string)
                if response.status_code == 201:

                    post_id_value = response.headers.get('x-restli-id')
                    post_urn, created = Post_urn.objects.get_or_create(org=org, urn=post_id_value)
                    if created:
                        post_urn.urn = post_id_value
                        post_urn.org = org
                        post_urn.save()
                    post.post_urn.add(post_urn)
                    post.published_at = timezone.now()
                    if post.status == 'SCHEDULED' or post.status == 'DRAFT' or post.status == 'PROCESSING':
                        post.status = 'PUBLISHED'
                        post.publish_check = True

                    post.save()
                    # "Video Posted successfully.")
                else:
                    post.status = 'FAILED'
                    post.save()
    else:
        response = text_post_linkedin(post, access_token_string, org_id)
        if response.status_code == 201:
            post_id_value = response.headers.get('x-restli-id')
            post_urn, created = Post_urn.objects.get_or_create(org=org, urn=post_id_value)
            if created:
                post_urn.urn = post_id_value
                post_urn.org = org
                post_urn.save()
            post.post_urn.add(post_urn)
            post.published_at = timezone.now()
            if post.status == 'SCHEDULED' or post.status == 'DRAFT' or post.status == 'PROCESSING':
                post.status = 'PUBLISHED'
                post.publish_check = True

            post.save()
            # "Video Posted successfully.")
        else:
            post.status = 'FAILED'
            post.save()

def post_nested_comment_linkedin(social, access_token, post_urn, reply, comment_urn):
    user = social.uid
    encoded_urn = quote(comment_urn, safe='')
    url = "https://api.linkedin.com/rest/socialActions/" + encoded_urn + "/comments"

    payload = json.dumps({
        "actor": "urn:li:person:" + user,
        "message": {
            "text": reply
        },
        "object": post_urn,
        "parentComment": comment_urn
    })
    headers = {
        'Linkedin-Version': '202304',
        'X-Restli-Protocol-Version': '2.0.0',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4552:u=55:x=1:i=1689679535:t=1689752271:v=2:sig=AQHrXpQbD6C1r_eMUoL9o6xmwpPa1AEs"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4546:u=55:x=1:i=1689314606:t=1689334414:v=2:sig=AQHSFW1fjeXULNO8CiDc8_rZkoMXJMK3"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"'
    }
    comment_response = dict()
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 201:
        response2 = response.json()
        actor = response2['created']['actor']
        prefix, value = actor.rsplit(':', 1)
        if prefix == 'urn:li:organization':
            url = "https://api.linkedin.com/v2/organizations/" + value + "?projection=(localizedName,logoV2(original~:playableStreams))"

            payload = {}
            headers = {
                'Linkedin-Version': '202304',
                'X-Restli-Protocol-Version': '2.0.0',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + access_token,
                'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4551:u=55:x=1:i=1689588794:t=1689613491:v=2:sig=AQEuUJEbIsk57LyEy9HwFJQrEu7ayH9n"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4551:u=55:x=1:i=1689587318:t=1689613491:v=2:sig=AQGp8c3I7u6ZkNJN7oSt0OLu8JRVv3WX"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lidc="b=TB01:s=T:r=T:a=T:p=T:g=5807:u=1:x=1:i=1689586527:t=1689672927:v=2:sig=AQFFnf4QlGIIpq60wKa97GoDCwxO3u-D"'
            }

            response = requests.request("GET", url, headers=headers, data=payload)
            response = response.json()
            name = response['localizedName']
        else:
            url = "https://api.linkedin.com/v2/people/(id:" + value + ")?projection=(id,firstName,lastName,profilePicture(displayImage~:playableStreams))"

            payload = {}
            headers = {
                'LinkedIn-Version': '202304',
                'X-Restli-Protocol-Version': '2.0.0',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + access_token,
                'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4546:u=53:x=1:i=1689164560:t=1689211004:v=2:sig=AQFTaVIUWiQvbWucAVvFtIY0AKWyBlpL"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lidc="b=OB01:s=O:r=O:a=O:p=O:g=5300:u=1:x=1:i=1689164320:t=1689250720:v=2:sig=AQG5yzvdOIb42jeJLKgJispG3AzPSMcJ"'
            }

            response = requests.request("GET", url, headers=headers, data=payload)
            response = response.json()

            name = response['firstName']["localized"]['en_US'] + " " + response['lastName']["localized"]['en_US']

        comment_response['name'] = name
        comment_response['user_id'] = response2['actor']
        # comment_response['created_time'] = response2['created_time']
        comment_response['text'] = response2['message']['text']
        comment_response['comment_urn'] = response2['$URN']
        comment_response['comment_id'] = response2['id']

        try:
            comment_response['profile_image'] = response['profilePicture']['displayImage~']['elements'][3]['identifiers'][0]['identifier']
        except Exception as e:
            e

        #
        return comment_response
    else:
        return "error"




def post_nested_comment_media_linkedin(social, access_token, post_urn, reply, comment_urn, media, org_id):
    access_token_string = access_token
    response = get_img_urn(org_id, access_token_string)
    if response.status_code == 200:
        response_json = response.json()
        upload_url = response_json['value']['uploadUrl']
        image_urn = response_json['value']['image']
        image_url = get_image_url(media)
        image_path = image_url.get('files')[0].get('path')
        image_model = ImageModel(image=media, image_url=image_path, image_urn=image_urn)
        image_model.save()
        image_file = image_model.image
        response = upload_img(upload_url, image_file, access_token_string)
        # if response.status_code == 201:
        #     # "Media succesfully uploaded")
        #
        # else:
        #     # "Media Upload Failed")

        user = social.uid
        encoded_urn = quote(comment_urn, safe='')

        url = "https://api.linkedin.com/rest/socialActions/" + encoded_urn + "/comments"
        payload = json.dumps({
            "actor": "urn:li:person:" + user,
            "message": {
                "text": reply
            },
            "object": post_urn,
            "parentComment": comment_urn,
            "content": [
                {
                    "entity": {
                        "image": image_urn
                    },
                    "type": "IMAGE",
                    "url": image_path
                }
            ]
        })
        headers = {
            'Linkedin-Version': '202304',
            'X-Restli-Protocol-Version': '2.0.0',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4552:u=55:x=1:i=1689679535:t=1689752271:v=2:sig=AQHrXpQbD6C1r_eMUoL9o6xmwpPa1AEs"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4546:u=55:x=1:i=1689314606:t=1689334414:v=2:sig=AQHSFW1fjeXULNO8CiDc8_rZkoMXJMK3"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 201:
            response = response.json()
            # "Replied to Comment successfully.")
        # else:
        #     "Failed to reply.")

        return response

def ugcpost_socialactions_nested_comments_data_orgainzer(elements,access_token):
    replies = []
    if len(elements) > 0:
        for element in elements:
            urls = []
            if 'content' in element:
                for content in element['content']:
                    if 'url' in content:
                        urls.append(content['url'])
            if 'likesSummary' in element:
                liked = element['likesSummary']['likedByCurrentUser']
            else:
                liked = None
            text = element['message']['text']
            actor = element['actor']
            comment_urn = element['$URN']
            comment_id = element['id']
            prefix, value = actor.rsplit(':', 1)
            if prefix == 'urn:li:organization':
                url = "https://api.linkedin.com/v2/organizations/" + value + "?projection=(localizedName,logoV2(original~:playableStreams))"

                payload = {}
                headers = {
                    'Linkedin-Version': '202304',
                    'X-Restli-Protocol-Version': '2.0.0',
                    'Authorization': 'Bearer ' + access_token,
                    'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4551:u=55:x=1:i=1689588794:t=1689613491:v=2:sig=AQEuUJEbIsk57LyEy9HwFJQrEu7ayH9n"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4551:u=55:x=1:i=1689587318:t=1689613491:v=2:sig=AQGp8c3I7u6ZkNJN7oSt0OLu8JRVv3WX"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lidc="b=TB01:s=T:r=T:a=T:p=T:g=5807:u=1:x=1:i=1689586527:t=1689672927:v=2:sig=AQFFnf4QlGIIpq60wKa97GoDCwxO3u-D"'
                }

                response = requests.request("GET", url, headers=headers, data=payload)
                response = response.json()
                if 'logoV2' in response:
                    display_image = response['logoV2']['original~']['elements'][0]['identifiers'][0]['identifier']
                else:
                    display_image = ''
                name = response['localizedName']
                obj = {'name': name, "profile_image": display_image, "text": text, "comment_urn": comment_urn,
                       "urls": urls, 'liked': liked, 'user_id': actor, 'comment_id': comment_id}
                replies.append(obj)
            else:
                url = "https://api.linkedin.com/v2/people/(id:" + value + ")?projection=(id,firstName,lastName,profilePicture(displayImage~:playableStreams))"

                payload = {}
                headers = {
                    'LinkedIn-Version': '202304',
                    'X-Restli-Protocol-Version': '2.0.0',
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + access_token,
                    'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4546:u=53:x=1:i=1689164560:t=1689211004:v=2:sig=AQFTaVIUWiQvbWucAVvFtIY0AKWyBlpL"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lidc="b=OB01:s=O:r=O:a=O:p=O:g=5300:u=1:x=1:i=1689164320:t=1689250720:v=2:sig=AQG5yzvdOIb42jeJLKgJispG3AzPSMcJ"'
                }

                response = requests.request("GET", url, headers=headers, data=payload)
                response = response.json()
                if 'profilePicture' in response:
                    display_image = response['profilePicture']['displayImage~']['elements'][0]['identifiers'][0][
                        'identifier']
                else:
                    display_image = ''
                name = response['firstName']['localized']['en_US'] + " " + response['lastName']['localized'][
                    'en_US']

                obj = {'name': name, "profile_image": display_image, "text": text, "comment_urn": comment_urn,
                       "urls": urls, 'liked': liked, 'user_id': actor, 'comment_id': comment_id}
                replies.append(obj)
    else:
        # "No Replies on Comments")
        replies = []
    return replies


def get_nested_comments(access_token, comment_urn):
    encoded_urn = quote(comment_urn, safe='')
    url = "https://api.linkedin.com/rest/socialActions/" + encoded_urn + "/comments?start=0&count=1"
    payload = {}
    headers = {
        'Linkedin-Version': '202304',
        'X-Restli-Protocol-Version': '2.0.0',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4552:u=55:x=1:i=1689679535:t=1689752271:v=2:sig=AQHrXpQbD6C1r_eMUoL9o6xmwpPa1AEs"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4546:u=55:x=1:i=1689314606:t=1689334414:v=2:sig=AQHSFW1fjeXULNO8CiDc8_rZkoMXJMK3"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"'
    }
    replies = []
    next = None
    response = requests.request("GET", url, headers=headers, data=payload)
    if response.status_code == 200:
        response = response.json()
        elements = response['elements']

        replies = ugcpost_socialactions_nested_comments_data_orgainzer(elements,access_token)

        link = response.get('paging', {}).get("links")
        if link and len(link) > 0:
            for l in link:
                if l.get('rel') == "next":
                    next = l.get('href')
    else:
        # "Fetching Replies Failed")
        pass
    return replies , next


def create_comment_media_linkedin(org_id, access_token, post_urn, comment, social, media):
    user = social.uid
    encoded_urn = quote(post_urn, safe='')
    access_token_string = access_token
    response = get_img_urn(org_id, access_token_string)
    if response.status_code == 200:
        response_json = response.json()
        upload_url = response_json['value']['uploadUrl']
        image_urn = response_json['value']['image']
        # upload_url)
        image_url = get_image_url(media)
        image_path = image_url.get('files')[0].get('path')
        image_model = ImageModel(image=media, image_url=image_path, image_urn=image_urn)
        image_model.save()
        image_file = image_model.image
        response = upload_img(upload_url, image_file, access_token_string)
        # if response.status_code == 201:
        #     "Media succesfully uploaded")
        #
        # else:
        #     "Media Upload Failed")
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0',
        'LinkedIn-Version': '202304',
    }
    url = f'https://api.linkedin.com/rest/socialActions/' + encoded_urn + '/comments'

    data = {
        "actor": "urn:li:person:" + user,
        "object": post_urn,
        "message": {
            "text": comment
        },
        "content": [
            {
                "entity": {
                    "image": image_urn
                },
                "type": "IMAGE",
                "url": image_path
            }
        ]

    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        response = response.json()
        # "Comment created successfully.")
        # response)
    # else:
    # "Failed to create comment.")
    # response.json())
    return response


def image_comment(org_id, access_token, post_urn, comment, social, media):
    access_token_string = access_token
    user = social.uid
    encoded_urn = quote(post_urn, safe='')

    url = "https://api.linkedin.com/rest/assets?action=registerUpload"

    payload = json.dumps({
        "registerUploadRequest": {
            "owner": "urn:li:organization:" + org_id,
            "recipes": [
                "urn:li:digitalmediaRecipe:feedshare-image"
            ],
            "serviceRelationships": [
                {
                    "identifier": "urn:li:userGeneratedContent",
                    "relationshipType": "OWNER"
                }
            ],
            "supportedUploadMechanism": [
                "SYNCHRONOUS_UPLOAD"
            ]
        }
    })
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Authorization': 'Bearer ' + access_token,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4570:u=70:x=1:i=1692093475:t=1692172409:v=2:sig=AQHvqY4B7PQyhaJ3i0Jha9CnZNHz3aPN"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    data = response.json()
    # data)
    asset = data["value"]["asset"]
    upload_url = data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"][
        "uploadUrl"]

    url = upload_url
    # Set the path to the imaganasrehman/Pyce file on your local machine
    image_url = get_image_url(media)
    image_path = image_url.get('files')[0].get('path')
    image_model = ImageModel(image=media, image_url=image_path, image_urn=asset)
    image_model.save()
    image_file = image_model.image

    image_path = os.path.join(settings.BASE_DIR, "media/" + str(image_file))

    input_path = image_path
    output_path = input_path
    max_pixels = 36152320  # Maximum pixel count (e.g., 1920x1080)

    reduce_pixel_count(input_path, output_path, max_pixels)

    headers = {
        "Authorization": f"Bearer {access_token_string}",
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
    }

    # Open the image file in binary mode and send it as the request body
    with open(output_path, "rb") as file:
        response = requests.request("PUT", url, headers=headers, data=file)
        # if response.status_code == 201:
        #         response)
        #         "Media succesfully uploaded")
        #
        # else:
        #         "Media Upload Failed")

    parts = asset.split(':')
    asset_id = parts[-1]
    post_url = url = f'https://api.linkedin.com/rest/socialActions/' + encoded_urn + '/comments'
    post_data = json.dumps({
        "actor": f"urn:li:person:" + user,
        "object": post_urn,
        "message": {
            "text": comment
        },
        "content": [
            {
                "entity": {
                    "image": 'urn:li:image:' + asset_id
                },
                "type": "IMAGE",
                "url": image_path
            }
        ]
    })
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0',
        'LinkedIn-Version': '202304',
    }

    response = requests.post(post_url, headers=headers, data=post_data)
    if response.status_code == 201:
        response = response.json()
        # "Comment created successfully.")
        # response['$URN'])
        # response)
    # else:
    #     "Failed to create comment.")
    #     response.json())
    return response


def get_reaction_linkedin_post(social, post_urn, access_token_string):
    encoded_urn = quote(post_urn, safe='')
    url = "https://api.linkedin.com/rest/reactions/(actor:urn%3Ali%3Aperson%3A" + social.uid + ",entity:" + encoded_urn + ")"

    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + access_token_string,
    }

    response = requests.request("GET", url, headers=headers)
    if response.status_code == 200:
        liked = True
        return liked
    else:
        liked = False
        return liked


def create_comment(access_token, post_urn, comment, social):
    user = social.uid
    encoded_urn = quote(post_urn, safe='')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0',
        'LinkedIn-Version': '202304',
    }

    url = f'https://api.linkedin.com/rest/socialActions/' + encoded_urn + '/comments'
    data = {
        "actor": "urn:li:person:" + user,
        "object": post_urn,
        "message": {
            "text": comment
        },
    }

    response = requests.post(url, headers=headers, json=data)
    comment_response = dict()
    if response.status_code == 201:
        response2 = response.json()

        actor = response2['created']['actor']
        prefix, value = actor.rsplit(':', 1)
        if prefix == 'urn:li:organization':
            url = "https://api.linkedin.com/v2/organizations/" + value + "?projection=(localizedName,logoV2(original~:playableStreams))"

            payload = {}
            headers = {
                'Linkedin-Version': '202304',
                'X-Restli-Protocol-Version': '2.0.0',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + access_token,
                'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4551:u=55:x=1:i=1689588794:t=1689613491:v=2:sig=AQEuUJEbIsk57LyEy9HwFJQrEu7ayH9n"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4551:u=55:x=1:i=1689587318:t=1689613491:v=2:sig=AQGp8c3I7u6ZkNJN7oSt0OLu8JRVv3WX"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lidc="b=TB01:s=T:r=T:a=T:p=T:g=5807:u=1:x=1:i=1689586527:t=1689672927:v=2:sig=AQFFnf4QlGIIpq60wKa97GoDCwxO3u-D"'
            }

            response = requests.request("GET", url, headers=headers, data=payload)
            response = response.json()
            name = response['localizedName']
        else:
            url = "https://api.linkedin.com/v2/people/(id:" + value + ")?projection=(id,firstName,lastName,profilePicture(displayImage~:playableStreams))"

            payload = {}
            headers = {
                'LinkedIn-Version': '202304',
                'X-Restli-Protocol-Version': '2.0.0',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + access_token,
                'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4546:u=53:x=1:i=1689164560:t=1689211004:v=2:sig=AQFTaVIUWiQvbWucAVvFtIY0AKWyBlpL"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lidc="b=OB01:s=O:r=O:a=O:p=O:g=5300:u=1:x=1:i=1689164320:t=1689250720:v=2:sig=AQG5yzvdOIb42jeJLKgJispG3AzPSMcJ"'
            }

            response = requests.request("GET", url, headers=headers, data=payload)
            response = response.json()

            name = response['firstName']["localized"]['en_US'] + " " + response['lastName']["localized"]['en_US']


        comment_response['name'] = name
        comment_response['user_id'] = response2['actor']
        # comment_response['created_time'] = response2['created_time']
        comment_response['text'] = response2['message']['text']
        comment_response['comment_urn'] = response2['$URN']
        comment_response['comment_id'] = response2['id']

        try:
            comment_response['profile_image'] = response['profilePicture']['displayImage~']['elements'][3]['identifiers'][0]['identifier']
        except Exception as e:
            e



        # "Comment created successfully.")
        # response['$URN'])
    # else:
    #     "Failed to create comment.")
    #     response.json())
        return comment_response
    else:
        return "error"


def ugcpost_socialactions_comment_data_organizer(elements,access_token_string):
    data = []
    next = None
    for element in elements:
        urls = []
        if 'content' in element:
            for content in element['content']:
                if 'url' in content:
                    urls.append(content['url'])
        actor = element.get('actor')
        comment_urn = element.get('$URN')
        comment_id = element.get('id')
        if 'likesSummary' in element:
            liked = element['likesSummary']['likedByCurrentUser']
        else:
            liked = None
        if comment_urn:
            result = get_nested_comments(access_token_string, comment_urn)
            replies = result[0]
            next = result[1]

        else:
            replies = None
        texts = element.get('message', {}).get('text')
        if elements and len(elements) > 0:
            prefix, value = actor.rsplit(':', 1)
            if prefix == 'urn:li:organization':
                url = "https://api.linkedin.com/v2/organizations/" + value + "?projection=(localizedName,logoV2(original~:playableStreams))"

                payload = {}
                headers = {
                    'Linkedin-Version': '202304',
                    'X-Restli-Protocol-Version': '2.0.0',
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + access_token_string,
                    'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4551:u=55:x=1:i=1689588794:t=1689613491:v=2:sig=AQEuUJEbIsk57LyEy9HwFJQrEu7ayH9n"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4551:u=55:x=1:i=1689587318:t=1689613491:v=2:sig=AQGp8c3I7u6ZkNJN7oSt0OLu8JRVv3WX"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lidc="b=TB01:s=T:r=T:a=T:p=T:g=5807:u=1:x=1:i=1689586527:t=1689672927:v=2:sig=AQFFnf4QlGIIpq60wKa97GoDCwxO3u-D"'
                }

                response = requests.request("GET", url, headers=headers, data=payload)
                response = response.json()
                if 'logoV2' in response:
                    display_image = response['logoV2']['original~']['elements'][0]['identifiers'][0]['identifier']
                else:
                    display_image = ''
                name = response['localizedName']
                obj = {'name': name, "profile_image": display_image, "text": texts, "urls": urls,
                       "comment_urn": comment_urn, 'liked': liked, "comment_id": comment_id, "user_id": actor}
                obj['replies'] = replies
                obj['next'] = next

                data.append(obj)
            else:
                url = "https://api.linkedin.com/v2/people/(id:" + value + ")?projection=(id,firstName,lastName,profilePicture(displayImage~:playableStreams))"

                payload = {}
                headers = {
                    'LinkedIn-Version': '202304',
                    'X-Restli-Protocol-Version': '2.0.0',
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + access_token_string,
                    'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4546:u=53:x=1:i=1689164560:t=1689211004:v=2:sig=AQFTaVIUWiQvbWucAVvFtIY0AKWyBlpL"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lidc="b=OB01:s=O:r=O:a=O:p=O:g=5300:u=1:x=1:i=1689164320:t=1689250720:v=2:sig=AQG5yzvdOIb42jeJLKgJispG3AzPSMcJ"'
                }

                response = requests.request("GET", url, headers=headers, data=payload)
                response = response.json()
                if 'profilePicture' in response:
                    display_image = response['profilePicture']['displayImage~']['elements'][0]['identifiers'][0][
                        'identifier']
                else:
                    display_image = ''
                name = response['firstName']['localized']['en_US'] + " " + response['lastName']['localized'][
                    'en_US']

                obj = {'name': name, "profile_image": display_image, "text": texts, "urls": urls,
                       "comment_urn": comment_urn, 'liked': liked, "comment_id": comment_id, "user_id": actor}
                obj['replies'] = replies
                obj['next'] = next
                data.append(obj)
        else:
            obj = {'name': "", "profile_image": "", "text": "", "urls": urls, "comment_urn": "", 'liked': False,
                   "comment_id": "", "user_id": ""}
            replies = None
            obj['replies'] = replies
            obj['next'] = next
            data.append(obj)
    return data



def ugcpost_socialactions(urn, access_token_string, linkedin_post):
    access_token = access_token_string
    encoded_urn = quote(urn, safe='')
    url = "https://api.linkedin.com/v2/socialActions/" + encoded_urn

    payload = {}
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'LinkedIn-Version': '202304',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Bearer ' + access_token_string,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4514:u=51:x=1:i=1687620040:t=1687696419:v=2:sig=AQFLXWHSfe752c-owR1S3P8Q_frEVh6e"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4514:u=51:x=1:i=1687595585:t=1687608928:v=2:sig=AQH0H7FjSwSsdlmZsw6uhsFDCp1ROKX8"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    response_json = response.json()

    t_likes = response_json['likesSummary']['aggregatedTotalLikes']
    t_comments = response_json['commentsSummary']['aggregatedTotalComments']
    form = Post_urn.objects.get(urn=urn)
    form.post_likes = t_likes
    form.post_comments = t_comments
    form.save()
    next = None
    if linkedin_post.comment_check:
        url = "https://api.linkedin.com/v2/socialActions/" + encoded_urn + "/comments?start=0&count=5"

        payload = {}
        headers = {
            'LinkedIn-Version': '202304',
            'X-Restli-Protocol-Version': '2.0.0',
            'Authorization': 'Bearer ' + access_token_string,
            'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4543:u=51:x=1:i=1688402283:t=1688474844:v=2:sig=AQEpkxXWxp7LRP7Mi5vt8y1DzvizD74p"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4543:u=51:x=1:i=1688402184:t=1688474844:v=2:sig=AQEe56HhN4GzpbcINCOFmpXb-L-mvjpK"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4543:u=51:x=1:i=1688399773:t=1688474844:v=2:sig=AQFdvDMS2NMzPLvL9rDALkiyQv6etADT"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lang=v=2&lang=en-us'
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        response_json3 = response.json()
        link = response_json3.get('paging',{}).get("links")
        if link and len(link) > 0:
            for l in link:
                if l.get('rel') == "next":
                    next = l.get('href')



        elements = response_json3.get('elements')
        data = ugcpost_socialactions_comment_data_organizer(elements,access_token_string)
        return t_likes, t_comments, data, next
    else:
        data = []
        obj = {}
        data.append(obj)
    return t_likes, t_comments, data, next







def linkedin_post_socialactions(urn, access_token_string, linkedin_post):
    encoded_urn = quote(urn, safe='')
    access_token = access_token_string
    url = "https://api.linkedin.com/rest/socialActions/" + encoded_urn

    payload = {}
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'LinkedIn-Version': '202304',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Bearer ' + access_token_string,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4514:u=51:x=1:i=1687620040:t=1687696419:v=2:sig=AQFLXWHSfe752c-owR1S3P8Q_frEVh6e"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4514:u=51:x=1:i=1687595585:t=1687608928:v=2:sig=AQH0H7FjSwSsdlmZsw6uhsFDCp1ROKX8"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    response_json = response.json()

    t_comments = response_json['commentsSummary']['aggregatedTotalComments']
    t_likes = response_json['likesSummary']['aggregatedTotalLikes']
    form = Post_urn.objects.get(urn=urn)
    form.post_likes = t_likes
    form.post_comments = t_comments
    form.save()
    next = None
    if linkedin_post.comment_check:
        url = "https://api.linkedin.com/v2/socialActions/" + encoded_urn + "/comments"

        payload = {}
        headers = {
            'LinkedIn-Version': '202304',
            'X-Restli-Protocol-Version': '2.0.0',
            'Authorization': 'Bearer ' + access_token_string,
            'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4543:u=51:x=1:i=1688402283:t=1688474844:v=2:sig=AQEpkxXWxp7LRP7Mi5vt8y1DzvizD74p"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4543:u=51:x=1:i=1688402184:t=1688474844:v=2:sig=AQEe56HhN4GzpbcINCOFmpXb-L-mvjpK"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4543:u=51:x=1:i=1688399773:t=1688474844:v=2:sig=AQFdvDMS2NMzPLvL9rDALkiyQv6etADT"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lang=v=2&lang=en-us'
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        response_json3 = response.json()
        link = response_json3.get('paging', {}).get("links")
        if link and len(link) > 0:
            for l in link:
                if l.get('rel') == "next":
                    next = l.get('href')

        elements = response_json3.get('elements')
        data = []
        for element in elements:
            urls = []
            if 'content' in element:
                for content in element['content']:
                    if 'url' in content:
                        urls.append(content['url'])
            actor = element.get('actor')
            comment_urn = element.get('$URN')
            comment_id = element.get('id')
            if 'likesSummary' in element:
                liked = element['likesSummary']['likedByCurrentUser']
            else:
                liked = None
            if comment_urn:
                result = get_nested_comments(access_token, comment_urn)
                replies = result[0]
                reply_next = result[1]


            else:
                replies = None
            texts = element.get('message', {}).get('text')
            if elements and len(elements) > 0:
                # actor = elements[0].get('actor')
                prefix, value = actor.rsplit(':', 1)
                if prefix == 'urn:li:organization':
                    url = "https://api.linkedin.com/v2/organizations/" + value + "?projection=(localizedName,logoV2(original~:playableStreams))"

                    payload = {}
                    headers = {
                        'Linkedin-Version': '202304',
                        'X-Restli-Protocol-Version': '2.0.0',
                        'Authorization': 'Bearer ' + access_token_string,
                        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4551:u=55:x=1:i=1689588794:t=1689613491:v=2:sig=AQEuUJEbIsk57LyEy9HwFJQrEu7ayH9n"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4551:u=55:x=1:i=1689587318:t=1689613491:v=2:sig=AQGp8c3I7u6ZkNJN7oSt0OLu8JRVv3WX"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lidc="b=TB01:s=T:r=T:a=T:p=T:g=5807:u=1:x=1:i=1689586527:t=1689672927:v=2:sig=AQFFnf4QlGIIpq60wKa97GoDCwxO3u-D"'
                    }

                    response = requests.request("GET", url, headers=headers, data=payload)
                    response = response.json()
                    if 'logoV2' in response:
                        display_image = response['logoV2']['original~']['elements'][0]['identifiers'][0]['identifier']
                    else:
                        display_image = ''
                    name = response['localizedName']
                    obj = {'name': name, "profile_image": display_image, "text": texts, "urls": urls,
                           "comment_urn": comment_urn, "liked": liked, "comment_id": comment_id, "user_id": actor}
                    obj['replies'] = replies
                    obj['next'] = reply_next
                    data.append(obj)
                else:

                    url = "https://api.linkedin.com/v2/people/(id:" + value + ")?projection=(id,firstName,lastName,profilePicture(displayImage~:playableStreams))"

                    payload = {}
                    headers = {
                        'LinkedIn-Version': '202304',
                        'X-Restli-Protocol-Version': '2.0.0',
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + access_token_string,
                        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4546:u=53:x=1:i=1689164560:t=1689211004:v=2:sig=AQFTaVIUWiQvbWucAVvFtIY0AKWyBlpL"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lidc="b=OB01:s=O:r=O:a=O:p=O:g=5300:u=1:x=1:i=1689164320:t=1689250720:v=2:sig=AQG5yzvdOIb42jeJLKgJispG3AzPSMcJ"'
                    }

                    response = requests.request("GET", url, headers=headers, data=payload)
                    response = response.json()
                    if 'profilePicture' in response:
                        display_image = response['profilePicture']['displayImage~']['elements'][0]['identifiers'][0][
                            'identifier']
                    else:
                        display_image = ''
                    name = response['firstName']['localized']['en_US'] + " " + response['lastName']['localized'][
                        'en_US']

                    obj = {'name': name, "profile_image": display_image, "text": texts, "urls": urls,
                           "comment_urn": comment_urn, "liked": liked, "comment_id": comment_id, "user_id": actor}
                    obj['replies'] = replies
                    obj['next'] = reply_next
                    data.append(obj)
            else:
                obj = {'name': "", "profile_image": "", "text": "", "urls": urls, "comment_urn": "", "liked": False,
                       "comment_id": "", "user_id": ""}
                replies = None
                obj['replies'] = replies
                obj['next'] = reply_next
                data.append(obj)

        return t_likes, t_comments, data, next
    else:
        data = []
        obj = {}
        data.append(obj)

    return t_likes, t_comments, data, next





def linkedin_org_stats(access_token_string, id, data_list):
    data_dict = {}
    url = "https://api.linkedin.com/rest/organizationalEntityFollowerStatistics?q=organizationalEntity&organizationalEntity=urn%3Ali%3Aorganization%3A" + id.org_id

    payload = {}
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Authorization': 'Bearer ' + access_token_string,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4514:u=51:x=1:i=1687765789:t=1687848629:v=2:sig=AQHjIm1wsBkgK_2TJaHoboqQvmgXp9Aw"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    response_1 = response.json()

    try:
        follower_counts = response_1['elements'][0]['followerCountsBySeniority'][0]['followerCounts']
        organic_follower_count = follower_counts['organicFollowerCount']
        paid_follower_count = follower_counts['paidFollowerCount']


    except (KeyError, IndexError):
        organic_follower_count = 0
        paid_follower_count = 0
        pass

    organization = response_1['elements'][0]['organizationalEntity']

    url = "https://api.linkedin.com/rest/organizationalEntityShareStatistics?q=organizationalEntity&organizationalEntity=urn%3Ali%3Aorganization%3A" + id.org_id

    payload = {}
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Authorization': 'Bearer ' + access_token_string,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4514:u=51:x=1:i=1687765789:t=1687848629:v=2:sig=AQHjIm1wsBkgK_2TJaHoboqQvmgXp9Aw"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    response_2 = response.json()
    stats = response_2['elements'][0]['totalShareStatistics']
    unique_impression = stats['uniqueImpressionsCount']
    shares = stats['shareCount']
    mentions = stats['shareMentionsCount']
    engagements = stats['engagement']
    clickcount = stats['clickCount']
    likecount = stats['likeCount']
    impression_count = stats['impressionCount']
    comment_mentions = stats['commentMentionsCount']
    comments_count = stats['commentCount']

    data_dict['organization'] = organization
    data_dict['organic_follower_count'] = organic_follower_count
    data_dict['paid_follower_count'] = paid_follower_count
    data_dict['unique_impression'] = unique_impression
    data_dict['shares'] = shares
    data_dict['mentions'] = mentions
    data_dict['engagements'] = engagements
    data_dict['clickcount'] = clickcount
    data_dict['likecount'] = likecount
    data_dict['impression_count'] = impression_count
    data_dict['comment_mentions'] = comment_mentions
    data_dict['comments_count'] = comments_count
    data_list.append(data_dict)
    # return data_list


def delete_post_like_linkedin(post_urn, social, access_token):
    encoded_post = quote(post_urn, safe='')
    url = "https://api.linkedin.com/rest/reactions/(actor:urn%3Ali%3Aperson%3A" + social.uid + ",entity:" + encoded_post + ")"

    payload = json.dumps({
        "root": post_urn,
        "reactionType": "LIKE"
    })
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + access_token,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4595:u=82:x=1:i=1693371139:t=1693391046:v=2:sig=AQGaLrcwXLeVna6tI9hnBQby5nDr4N94"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4595:u=82:x=1:i=1693369485:t=1693391046:v=2:sig=AQF779dHfhe2gSoMR5lLPKLbyBryCShS"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lidc="b=VB60:s=V:r=V:a=V:p=V:g=3435:u=1:x=1:i=1693371035:t=1693457435:v=2:sig=AQHlAZ6D4gwH0OvAOk7C_y4O8r7mArwS"'
    }

    like_response = requests.request("DELETE", url, headers=headers, data=payload)


    if like_response.status_code == 204:
        like_response = "success"

    else:
        like_response = "error"

    encoded_urn = quote(post_urn, safe='')
    url = "https://api.linkedin.com/rest/socialActions/" + encoded_urn

    payload = {}
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'LinkedIn-Version': '202304',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Bearer ' + access_token,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4514:u=51:x=1:i=1687620040:t=1687696419:v=2:sig=AQFLXWHSfe752c-owR1S3P8Q_frEVh6e"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4514:u=51:x=1:i=1687595585:t=1687608928:v=2:sig=AQH0H7FjSwSsdlmZsw6uhsFDCp1ROKX8"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"'
    }

    like_count = requests.request("GET", url, headers=headers, data=payload)
    like_count = like_count.json()
    t_likes = like_count['likesSummary']['aggregatedTotalLikes']



    return like_response ,t_likes


def post_like_linkedin(post_urn, social, access_token):
    url = "https://api.linkedin.com/rest/reactions?actor=urn%3Ali%3Aperson%3A" + social.uid

    payload = json.dumps({
        "root": post_urn,
        "reactionType": "LIKE"
    })
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + access_token,
    }

    like_response = requests.request("POST", url, headers=headers, data=payload)

    if like_response.status_code == 201:
        like_response = like_response.json()
    else:
        like_response = "error"

    encoded_urn = quote(post_urn, safe='')
    url = "https://api.linkedin.com/rest/socialActions/" + encoded_urn

    payload = {}
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'LinkedIn-Version': '202304',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Bearer ' + access_token,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4514:u=51:x=1:i=1687620040:t=1687696419:v=2:sig=AQFLXWHSfe752c-owR1S3P8Q_frEVh6e"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4514:u=51:x=1:i=1687595585:t=1687608928:v=2:sig=AQH0H7FjSwSsdlmZsw6uhsFDCp1ROKX8"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"'
    }

    like_count = requests.request("GET", url, headers=headers, data=payload)
    like_count = like_count.json()
    t_likes = like_count['likesSummary']['aggregatedTotalLikes']


    return like_response ,t_likes


def linkedin_share_stats_overall(org_id, access_token):
    url = "https://api.linkedin.com/rest/organizationalEntityShareStatistics?q=organizationalEntity&organizationalEntity=urn%3Ali%3Aorganization%3A" + org_id
    payload = {}
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Authorization': 'Bearer ' + access_token,
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    data = response.json()

    if 'elements' in data and len(data['elements']) > 0:
        like_count = 0
        comment_count = 0

        for element in data['elements']:
            like_count += element['totalShareStatistics']['likeCount']
            comment_count += element['totalShareStatistics']['commentCount']

    else:
        like_count = 0
        comment_count = 0

    return like_count, comment_count


def linkedin_share_stats(org, start,end):
    org_id = org.org_id
    access_token = org.access_token
    url = "https://api.linkedin.com/rest/organizationalEntityShareStatistics?q=organizationalEntity&organizationalEntity=urn%3Ali%3Aorganization%3A" + org_id + "&timeIntervals=(timeRange:(start:" + str(
        int(start.timestamp()*1000)) + "),timeGranularityType:DAY)"

    payload = {}
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Authorization': 'Bearer ' + access_token,
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    data = response.json()
    # data)
    if 'elements' in data and len(data['elements']) > 0:
        like_count = 0
        comment_count = 0
        followers_count = 0
        for element in data['elements']:
            like_count += element['totalShareStatistics']['likeCount']
            comment_count += element['totalShareStatistics']['commentCount']

        followers_count = linkedin_followers(org_id, access_token)

    else:
        like_count = 0
        comment_count = 0
        followers_count = 0

    return like_count, comment_count,followers_count


# async def linkedin_share_stats(org, start, end):
#     org_id = org.org_id
#     access_token = org.access_token
#
#     url = f"https://api.linkedin.com/rest/organizationalEntityShareStatistics?q=organizationalEntity&organizationalEntity=urn%3Ali%3Aorganization%3A{org_id}&timeIntervals=(timeRange:(start:{int(start.timestamp() * 1000)}),timeGranularityType:DAY)"
#
#     headers = {
#         'X-Restli-Protocol-Version': '2.0.0',
#         'Linkedin-Version': '202304',
#         'Authorization': f'Bearer {access_token}',
#     }
#
#     like_count = 0
#     comment_count = 0
#     followers_count = 0
#
#     async with httpx.AsyncClient() as client:
#         try:
#             response = await client.get(url, headers=headers)
#             data = response.json()
#
#             if 'elements' in data and len(data['elements']) > 0:
#                 for element in data['elements']:
#                     like_count += element['totalShareStatistics']['likeCount']
#                     comment_count += element['totalShareStatistics']['commentCount']
#
#                 followers_count = await linkedin_followers(org_id, access_token)
#
#         except Exception as e:
#             # Handle exceptions as needed
#             pass


# def linkedin_followers_today(org_id, access_token):
#     result = linkedin_followers(org_id, access_token)
#     result)
#
#     return result


def linkedin_followers(org_id, access_token):
    url = "https://api.linkedin.com/rest/networkSizes/urn%3Ali%3Aorganization%3A" + org_id + "?edgeType=CompanyFollowedByMember"
    payload = {}
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Authorization': 'Bearer ' + access_token,
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    data = response.json()
    followers = data['firstDegreeSize']
    return followers


def comment_like_linkedin(comment_urn, social, access_token):
    url = "https://api.linkedin.com/rest/reactions?actor=urn%3Ali%3Aperson%3A" + social.uid

    payload = json.dumps({
        "root": comment_urn,
        "reactionType": "LIKE"
    })
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + access_token,
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.json()


def delete_comment_like_linkedin(comment_urn, social, access_token):
    encoded_post = quote(comment_urn, safe='')
    url = "https://api.linkedin.com/rest/reactions/(actor:urn%3Ali%3Aperson%3A" + social.uid + ",entity:" + encoded_post + ")"

    payload = json.dumps({
        "root": comment_urn,
        "reactionType": "LIKE"
    })
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + access_token,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4595:u=82:x=1:i=1693371139:t=1693391046:v=2:sig=AQGaLrcwXLeVna6tI9hnBQby5nDr4N94"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4595:u=82:x=1:i=1693369485:t=1693391046:v=2:sig=AQF779dHfhe2gSoMR5lLPKLbyBryCShS"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lidc="b=VB60:s=V:r=V:a=V:p=V:g=3435:u=1:x=1:i=1693371035:t=1693457435:v=2:sig=AQHlAZ6D4gwH0OvAOk7C_y4O8r7mArwS"'
    }

    response = requests.request("DELETE", url, headers=headers, data=payload)

    if response.status_code == 204:
        return 'success'
    else:
        return 'error'



def linkedin_retrieve_access_token(post_id):
    posts = PostModel.objects.get(id=post_id)
    user = posts.user
    if len(SocialAccount.objects.filter(user=user.id, provider='linkedin_oauth2')) > 0:
        social = SocialAccount.objects.get(user=user.id, provider='linkedin_oauth2')
        if social:
            ids = SharePage.objects.filter(user=social.pk)
            access_token = SocialToken.objects.filter(account_id=social)
            access_token_string = ', '.join(str(obj) for obj in access_token)

            return posts, access_token_string, ids, social
    else:
        posts = ''
        access_token_string = ''
        ids = ''
        social = ''
        return posts, access_token_string, ids, social


def linkedin_get_user_organization(accesstoken, userid):
    url = "https://api.linkedin.com/v2/organizationalEntityAcls?q=roleAssignee"

    payload = {}
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Authorization': 'Bearer ' + accesstoken,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4514:u=51:x=1:i=1687765789:t=1687848629:v=2:sig=AQHjIm1wsBkgK_2TJaHoboqQvmgXp9Aw"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    response = response.json()
    targets = [element['organizationalTarget'] for element in response['elements']]
    data = targets
    ids = [item.split(':')[-1] for item in data]

    id = ','.join(ids)

    url = f"https://api.linkedin.com/v2/organizations?ids=List({id})"

    payload = {}
    headers = {
        'LinkedIn-Version': '202304',
        'X-Restli-Protocol-Version': '2.0.0',
        'Authorization': 'Bearer ' + accesstoken,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4543:u=51:x=1:i=1688456448:t=1688474844:v=2:sig=AQGzRecgKiUECgv05uH2KHFxISD6bd_d"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4543:u=51:x=1:i=1688398890:t=1688474844:v=2:sig=AQHKhaANXQC9mWny3X46qeX8AAsrtxOQ"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lang=v=2&lang=en-us'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    response = response.json()
    names_with_ids = {}
    my_list = []

    for id, data in response['results'].items():
        my_object = {}

        localizedName = data['localizedName']
        names_with_ids[id] = localizedName
        my_object['id'] = id
        if 'coverPhotoV2' in data and 'cropped' in data['coverPhotoV2']:
            my_object['photo'] = data['coverPhotoV2']['cropped']
        my_object['name'] = localizedName
        my_object['user'] = userid  # referring to the user of the page
        organization_count = SharePage.objects.filter(org_id=id).count()
        if organization_count > 0:
            my_object['checked'] = True
        else:
            my_object['checked'] = False
        my_list.append(my_object)
    data = my_list
    return data


def linkedin_page_detail(accesstoken, id):

    data = {}
    detail = {}

    url = "https://api.linkedin.com/v2/organizations/" + id + "?projection=(localizedName,logoV2(original~:playableStreams),organizationType,locations,website,foundedOn)"

    payload = {}
    headers = {
        'Linkedin-Version': '202304',
        'X-Restli-Protocol-Version': '2.0.0',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + accesstoken,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4551:u=55:x=1:i=1689588794:t=1689613491:v=2:sig=AQEuUJEbIsk57LyEy9HwFJQrEu7ayH9n"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4551:u=55:x=1:i=1689587318:t=1689613491:v=2:sig=AQGp8c3I7u6ZkNJN7oSt0OLu8JRVv3WX"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lidc="b=TB01:s=T:r=T:a=T:p=T:g=5807:u=1:x=1:i=1689586527:t=1689672927:v=2:sig=AQFFnf4QlGIIpq60wKa97GoDCwxO3u-D"'
    }



    response = requests.request("GET", url, headers=headers, data=payload)
    response = response.json()



    name = response['localizedName']

    data['Personal Information'] = [{'Name':name},{"Organization Type":response['organizationType']}]

    if len(response.get('locations')) > 0:
         address_data = response.get('locations')[0]['address']

         line1 = address_data.get('line1', '')
         line2 = address_data.get('line2', '')
         city = address_data.get('city', '')
         geographicArea = address_data.get('geographicArea', '')
         country = address_data.get('country', '')

            # Join the non-empty values with commas
         full_address = ', '.join(filter(None, [line1, line2, city, geographicArea, country]))

         if 'postalCode' in response.get('locations')[0]['address']:
            data['Contact Information'] = [{'Address': full_address},{"Postal Code": response.get('locations')[0]['address']['postalCode']}]
         else:
            data['Contact Information'] = [{'Address': full_address}]

    if 'logoV2' in response:
        detail['profile_picture'] = response['logoV2']['original~']['elements'][0]['identifiers'][0][
            'identifier']



    detail['details'] = data

    return detail


from PIL import Image


def reduce_pixel_count(input_path, output_path, max_pixels):
    try:
        # Open the image file
        with Image.open(input_path) as image:
            # Get the current pixel count
            current_pixels = image.width * image.height

            if current_pixels > max_pixels:
                # Calculate the new dimensions to reduce the pixel count while maintaining the aspect ratio
                aspect_ratio = image.width / image.height
                new_height = int((max_pixels / aspect_ratio) ** 0.5)
                new_width = int(aspect_ratio * new_height)

                # Resize the image to the new dimensions
                resized_image = image.resize((new_width, new_height))

                # Save the resized image
                resized_image.save(output_path)
                # f"Image pixel count reduced and saved as {output_path}")
            else:
                # No need to resize, save the image as it is
                image.save(output_path)
                # f"Image pixel count is within the specified limit. Image saved as {output_path}")
    except Exception as e:
        e


def get_img_urn(org_id, access_token_string):
    url = "https://api.linkedin.com/rest/images?action=initializeUpload"

    payload = json.dumps({
        "initializeUploadRequest": {
            "owner": "urn:li:organization:" + org_id
        },

    })
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + access_token_string,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4543:u=51:x=1:i=1688190892:t=1688211049:v=2:sig=AQFsBoC8nO9rLgaq01RvNUX3PJGk3BJm"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    # response.json())
    return response


def get_video_urn(org_id, access_token_string):
    url = "https://api.linkedin.com/rest/assets?action=registerUpload"

    payload = json.dumps({
        "registerUploadRequest": {
            "owner": "urn:li:organization:" + org_id,
            "recipes": [
                "urn:li:digitalmediaRecipe:feedshare-video"
            ],
            "serviceRelationships": [
                {
                    "identifier": "urn:li:userGeneratedContent",
                    "relationshipType": "OWNER"
                }
            ]
        }
    })
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Content-Type': 'text/plain',
        'Authorization': 'Bearer ' + access_token_string,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4545:u=51:x=1:i=1688749809:t=1688770215:v=2:sig=AQF9_UPU7ioqjq0bnTarcQnzOY7zgjys"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lang=v=2&lang=en-us; lidc="b=OGST09:s=O:r=O:a=O:p=O:g=2538:u=1:x=1:i=1688729286:t=1688815686:v=2:sig=AQEaQczLgDhIkqosNSFNczvZQ63GlG-z"'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response


def upload_img(upload_url, image_file, access_token_string):
    url = upload_url
    # Set the path to the imaganasrehman/Pyce file on your local machine

    image_path = os.path.join(settings.BASE_DIR, "media/" + str(image_file))
    # image_path)
    # image_path = "/Users/harmProjects/social_automation/social_auto/media/" + str(image_file)
    input_path = image_path
    output_path = input_path
    max_pixels = 36152320  # Maximum pixel count (e.g., 1920x1080)

    reduce_pixel_count(input_path, output_path, max_pixels)

    headers = {
        "Authorization": f"Bearer {access_token_string}",
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
    }

    # Open the image file in binary mode and send it as the request body
    with open(output_path, "rb") as file:
        response = requests.request("PUT", url, headers=headers, data=file)
        return response


def upload_video(upload_url, video_file):
    url = upload_url
    video_path = os.path.join(settings.BASE_DIR, "media/" + str(video_file))
    # video_path = "/Users/anasrehman/PycharmProjects/social_automation/social_auto/media/videos/" + str(video_file)

    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Content-Type': 'application/octet-stream',
    }
    with open(video_path, 'rb') as file:
        response = requests.request("PUT", url, headers=headers, data=file)
        # if response.status_code == 201:
        # # "Video Succesfully Uploaded")
        return response


def post_video_linkedin(image_urn, access_token_string, org_id, post):
    url = "https://api.linkedin.com/v2/ugcPosts"
    payload = json.dumps({
        "author": "urn:li:organization:" + org_id,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "media": [
                    {
                        "media": image_urn,
                        "status": "READY",
                        "title": {
                            "attributes": [],
                            "text": "Sample Video Create"
                        }
                    }
                ],
                "shareCommentary": {
                    "attributes": [],
                    "text": post.post
                },
                "shareMediaCategory": "VIDEO"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    })
    headers = {
        'Content-Type': 'application/json',
        'LinkedIn-Version': '202304',
        'X-Restli-Protocol-Version': '2.0.0',
        'Authorization': 'Bearer ' + access_token_string,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4545:u=51:x=1:i=1688630120:t=1688679838:v=2:sig=AQHWT7t_ASmSYYkcUrr26qV5Yuj-El5U"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lang=v=2&lang=en-us'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response


def post_linkedin(image_list, post, org_id, access_token):
    url = "https://api.linkedin.com/rest/posts"

    # print(post)

    payload = json.dumps({
        "author": "urn:li:organization:" + org_id,
        "commentary": post.post,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
        "content": {
            "multiImage": {
                "images": image_list
            }
        }
    })
    headers = {
        'Content-Type': 'application/json',
        'LinkedIn-Version': '202304',
        'X-Restli-Protocol-Version': '2.0.0',
        'Authorization': 'Bearer ' + access_token,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4545:u=51:x=1:i=1688630120:t=1688679838:v=2:sig=AQHWT7t_ASmSYYkcUrr26qV5Yuj-El5U"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lang=v=2&lang=en-us'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response


def post_single_image_linkedin(access_token_string, org_id, post, image_list):
    url = 'https://api.linkedin.com/rest/posts'
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + access_token_string,
    }

    # Set the post data including the image URN and other relevant details

    data = {

        "author": "urn:li:organization:" + org_id,
        "commentary": post.post,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "content": {
            "media": image_list
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }
    response = requests.request('POST', url, headers=headers, json=data)

    return response


def save_files(image):
    file = image
    if file:
        file_extension = file.name.split('.')[-1].lower()
        if file_extension == 'mp4':
            image_url = get_video_url(file)
            image_path = image_url.get('files')[0].get('path')
            image_model = ImageModel(image=image, image_url=image_path)
            image_model.save()
        else:
            image_url = get_image_url(image)
            image_path = image_url.get('files')[0].get('path')
            image_model = ImageModel(image=image, image_url=image_path)
            image_model.save()

    return image_model


def save_file1(image):
    file = image.image
    if file:
        file_extension = file.name.split('.')[-1].lower()
        if file_extension == 'mp4':
            image_url = get_video_url(file)
            image_path = image_url.get('files')[0].get('path')

        else:
            image_url = get_image_url(file)
            image_path = image_url.get('files')[0].get('path')

        image_model = ImageModel.objects.get(id=image.id)
        image_model.image_url = image_path
        image_model.save()
        return image_model


def clean_file(images):
    video_file = None
    updated_images_list = []

    for item in images:
        if item.image.name.endswith('.mp4'):
            video_file = item.image
        else:
            updated_images_list.append(item)
    return video_file, updated_images_list


def linkdein(access_token_string):
    url = "https://api.linkedin.com/v2/organizationalEntityAcls?q=roleAssignee"

    payload = {}
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Authorization': 'Bearer ' + access_token_string,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4543:u=51:x=1:i=1688454620:t=1688474844:v=2:sig=AQEPLNOkmN73V6fYvS7fD8W9CViGJ3hF"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lang=v=2&lang=en-us'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    response = response.json()
    targets = [element['organizationalTarget'] for element in response['elements']]
    data = targets
    ids = [item.split(':')[-1] for item in data]

    id = ','.join(ids)

    url = f"https://api.linkedin.com/v2/organizations?ids=List({id})"

    payload = {}
    headers = {
        'LinkedIn-Version': '202304',
        'X-Restli-Protocol-Version': '2.0.0',
        'Authorization': 'Bearer ' + access_token_string,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4543:u=51:x=1:i=1688456448:t=1688474844:v=2:sig=AQGzRecgKiUECgv05uH2KHFxISD6bd_d"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4543:u=51:x=1:i=1688398890:t=1688474844:v=2:sig=AQHKhaANXQC9mWny3X46qeX8AAsrtxOQ"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"; lang=v=2&lang=en-us'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    response = response.json()


def get_image_url(file):
    url = "https://messangel.caansoft.com/uploadfile"

    payload = {'base_path': '/social_prefrences/image/',
               'artifect_type': 'image',
               'filename': 'test.png'}

    files = [
        ('dataFiles', (file),)

    ]
    headers = {}

    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    response = response.json()
    return response


def get_video_url(file):
    url = "https://messangel.caansoft.com/uploadfile"

    payload = {'base_path': '/social_prefrences/video/',
               'artifect_type': 'video',
               'filename': 'test.mp4'}
    files = [
        ('dataFiles', (file),)
    ]

    headers = {}

    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    response = response.json()

    return response


def text_post_linkedin(post, access_token_string, org_id):
    url = "https://api.linkedin.com/rest/posts"

    payload = json.dumps({
        "author": "urn:li:organization:" + org_id,
        "commentary": post.post,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    })
    headers = {
        'Content-Type': 'application/json',
        'LinkedIn-Version': '202304',
        'X-Restli-Protocol-Version': '2.0.0',
        'Authorization': 'Bearer ' + access_token_string,
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4546:u=55:x=1:i=1689314606:t=1689334414:v=2:sig=AQHSFW1fjeXULNO8CiDc8_rZkoMXJMK3"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response


def meta_comments(urn, text, media, access_token,provider_name):
    url = f"https://graph.facebook.com/v17.0/{urn}/comments"

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    data = {}

    if text:
        data['message'] = text

    files = []
    if media and media != '':
        extension = get_file_extension(media.content_type)
        if extension in ['jpg', 'png']:
            data['attachment_url'] = get_image_url(media).get('files')[0].get('path')
        elif extension in ['gif']:
            pass
        elif extension in ['mp4']:
            video_path = os.path.join(settings.BASE_DIR, "media/" + "videos/send.mp4")
            files = [
                ('source', ('send.mp4',
                            open(video_path,
                                 'rb'), 'application/octet-stream'))
            ]

    response = requests.post(url=url, headers=headers, data=data, files=files)
    comment_response = dict()
    if response.status_code == 200:
        id = response.json()['id']
        if provider_name == "facebook":

            url = f"https://graph.facebook.com/v17.0/{id}"

            respone2 = requests.get(url = url, headers=headers)

            if respone2.status_code == 200:
                response2 = respone2.json()
                comment_response['name'] = response2['from']['name']
                comment_response['user_id'] = response2['from']['id']
                comment_response['created_time'] = response2['created_time']
                comment_response['text'] = response2['message']
                comment_response['comment_urn'] = response2['id']

                return comment_response
        elif provider_name == "instagram":
            url = f"https://graph.facebook.com/v17.0/{id}?fields=from,text"
            respone2 = requests.get(url=url, headers=headers)

            if respone2.status_code == 200:
                response2 = respone2.json()
                comment_response['name'] = response2['from']['username']
                comment_response['user_id'] = response2['from']['id']
                comment_response['text'] = response2['text']
                comment_response['comment_urn'] = response2['id']

                return comment_response



    else:
        return "error"


def meta_nested_comment(urn, text, media, access_token, provider_name):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    files = []
    data = {}
    if text:
        data['message'] = text
    comment_response = dict()
    if provider_name == "facebook":
        url = f"https://graph.facebook.com/{urn}/comments"
        if media and media != '':
            extension = get_file_extension(media.content_type)
            if extension in ['jpg', 'png']:
                data['attachment_url'] = get_image_url(media).get('files')[0].get('path')
            elif extension in ['gif']:
                pass
            elif get_file_extension(media.content_type) in ['mp4']:
                video_path = os.path.join(settings.BASE_DIR, "media/" + "videos/send.mp4")
                files = [
                    ('source', ('send.mp4',
                                open(video_path,
                                     'rb'), 'application/octet-stream'))
                ]

            else:
                pass
        response = requests.post(url=url, headers=headers, data=data, files=files)

        if response.status_code == 200:
            id = response.json()['id']

            url = f"https://graph.facebook.com/v17.0/{id}"

            respone2 = requests.get(url=url, headers=headers)

            if respone2.status_code == 200:
                response2 = respone2.json()
                comment_response['name'] = response2['from']['name']
                comment_response['user_id'] = response2['from']['id']
                comment_response['created_time'] = response2['created_time']
                comment_response['text'] = response2['message']
                comment_response['comment_urn'] = response2['id']

                return comment_response

    elif provider_name == "instagram":
        url = f"https://graph.facebook.com/{urn}/replies"

        response = requests.post(url=url, headers=headers, data=data, files=files)
        if response.status_code == 200:
            id = response.json()['id']
            url = f"https://graph.facebook.com/v17.0/{id}?fields=from,text"
            respone2 = requests.get(url=url, headers=headers)

            if respone2.status_code == 200:
                response2 = respone2.json()
                comment_response['name'] = response2['from']['username']
                comment_response['user_id'] = response2['from']['id']
                comment_response['text'] = response2['text']
                comment_response['comment_urn'] = response2['id']

                return comment_response



def meta_reply_pagination(pagination,access_token,provider_name):

    parse_url = urlparse(pagination)
    scheme = parse_url.scheme
    netloc = parse_url.netloc
    path = parse_url.path
    query = parse_url.query
    query_parameters = parse_qs(query)
    # query_parameters.pop("limit")
    query_parameters["limit"] = ["5"]
    encodedquery = urlencode(query_parameters, doseq=True)

    url = scheme + "://"+ netloc + path + "?" + encodedquery

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url=url,headers=headers)
    data = "error"
    if response.status_code == 200:
        response = response.json()
        element = response.get('data')
        data = dict()
        if provider_name  == "facebook":

            if response['paging'].get('next'):
                data['next'] = response['paging']['next']
            else:
                data['next'] = None

            data['comment_response'] = fb_social_action_data_organizer(element,headers)

        elif provider_name == "instagram":
            if response.get('paging',{}).get('next'):
                data['next'] = response['paging']['next']
            else:
                data['next'] = None
            data['comment_response'] = insta_social_actions_data_organizer(element,headers)

    return data



def schedule_validator(request, post_id):

    post = PostModel.objects.get(pk=post_id)
    if post.status == 'SCHEDULED':
        scheduled_time = post.schedule_datetime
        current_datetime = timezone.now()
        errors = {}
        if current_datetime > scheduled_time:
            errors["Invalid Post "] = "Post does not exists"

        return errors
    else:
        return {}








def linkedin_validator(request):
    video = 0
    img = 0
    images = request.FILES.getlist('images')
    provider = request.POST.get("linkedin")
    errors = {}
    if provider:
        for image in images:
            if image.name.endswith('.mp4'):
                video += 1
            else:
                img += 1

            if video >= 1 and img >= 1 and errors.get('Invalid Number') == None:
                errors["Invalid Number"] = "Linkedin cannot contain both image and video"
                # print("Can not contain video and image")

            if video > 1 and errors.get('Video') == None:
                errors['Video'] = "Linkedin can not contain more than one video"
                # print("Can not contain more than one Video")

    return errors


def instagram_validator(request):
    errors = {}
    provider = request.POST.get("instagram")
    images = request.FILES.getlist('images')
    if provider:
        # if not request.POST.get("post"):
        #     errors["Invalid Post for insta"] = "Instagram media can not be post without text"
        if len(images) < 1:
            errors['Invalid Post for insta'] = "Instagram cannot post without media"

    return errors

def instagram_validator2(request, post_id):
    errors = {}
    provider = request.POST.get("instagram")
    images = request.FILES.getlist('images')
    post = PostModel.objects.get(pk=post_id)
    image = post.images.all()
    if provider:
        # if not request.POST.get("post"):
        #     errors["Invalid Post for insta"] = "Instagram media can not be post without text"
        if len(image) > 0:
            if len(images) and len(image) < 1:
                errors['Invalid Post for insta'] = "Instagram cannot post without media"
        else:
            if len(images) < 1:
                errors['Invalid Post for insta'] = "Instagram cannot post without media"

    return errors


def facebook_validator(request):
    video = 0
    img = 0
    images = request.FILES.getlist('images')
    provider = request.POST.get("facebook")
    errors = {}
    if provider:
        for image in images:
            if image.name.endswith('.mp4'):
                video += 1
            else:
                img += 1

            if video >= 1 and img >= 1 and errors.get('Invalid Number') == None:
                errors["Invalid Number"] = "Facebook cannot contain both image and video"
                # print("Can not contain video and image")

            if video > 1 and errors.get('Video') == None:
                errors['Video'] = "Facebook can not contain more than one video"
                # print("Can not contain more than one Video")

    return errors


def fb_object_like(urn, access_token):
    url = f"https://graph.facebook.com/v17.0/{urn}/likes"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    like_response = requests.post(url=url, headers=headers)

    if like_response.status_code == 200:
        like_response = like_response.json()
    else:
        like_response = "error"

    url2 = f"https://graph.facebook.com/{urn}?fields=reactions.summary(true)"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    like_count_response = requests.get(url=url2, headers=headers)
    like_count_response = like_count_response.json()["reactions"]["summary"]["total_count"]

    return like_response , like_count_response






def fb_object_unlike(urn, access_token):
    url = f"https://graph.facebook.com/v17.0/{urn}/likes"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    like_response = requests.delete(url=url, headers=headers)

    if like_response.status_code == 200:
        like_response = like_response.json()
    else:
        like_response = "error"

    url2 = f"https://graph.facebook.com/{urn}?fields=reactions.summary(true)"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    like_count_response = requests.get(url=url2, headers=headers)
    like_count_response = like_count_response.json()["reactions"]["summary"]["total_count"]

    return like_response , like_count_response




def fb_user_detail(access_token):
    url = "https://graph.facebook.com/v17.0/me?fields=name,email,location,about,gender,picture.type(large){url,height,width}"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)
    details = dict()
    data = dict()

    if response.status_code == 200:
        response = response.json()
        data['Personal Information'] = []
        data['Personal Information'].append({'Name': response.get('name').capitalize()})if response.get('name') else None
        data['Personal Information'].append({'Gender':response.get('gender',None).capitalize()})if response.get('gender') else None
        if response.get('location'):
            data['Location'] = [{ 'Location':response.get('location')['name']}]

        profile_image = response.get('picture')['data']['url'] if response.get('picture') else None
        if response.get('email') :
            data['Contact Information']= [{'Email': response.get('email')}]
        details["profile_picture"] = profile_image
    else:
        data['error'] = response.json()

    details['details'] = data
    return details


def fb_page_detail(org_id, access_token):
    url = f"https://graph.facebook.com/v17.0/{org_id}?fields=name,category,location,about,emails,display_subtext,website,phone,picture.type(large){{url}}"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    details = dict()
    data = dict()
    response = requests.get(url=url,headers = headers)

    if response.status_code == 200:
        response = response.json()

        if response['category']:
            data['Category'] = [{"Category":response.get("category")}]


        data["Personal Information"] = [{"Name":response.get('name')}]

        data['Contact Information'] = []
        if response.get('location'):
            address = ','.join(
                [response['location'].get('street',''), response['location'].get('city',''), response['location'].get('country',''),
                 response['location'].get('zip','')])


            data['Contact Information'].append({"Address": address})  if address else None


        data['Contact Information'].append({"Phone":response.get('phone')}) if response.get('phone') else None
        data['Contact Information'].append({"Email":response.get('emails')[0]}) if response.get('emails') else None
        profile_image = response.get('picture')['data']['url'] if response.get('picture') else None

        data['Websites'] = [{'website':response.get('website', '')}] if response.get('website') else []

        details['profile_picture'] = profile_image
    else:
        data['error'] = response.json()

    details['details'] = data
    return details


def instagram_account_insights(urn, since, until):
    access_token = urn.access_token
    instagram_id = urn.org_id
    url = f"https://graph.facebook.com/v17.0/{instagram_id}/insights"
    url2 = f"https://graph.facebook.com/v17.0/{instagram_id}?fields=followers_count"

    params = {
        'metric': 'likes,comments',
        'period': 'day',
        'metric_type': 'total_value',
        'since': int(since.timestamp()),
        'until': int(until.timestamp())
    }

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    total_likes = 0
    total_comments = 0
    followers_count = 0


    try:
        response = requests.get(url=url, headers=headers, params=params)
        response2 = requests.get(url=url2, headers=headers)

        if response.status_code == 200:
            data = response.json().get('data')
            total_likes += data[0]['total_value']['value']
            total_comments += data[1]['total_value']['value']

        if response2.status_code == 200:
            data2 = response2.json()
            followers_count = data2['followers_count']
    except Exception as e:
        pass

    return total_likes, total_comments, followers_count


# def instagram_details(access_token, instagram_id):
#     # "https://graph.facebook.com/v17.0/{id}?fields=name,profile_picture_url,username"
#     url = f"https://graph.facebook.com/v17.0/{instagram_id}?fields=username,biography,name,profile_picture_url,website"
#
#     headers = {
#         "Authorization": f"Bearer {access_token}"
#     }
#
#     response = requests.get(url=url, headers=headers)
#     data = {}
#     details = {}
#     if response.status_code == 200:
#         response = response.json()
#         data["Personal Information"] = [{"Name":response.get('name')} , {"username":response.get('username')}]
#         data["Personal Information"].append({"Description": response.get('biography')}) if response.get('biography') else None
#
#         if response.get("website"):
#             data["Contact Information"] = [{"Website": response.get('website')}]
#         profile_image = response.get('profile_picture_url') if response.get('profile_picture_url') else None
#         details['profile_picture'] = profile_image
#     else:
#         data['error'] = 'failed to fetch data. Unexpected Error has occurred'
#
#     details['details'] = data
#
#     return details





# async def fb_post_insights(urn_list,access_token, urn, since=None, until=None):
#     print(urn_list)
#     access_token = access_token
#     reaction_response = []
#     comment_response = []
#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         'Content-Type': 'application/json'
#     }
#     async with httpx.AsyncClient() as client:
#         tasks = []
#         len_execute = int(len(urn_list) / 50)
#
#         if (len(urn_list) % 50 != 0):
#             len_execute += 1
#
#         for turn in range(len_execute):
#             starting_index = turn * 50
#             ending_index = (turn + 1) * 50
#             new_urn_list = urn_list[starting_index:ending_index]
#
#             tasks.append(make_batch_request(client, access_token, new_urn_list, f'likes?since={int(since.timestamp())}&until={int(until.timestamp())}'))
#             tasks.append(make_batch_request(client, access_token, new_urn_list,
#                                             f'comments?fields=id,created_time,message&filter=stream&since={int(since.timestamp())}&until={int(until.timestamp())}'))
#
#
#         responses = await asyncio.gather(*tasks)
#         responses_len = int(len(responses) / 2)
#         for response in range(responses_len):
#             reaction_response.extend(responses[response])
#             comment_response.extend(responses[response + 1])
#
#         total_reaction = 0
#         total_comments = 0
#
#         for urn in range(len(urn_list)):
#             count_task = []
#             reaction_response_body = json.loads(reaction_response[urn].get('body'))
#             comment_response_body = json.loads(comment_response[urn].get('body'))
#             count_task.append(facebook_count_reactions(client, reaction_response_body))
#             count_task.append(facebook_count_comments(client, comment_response_body))
#
#             count_response = await asyncio.gather(*count_task)
#
#             total_reaction += count_response[0]
#             total_comments += count_response[1]
#
#         id = urn
#         url = f"https://graph.facebook.com/v17.0/{id}?fields=followers_count"
#
#         response3 = await client.get(url=url, headers=headers)
#         follower_count = 0
#         if response3.status_code == 200:
#             response3 = response3.json()
#             follower_count = response3['followers_count']
#
#
#         return total_reaction,total_comments,follower_count
#
#
# async def make_batch_request(client, access_token, post_ids, endpoint):
#
#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         'Content-Type': 'application/json'
#     }
#
#
#     batch_request = []
#     for post_id in post_ids:
#         request = {
#             'method': 'GET',
#             'relative_url': f'{post_id}/{endpoint}',
#         }
#         batch_request.append(request)
#     print(batch_request)
#     batch_request = json.dumps(batch_request)
#
#
#     try:
#         response = await client.post(f'https://graph.facebook.com/v17.0/', headers=headers,
#                                      params={'batch': batch_request, 'include_headers': 'false'})
#         print(response)
#     except Exception as e:
#         print(e)
#
#     if response.status_code == 200:
#         return response.json()
#     else:
#         return []
#
# async def facebook_count_reactions(client,response, response_request=None, total_reactions=0, send_request=False):
#     if send_request:
#         response = await client.get(response_request)
#         response = response.json()
#
#
#     total_reactions += len(response.get('data'))
#
#     if response.get('next'):
#         response_request = response.get('next')
#         facebook_count_reactions(response, response_request, total_reactions, True)
#
#     return total_reactions
#
# async def facebook_count_comments(client,response, response_request=None, total_comments=0, send_request=False):
#     if send_request:
#         response = await client.get(response_request)
#         response = response.json()
#
#     total_comments += len(response.get('data'))
#
#     if response.get('next'):
#         response_request = response.get('next')
#         facebook_count_comments(response, response_request, total_comments, True)
#
#     return total_comments





def fb_post_insights(urn_list, urn, since=None, until=None):


    access_token = urn.access_token
    base_url = 'https://graph.facebook.com/v17.0/'

    headers = {
        "Authorization": f"Bearer {access_token}",
        'Content-Type': 'application/json'
    }

    reaction_response = []
    comment_response = []
    len_execute = int(len(urn_list) / 50)

    if (len(urn_list) % 50 != 0):
        len_execute = len_execute + 1



    for _ in range(len_execute):
        starting_index = _*50
        ending_index = (_+1)*50
        new_urn_list = urn_list[starting_index:ending_index]
        batch_request1 = []
        batch_request2 = []
        for post_id in new_urn_list:
            request1 = {
                'method': 'GET',
                'relative_url': f'{post_id}/likes?since={int(since.timestamp())}&until={int(until.timestamp())}',
            }
            request2 = {
                'method': 'GET',
                'relative_url': f'{post_id}/comments?fields=id,created_time,message&since={int(since.timestamp())}&until={int(until.timestamp())}&filter=stream'
            }



            batch_request1.append(request1)
            batch_request2.append(request2)
        batch_request1 = json.dumps(batch_request1)
        batch_request2 = json.dumps(batch_request2)
        response1 = requests.post(base_url, headers=headers, params={'batch': batch_request1, 'include_headers': 'false'})
        response2 = requests.post(base_url, headers=headers, params={'batch': batch_request2, 'include_headers': 'false'})
        reaction_response.extend(response1.json())
        comment_response.extend(response2.json())


    total_reactions = 0

    for reaction in reaction_response:
        response = json.loads(reaction.get('body'))

        total_reactions += facebook_count_reactions(response)

    total_comments = 0
    for comment in comment_response:
        response = json.loads(comment.get('body'))

        total_comments += facebook_count_comments(response)


    # Request to get followerCounts
    id = urn.org_id
    url = f"https://graph.facebook.com/v17.0/{id}?fields=followers_count"

    response3 = requests.get(url = url,headers= headers)
    follower_count = 0
    if response3.status_code == 200:
        response3 = response3.json()
        follower_count = response3['followers_count']



    return total_reactions, total_comments , follower_count



def facebook_count_comments(response, response_request=None, total_comments=0, send_request=False):
    if send_request:
        response = requests.get(response_request)
        response = response.json()

    total_comments += len(response.get('data'))

    if response.get('next'):
        response_request = response.get('next')
        facebook_count_comments(response, response_request, total_comments, True)

    return total_comments


def facebook_count_reactions(response, response_request=None, total_reactions=0, send_request=False):

    if send_request:
        response = requests.get(response_request)
        response = response.json()


    total_reactions += len(response.get('data'))



    if response.get('next'):
        response_request = response.get('next')
        facebook_count_reactions(response, response_request, total_reactions, True)

    return total_reactions


def delete_meta_posts_comment(access_token, id):
    url = f"https://graph.facebook.com/v17.0/{id}"

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    response = requests.delete(url, headers=headers)

    if response.status_code == 200:
        return 'success'
    else:
        return 'failed'


def delete_linkedin_posts(access_token, id):
    encoded_urn = quote(id, safe='')
    url = "https://api.linkedin.com/rest/posts/" + encoded_urn

    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        "Authorization": f"Bearer {access_token}",
    }

    response = requests.delete(url, headers=headers)

    if response.status_code == 204:
        return 'success'
    else:
        return 'failed'


def delete_linkedin_comments(access_token, post_urn, comment_id, actor):
    encoded_urn = quote(post_urn, safe='')
    encoded_actor = quote(actor, safe='')
    url = 'https://api.linkedin.com/rest/socialActions/' + encoded_urn + '/comments/' + comment_id + '?actor=' + encoded_actor

    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        "Authorization": f"Bearer {access_token}",
    }

    response = requests.delete(url, headers=headers)

    if response.status_code == 204:
        return 'success'
    else:
        return 'failed'


def linkdein_pagination(pagination,access_token, type):
    parse_url = urlparse(pagination)

    path = parse_url.path
    query = parse_url.query
    query_parameters = parse_qs(query)
    # query_parameters.pop("count")
    query_parameters['count'] = ['5']
    encodedquery = urlencode(query_parameters, doseq=True)

    url = "https://api.linkedin.com" + path + "?" + encodedquery

    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'LinkedIn-Version': '202304',
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get(url=url,headers=headers)
    data = "error"
    if response.status_code == 200:
        response = response.json()
        elements = response.get('elements')

        data = dict()
        link = response.get('paging', {}).get("links")
        if link and len(link) > 0:
            for l in link:
                if l.get('rel') == "next":
                    data['next'] = l.get('href')

            if not data.get('next'):
                data['next'] = None

        if type == "comment":
            data['comment_response'] = ugcpost_socialactions_comment_data_organizer(elements, access_token)
        elif type == "reply":
            data['comment_response'] = ugcpost_socialactions_nested_comments_data_orgainzer(elements, access_token)

    return data



def map_search(search_input):

    access_token = 'pk.eyJ1IjoicmVoYW4wMTAiLCJhIjoiY2p1MWppdzh1MDJjZzQ5cHY0bG80eDFjcCJ9.CiQmY8N2iAms6F1nj1Twew'
    search_input = search_input # Replace with your actual search query
    bbox = "-8.667,19.057,11.999,37.125,"  # Replace with your desired bounding box coordinates

    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{search_input}.json?access_token={access_token}&bbox={bbox}"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)


