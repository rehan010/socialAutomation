import time
from io import BytesIO

from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.shortcuts import redirect, render
import os
from .models import *
from PIL import Image
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.models import SocialToken
from django.shortcuts import redirect
import requests
from django.http import JsonResponse
from urllib.parse import quote

import json
from django.conf import settings

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

def fb_social_action_data_organizer(elements,headers):
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

                obj = {'name': name, "profile_image": display_image, "text": text, "comment_urn": comment_urn}
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

                if element.get('comments'):

                    comments = element.get('comments').get('data')
                    obj['replies'] = fb_social_action_data_organizer(comments,headers)

                data.append(obj)

            else:
                obj = {'name': "", "profile_image": "", "text": "", "comment_urn": "","urls":[]}
                obj['replies'] = {}
                data.append(obj)
    return data


def fb_socialactions(post_urn,access_token):



    url = f"https://graph.facebook.com/{post_urn}?fields=likes.summary(true),comments.summary(true)"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url=url,headers=headers)

    response_json = response.json()

    t_likes = response_json.get("likes",{}).get("summary",{}).get("total_count",{})

    t_comments = response_json.get("comments",{}).get("summary",{}).get("total_count",{})

    form = Post_urn.objects.get(urn=post_urn)
    form.post_likes = t_likes
    form.post_comments = t_comments
    form.save()

    url = f"https://graph.facebook.com/{post_urn}/comments?fields=message,created_time,from,reactions,attachment,comments{{message,created_time,from,reactions,attachment,comments{{message, created_time,from, reactions, attachment}}}}"

#     comments{message,created_time,from}  field to get replies
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url=url,headers=headers)
    response_json2 = response.json()

    elements = response_json2.get("data")

    data = fb_social_action_data_organizer(elements,headers)
    return t_likes, t_comments, data


def insta_social_actions_data_organizer(elements,headers):
    data = []
    if elements:
        for element in elements:
            text = element["text"]
            comment_urn = element['id']
            if element and len(elements) > 0:
                actor = element['from']['id']

                url = f"https://graph.facebook.com/v17.0/{actor}?fields=profile_picture_url,name"

                response_2 = requests.get(url=url, headers=headers)

                response_json_2 = response_2.json()

                if "profile_picture_url" in response_json_2:
                    display_image = response_json_2.get("profile_picture_url")
                else:
                    display_image = ""

                name = response_json_2.get("name")

                obj = {'name': name, "profile_image": display_image, "text": text, 'comment_urn': comment_urn}

                if element.get('replies'):
                    replies = element.get('replies').get('data')
                    obj['replies'] = insta_social_actions_data_organizer(replies,headers)

                data.append(obj)
            else:
                obj = {'name': "", "profile_image": "", "text": "", "comment_urn": "","replies" :""}
                data.append(obj)
    return data

def insta_socialactions(post_urn,access_token):

    url = f"https://graph.facebook.com/{post_urn}?fields=like_count,comments_count"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url=url, headers=headers)

    response_json = response.json()



    t_likes = response_json.get("like_count")


    t_comments = response_json.get("comments_count")

    form = Post_urn.objects.get(urn=post_urn)
    form.post_likes = t_likes
    form.post_comments = t_comments
    form.save()


    url = f"https://graph.facebook.com/v17.0/{post_urn}/comments/?fields=from,text,like_count,media,replies{{like_count,from,text}}"

    response = requests.get(url=url,headers=headers)

    response_json_1 = response.json()

    elements = response_json_1.get("data")

    data = insta_social_actions_data_organizer(elements,headers)

    return t_likes, t_comments, data












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
        "caption": request.POST.get("caption")
    }

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.post(url, headers=headers, json=data)
    # print(response.json())
    return redirect("facebook_redirect")



def facebook_page_data(accesstoken):

    url = "https://graph.facebook.com/v17.0/me/accounts?fields=access_token,id,name"

    headers = {
        "Authorization": f"Bearer {accesstoken}"
    }

    response = requests.get(url,headers=headers)
    # print(response.json())
    data = {}

    return response.json().get("data")





