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



def facebook_page_data(accesstoken):

    url = "https://graph.facebook.com/v17.0/me/accounts?fields=access_token,id,name"

    headers = {
        "Authorization": f"Bearer {accesstoken}"
    }

    response = requests.get(url,headers=headers)
    # print(response.json())
    data = {}

    return response.json().get("data")





def instagram_id(accesstoken):

    url = "https://graph.facebook.com/v17.0/me/accounts?fields=instagram_business_account"

    headers = {
        "Authorization": f"Bearer {accesstoken}"
    }

    response = requests.get(url,headers=headers)

    data = {}
    print(response.json())
    instaid = None



    for _ in response.json().get('data'):
        if _.get("instagram_business_account"):
            instaid = _.get("instagram_business_account")["id"]

    try:
        url = f"https://graph.facebook.com/v17.0/{instaid}?fields=name,profile_picture_url"
        response = requests.get(url,headers=headers)
        return response.json()

    except Exception as e:

        print(e)










def facebookpost(request,data,image,post,sharepage):
    post = {
            "url": image.image_url,
            "caption": request.POST['post']
        }

    url = f"https://graph.facebook.com/{data['page_id']}/photos"

    headers = {
        "Authorization": f"Bearer {data['page_access_token']}"
    }

    response = requests.post(url, headers=headers, json=post)
    response = response.json()
    post_id = response.get('id')
    post_urn = Post_urn.objects.create(org=sharepage, urn=post_id)
    post_urn.save()

    post = PostModel.objects.get(id=post.id)

    post.post_urn.add(post_urn)
    post.save()





def instagrampost(request,data,access_token,image,post_model,sharepage):
    post = {
            "image_url": image.image_url,
            "caption": request.POST['post']

        }
    url = f"https://graph.facebook.com/v17.0/{data['insta_id']}/media/"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.post(url, headers=headers, json=post)

    mediaid = response.json()['id']

    url = f"https://graph.facebook.com/v17.0/{data['insta_id']}/media_publish"

    data = {
        'creation_id': mediaid
    }

    response = requests.post(url, headers=headers, data=data)
    response = response.json()
    post_id = response.get('id')
    post_urn = Post_urn.objects.create(org=sharepage, urn=post_id)
    post_urn.save()

    post = PostModel.objects.get(id=post_model.id)

    post.post_urn.add(post_urn)
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





# ...

def save_image_from_url(image_url):

    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    image = image.convert('RGB')
    image_buffer = BytesIO()
    image.save(image_buffer, format='JPEG', optimize=True, quality=85)
    image_buffer.seek(0)

    content_file = ContentFile(image_buffer.getvalue())


    return content_file


def getmediaid(image,data,post):

    url =f"https://graph.facebook.com/{data['page_id']}/photos?published=false&temporary=true"

    headers = {
        "Authorization": f"Bearer {data['page_access_token']}"
    }

    data = {
        "url":image.image_url
    }

    response = requests.post(url,headers=headers,data=data)





    # image.save()

    return response.json()


def facebookmultiimage(request,data,images,post,sharepage):

    url = f"https://graph.facebook.com/{data['page_id']}/feed"

    data_post = {
        "message":request.POST['post']
    }
    headers = {
        "Authorization": f"Bearer {data['page_access_token']}"
    }
    # i = 0
    for _ in range(len(images)):
        response_id = getmediaid(images[_], data,post)["id"]
        images[_].image_posted = response_id
        images[_].save()
        data_post[f"attached_media[{_}]"] = f'{{"media_fbid": "{response_id}"}}'

    response = requests.post(url,headers=headers,data=data_post)
    response = response.json()
    post_id = response["id"]

    post_urn = Post_urn.objects.create(org = sharepage,urn = post_id)
    post_urn.save()

    post = PostModel.objects.get(id=post.id)

    post.post_urn.add(post_urn)
    post.save()



def media_id_insta(image,data,access_token):
    url = f"https://graph.facebook.com/v17.0/{data['insta_id']}/media?is_carousel_item=true"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    data_post = {
        "image_url":image.image_url
    }

    response = requests.post(url,headers=headers,data=data_post)
    print(response.json())
    return response.json()


def instagrammultiimage(request,data,access_token,images,post,sharepage):

    childern_list = []
    for _ in images:
        childern_list.append(media_id_insta(_,data,access_token)["id"])


    url = f"https://graph.facebook.com/v17.0/{data['insta_id']}/media?media_type=CAROUSEL"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    data_post = {
        "caption": request.POST['post'],
        "children": ",".join(childern_list)
    }
    response_1 = requests.post(url,headers=headers,data=data_post)

    url_2 = f"https://graph.facebook.com/v17.0/{data['insta_id']}/media_publish"

    data_post_2 = {
        "creation_id": response_1.json()['id']
    }

    response_2 = requests.post(url_2,headers=headers,data=data_post_2)
    response_2 = response_2.json()

    post_id = response_2.get('id')
    post_urn = Post_urn.objects.create(org=sharepage, urn=post_id)
    post_urn.save()

    post = PostModel.objects.get(id=post.id)

    post.post_urn.add(post_urn)
    post.save()



def create_l_multimedia(images, org_id, access_token_string,clean_file,
                        get_video_urn,image_m,upload_video,post_video_linkedin,
                        org,get_img_urn,upload_img,post_single_image_linkedin,
                        post,post_linkedin):
    if images:
        result = clean_file(images)
        file_extension = result[1]
        video_file = result[0]
        if file_extension == 'mp4':
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

                response = upload_video(upload_url, video_file, image_urn, access_token_string)
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

        else:
            image_list = []

            for a in image_m.images.all():
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



def ugcpost_socialactions(urn, access_token_string):
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
    texts = [element['message']['text'] for element in response_json3['elements']]
    form.comments = texts
    form.save()

    return response


def linkedin_post_socialactions(urn, access_token_string):
    encoded_urn = quote(urn, safe='')
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
    texts = [element['message']['text'] for element in response_json3['elements']]
    form.comments = texts
    form.save()
    return response


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
    user = self.request.user  # Set the user to the logged-in user
    social = SocialAccount.objects.get(user=user.id)
    ids = SharePage.objects.filter(user=social)
    access_token = SocialToken.objects.filter(account_id=social)
    access_token_string = ', '.join(str(obj) for obj in access_token)
    posts = PostModel.objects.filter(user=user.id)

    return  posts, access_token_string,ids


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

def upload_video(upload_url,video_file,image_urn,access_token_string):
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

def save_files(image,post):


    image_url = get_image_url(image)
    image_path = image_url.get('files')[0].get('path')
    image_model = ImageModel(image=image,image_url = image_path)
    image_model.save()
    post = PostModel.objects.get(id=post.id)
    post.images.add(image_model)
    post.save()

    return image_model
def clean_file(images):
    for image in images:
        file = image
        if file:
            file_extension = file.name.split('.')[-1].lower()
            if file_extension == 'mp4':
                return file, file_extension
            else:
                return images, file_extension

        # return None
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

    return response.json()