def get_instagram_user_data(accesstoken):

    url = "https://graph.facebook.com/v17.0/me/accounts?fields=instagram_business_account"

    headers = {
        "Authorization": f"Bearer {accesstoken}"
    }

    response = requests.get(url,headers=headers)

    data = {}
    print(response.json())
    instaid = None

    accounts = []

    for _ in response.json().get('data'):
        if _.get("instagram_business_account"):
            instaid = _.get("instagram_business_account")["id"]

            try:
                url = f"https://graph.facebook.com/v17.0/{instaid}?fields=name,profile_picture_url"
                response = requests.get(url,headers=headers)

                accounts.append(response.json())

            except Exception as e:

                    print(e)
    return accounts


def fb_video_post(data,images,post_model,sharepage):
    # post = {
    #     "url": images[0].image_url,
    #     "caption": post_model.post
    # }
    payload = {
        'description': post_model.post,
    }
    video_path = os.path.join(settings.BASE_DIR, "media/" + str(images[0].image))
    print(video_path)

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


def instagram_post_single_media(page_id,access_token,media,post,page):

    print("Excuting Single Instagram Post Function")
    url = f"https://graph.facebook.com/v17.0/{page_id}/media/"
    print(url)
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

    print("data is",data)
    response = requests.post(url, headers=headers, json=data)

    mediaid = response.json().get('id')
    print("media id is",mediaid,response.json())

    if data.get('media_type') == 'VIDEO':
        while True:
            print("Waiting for 10s till the media is created")
            time.sleep(10)
            check_url = f"https://graph.facebook.com/v17.0/{mediaid}?fields=status_code,status,id"

            response = requests.request("GET",url=check_url,headers=headers)
            status = response.json().get("status_code")
            print(status)
            if status == "FINISHED":
                break
            elif status == "ERROR" or status == "FATAL":
                print("Error Has Occured")
                return
            else:
                pass


    url = f"https://graph.facebook.com/v17.0/{page_id}/media_publish"

    data = {
        'creation_id': mediaid
    }



    response = requests.post(url, headers=headers, data=data)
    response = response.json()
    post_id = response.get('id')
    print("Post id is ",post_id,response)
    post_urn = Post_urn.objects.create(org=page, urn=post_id)
    post_urn.save()
    post.post_urn.add(post_urn)
    print("Post Successfull Created")



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
        'image/png': 'png',   # PNG image
        'image/gif': 'gif',   # GIF image
        'video/mp4': 'mp4',   # MP4 video

    }

    return mime_to_extension.get(content_type, 'unknown')

def getmediaid(image,data,post):

    url =f"https://graph.facebook.com/{data['page_id']}/photos?published=false&temporary=true"

    headers = {
        "Authorization": f"Bearer {data['page_access_token']}"
    }

    data = {
        "url": image.image_url
    }

    response = requests.post(url, headers=headers, data=data)

    # image.save()

    return response.json()

def create_fb_post(page_id,access_token,media,post,sharepage):
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





def facebook_post_multiimage(data,images,post,sharepage):

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
            response_id = getmediaid(images[_], data,post)["id"]
            images[_].image_posted = response_id
            images[_].save()
            data_post[f"attached_media[{_}]"] = f'{{"media_fbid": "{response_id}"}}'

    print("Data ",data_post)

    response = requests.post(url,headers=headers,data=data_post)
    response = response.json()
    post_id = response["id"]
    print(post_id)
    post_urn = Post_urn.objects.create(org = sharepage,urn = post_id)
    post_urn.save()
    print("Post Successfull Created")

    post.post_urn.add(post_urn)

def create_insta_post(page_id,access_token,media,post,page):

    if media:
        if len(media)>1:
            instagram_multi_media(page_id,access_token,media,post,page)
        else:
            instagram_post_single_media(page_id,access_token,media,post,page)
    else:
        pass


def facebook_post_video(data,video,post,sharepage):


    page_id = data['page_id']

    url = f"https://graph.facebook.com/{page_id}/videos"
    headers = {
        "Authorization": f"Bearer {data['page_access_token']}"
    }
    data_post = {
        'description': post.post
    }
    if (len(video) != 0):
        data_post['file_url'] = video[0].image_url
    response = requests.post(url, headers=headers, data=data_post)
    response = response.json()
    post_id = response.get('id')

    post_urn = Post_urn.objects.create(org=sharepage, urn=post_id)
    post_urn.save()

    post.post_urn.add(post_urn)



def get_instagram_image_id(image,page_id,access_token):
    url = f"https://graph.facebook.com/v17.0/{page_id}/media?is_carousel_item=true"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    data_post = {
        "image_url":image.image_url
    }
    print(data_post)

    # data_post = {
    #     "image_url":"https://messangel.caansoft.com/uploads/social_prefrences/image/1691750723366-homepage-seen-computer-screen_CvuwFmi.jpg"
    # }

    response = requests.post(url,headers=headers,data=data_post)
    print(response.json())
    return response.json()

def get_instagram_video_id(video,page_id,access_token):
    url = f"https://graph.facebook.com/v17.0/{page_id}/media?is_carousel_item=true"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    data_post = {
        'video_url':{video.image_url},
        'media_type':'VIDEO',
    }
    print(data_post)
    # data_post = {
    #     'video_url':"https://messangel.caansoft.com/uploads/social_prefrences/video/1691750720923-send_WqThsJC.mp4",
    #     'media_type':'VIDEO',
    # }

    response = requests.post(url, headers=headers, data=data_post)
    print(response.json())
    return response.json()


def get_instagram_media_id(data_post,headers,page_id):
    print("Getting Media id")
    url = f"https://graph.facebook.com/v17.0/{page_id}/media?media_type=CAROUSEL"

    response = requests.request("POST", url, headers=headers, data=data_post)

    if response.json().get('id'):
        return response
    else:
        print(response.json())
        print("Sleeping For 30s till data arrive")
        time.sleep(30)
        response = get_instagram_media_id(data_post,headers,page_id)

    return response


def instagram_multi_media(page_id,access_token,media,post,page):
    is_video = False
    childern_list = []
    for image in media:
        childern_id = None
        if image.image.name.endswith('.mp4'):
            childern_id = get_instagram_video_id(image,page_id,access_token).get('id')
            is_video =True
        else:
            childern_id = get_instagram_image_id(image, page_id, access_token).get('id')
        childern_list.append(childern_id)


    headers = {
        "Authorization": f"Bearer {access_token}",
        'Content-Type': 'application/json',
    }
    data_post = json.dumps({
        "caption": post.post,
        "children": ",".join(childern_list)
    })
    print(data_post)

    media_id = get_instagram_media_id(data_post,headers,page_id).json().get('id')
    print(media_id)
    if is_video:
        while True:
            print("Waiting for 10s till the media is created")
            time.sleep(10)
            check_url = f"https://graph.facebook.com/v17.0/{media_id}?fields=status_code,status,id"

            response = requests.request("GET", url=check_url, headers=headers)
            print(response.json())
            status = response.json().get("status_code")
            print(status)
            if status == "FINISHED":
                break
            elif status == "ERROR" or status == "FATAL":
                print("Error Has Occured")
                return
            else:
                pass


    url_2 = f"https://graph.facebook.com/v17.0/{page_id}/media_publish"

    data_post_2 = {
        "creation_id": media_id
    }

    response_2 = requests.post(url_2,headers=headers,data=data_post_2)
    response_2 = response_2.json()
    print(response_2)

    post_id = response_2.get('id')
    post_urn = Post_urn.objects.create(org=page, urn=post_id)
    post_urn.save()

    post.post_urn.add(post_urn)






def create_l_multimedia(images, org_id, access_token_string,clean_file,
                        get_video_urn,image_m,upload_video,post_video_linkedin,
                        org,get_img_urn,upload_img,post_single_image_linkedin,
                        post,post_linkedin):
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
                response_json['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest'][
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
                        post.save()
                        print("Video Posted successfully.")

                    else:
                        print("Post Failed" + response.status_code)

            else:
                print("Video did not Register")

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
                        if response.status_code == 201:
                            print("Image successfully uploaded to LinkedIn.")

            count = 0
            for image in image_list:
                print(image)
                if 'id' in image:
                    count += 1

            if count < 2:
                image_list = image_list[0]
                response = post_single_image_linkedin(access_token_string, org_id, post, image_list)
                # print("Response ", response.json())
                if response.status_code == 201:
                    post_id_value = response.headers.get('x-restli-id')
                    post_urn, created = Post_urn.objects.get_or_create(org=org, urn=post_id_value)
                    if created:
                        post_urn.urn = post_id_value
                        post_urn.org = org
                        post_urn.save()
                    post.post_urn.add(post_urn)
                    post.save()


                else:
                    print("API request failed with status code:", response.status_code)
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
                    post.save()
                else:
                    print("API request failed with status code:", response.status_code)
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
            post.save()
        else:
            print("API request failed with status code:", response.status_code)

def post_nested_comment_linkedin(social,access_token,post_urn,reply,comment_urn):
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

    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 201:
        response = response.json()
        print("Replied to Comment successfully.")
    else:
        print("Failed to reply.")

    return response

def get_nested_comments(access_token,comment_urn):
    encoded_urn = quote(comment_urn, safe='')
    url = "https://api.linkedin.com/rest/socialActions/" + encoded_urn + "/comments"
    payload = {}
    headers = {
        'Linkedin-Version': '202304',
        'X-Restli-Protocol-Version': '2.0.0',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Cookie': 'lidc="b=VB86:s=V:r=V:a=V:p=V:g=4552:u=55:x=1:i=1689679535:t=1689752271:v=2:sig=AQHrXpQbD6C1r_eMUoL9o6xmwpPa1AEs"; lidc="b=VB86:s=V:r=V:a=V:p=V:g=4546:u=55:x=1:i=1689314606:t=1689334414:v=2:sig=AQHSFW1fjeXULNO8CiDc8_rZkoMXJMK3"; bcookie="v=2&3da7cbe9-1e10-4108-8734-c492859ca8d8"'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    if response.status_code == 200:
        response = response.json()
        replies = []
        if len(response['elements']) > 0:
            for element in response['elements']:
                urls = []
                if 'content' in element:
                    for content in element['content']:
                        if 'url' in content:
                            urls.append(content['url'])
                text = element['message']['text']
                actor = element['actor']
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
                    obj = {'name': name, "profile_image": display_image, "text": text, "urls": urls}
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
                        display_image = response['profilePicture']['displayImage~']['elements'][0]['identifiers'][0]['identifier']
                    else:
                        display_image = ''
                    name = response['firstName']['localized']['en_US'] + " " + response['lastName']['localized']['en_US']

                    obj = {'name': name, "profile_image": display_image, "text": text, "urls": urls}
                    replies.append(obj)
        else:
            print("No Replies on Comments")
            obj = {}
            replies.append(obj)

    else:
        print("Fetching Replies Failed")

    return replies


def create_comment(access_token, post_urn, comment,social):

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

    if response.status_code == 201:
        response = response.json()
        print("Comment created successfully.")
        print(response['$URN'])
    else:
        print("Failed to create comment.")
        print(response.json())
    return response

def ugcpost_socialactions(urn, access_token_string,linkedin_post):
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
            if comment_urn:
                result = get_nested_comments(access_token, comment_urn)
                replies = result
            else:
                replies = []
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
                    obj = {'name': name, "profile_image": display_image, "text": texts, "urls": urls ,"comment_urn": comment_urn}
                    obj['replies'] = replies

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
                        display_image = response['profilePicture']['displayImage~']['elements'][0]['identifiers'][0]['identifier']
                    else:
                        display_image = ''
                    name = response['firstName']['localized']['en_US'] + " " + response['lastName']['localized']['en_US']


                    obj = {'name': name, "profile_image": display_image, "text": texts, "urls": urls,"comment_urn": comment_urn}
                    obj['replies'] = replies
                    data.append(obj)
            else:
                obj = {'name': "", "profile_image": "", "text": "", "urls": urls, "comment_urn": ""}
                replies = {}
                obj['replies'] = replies
                data.append(obj)
        return t_likes, t_comments, data
    else:
        data = []
        obj = {}
        data.append(obj)

    return t_likes, t_comments, data


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
            if comment_urn:
                result = get_nested_comments(access_token, comment_urn)
                replies = result
            else:
                replies = {}
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
                    obj = {'name': name, "profile_image": display_image, "text": texts, "urls": urls,"comment_urn": comment_urn}
                    obj['replies'] = replies
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
                    name = response['firstName']['localized']['en_US'] + " " + response['lastName']['localized']['en_US']

                    obj = {'name': name, "profile_image": display_image, "text": texts, "urls": urls,"comment_urn": comment_urn}
                    obj['replies'] = replies
                    data.append(obj)
            else:
                obj = {'name': "", "profile_image": "", "text": "", "urls": urls, "comment_urn": ""}
                replies = {}
                obj['replies'] = replies
                data.append(obj)
            return t_likes, t_comments, data
    else:
        data = []
        obj = {}
        data.append(obj)

    return t_likes, t_comments, data




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




def linkedin_retrieve_access_token(self):
    user = self.request.user
    if len(SocialAccount.objects.filter(user=user.id,provider='linkedin_oauth2')) > 0:
        social = SocialAccount.objects.get(user=user.id, provider='linkedin_oauth2')
        if social:
            ids = SharePage.objects.filter(user=social.pk)
            access_token = SocialToken.objects.filter(account_id=social)
            access_token_string = ', '.join(str(obj) for obj in access_token)
            posts = PostModel.objects.filter(user=user.id)

            return  posts, access_token_string, ids, social
    else:
        posts = ''
        access_token_string = ''
        ids = ''
        social = ''
        return posts, access_token_string, ids, social


def linkedin_get_user_organization(accesstoken):

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
        my_object['key'] = id
        my_object['name'] = localizedName
        organization_count = SharePage.objects.filter(org_id=id).count()
        if organization_count > 0:
            my_object['checked'] = True
        else:
            my_object['checked'] = False
        my_list.append(my_object)
    data = my_list
    return data

    data = {}
    response.json().get("data")



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
                print(f"Image pixel count reduced and saved as {output_path}")
            else:
                # No need to resize, save the image as it is
                image.save(output_path)
                print(f"Image pixel count is within the specified limit. Image saved as {output_path}")
    except Exception as e:
        print(f"Error occurred while processing the image: {e}")



def get_img_urn(org_id,access_token_string):
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
    print(response.json())
    return response

def get_video_urn(org_id,access_token_string):

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

    image_path = os.path.join(settings.BASE_DIR,"media/" + str(image_file))
    print(image_path)
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

def upload_video(upload_url,video_file):
    url = upload_url
    video_path = os.path.join(settings.BASE_DIR,"media/" + str(video_file))
    # video_path = "/Users/anasrehman/PycharmProjects/social_automation/social_auto/media/videos/" + str(video_file)

    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Linkedin-Version': '202304',
        'Content-Type': 'application/octet-stream',
    }
    with open(video_path, 'rb') as file:
        response = requests.request("PUT", url, headers=headers, data=file)
        if response.status_code == 201:
            print("Video Succesfully Uploaded")
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



def post_linkedin(image_list,post,org_id,access_token):
    url = "https://api.linkedin.com/rest/posts"

    print(post)

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
    # print(response)
    return response




def post_single_image_linkedin(access_token_string,org_id,post,image_list):
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




def meta_comments(urn,text,media,access_token):

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
        if extension in ['jpg','png']:
            data['attachment_url'] = get_image_url(media).get('files')[0].get('path')
        elif extension in ['gif']:
            pass
        elif extension in ['mp4']:
            video_path = os.path.join(settings.BASE_DIR,"media/" + "videos/send.mp4")
            files = [
                ('source', ('send.mp4',
                            open(video_path,
                                 'rb'), 'application/octet-stream'))
            ]




    response = requests.post(url=url, headers=headers, data=data, files=files)
    return response.json()


def meta_nested_comment(urn,text,media,access_token,provider_name):


    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    files = []
    data = {}
    if text:
        data['message'] = text

    if provider_name == "facebook":
        url = f"https://graph.facebook.com/{urn}/comments"
        if media and media!= '':
            extension = get_file_extension(media.content_type)
            if extension in ['jpg','png']:
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

    elif provider_name == "instagram":
        url = f"https://graph.facebook.com/{urn}/replies"


    response = requests.post(url=url,headers=headers,data=data,files=files)

    response_json = response.json()






