import asyncio

from asgiref.sync import sync_to_async
from celery import signals
from django.urls import reverse
from .restapis import *
from .models import PostModel,SharePage,Post_urn
from celery import shared_task

from allauth.socialaccount.models import SocialAccount, SocialToken ,SocialApp
import datetime

from django.dispatch import receiver
from django.urls import reverse_lazy


from django.shortcuts import redirect, reverse

from datetime import datetime
from django.core.exceptions import PermissionDenied

from datetime import datetime, timezone ,timedelta
from django.utils import timezone
import time
from django.db.models.signals import m2m_changed, pre_delete

from .serializer import SharePageSerializer


# @receiver(pre_delete , sender = SocialAccount)
# def social_app_deleted(sender,instance,**kwargs):
#     user = instance.user
#
#     if instance.provider == 'linkedin_oauth2':
#         instance_share_pages = SharePage.objects.filter(user = user , provider = "linkedin" )
#     else:
#         instance_share_pages = SharePage.objects.filter(user = user , provider = instance.provider )
#
#     instance_share_pages.delete()


# post_save_signal = Signal()
#
# post_update_signal = Signal()

# @receiver(post_save, sender=PostModel)
# def handle_list3(sender, **kwargs):
#     post = kwargs.get('instance')
#     # logic3(announce)
#     modal-content py-2 text-left px-6(post)
# def call(sender,instance,**kwargs):
#     instance)
#
# post_save.connect(call,sender=PostModel)




#
# @receiver(m2m_changed, sender=PostModel.prepost_page.through)
# def handle_m2m_change(sender, instance, action, reverse, pk_set, **kwargs):
#     if action == 'post_add' and not reverse and instance == PostModel.objects.last():
#         announce = kwargs.get('instance')
#         instance)
#



# @receiver(post_s, sender=PostModel)
# def publish_or_schedule_post(sender, share_pages, images, instance, **kwargs):
#     # Check if the post is newly created
#     if instance:
#         if instance.prepost_page.exists():
#             pass
#         else:
#             for page in share_pages:
#                 instance.prepost_page.add(page)
#
#             image_object = []
#             if images:
#                 for image in images:
#                     image_object.append(save_files(image, instance))
#         if instance.status == 'DRAFT':
#             # raise PermissionDenied("This post is in draft status. Cannot proceed.")
#             return redirect(reverse("my_posts", kwargs={'pk': instance.user.id}))
#
#         elif instance.status == 'PUBLISHED':
#                 publish_post_on_social_media(instance)
#         elif instance.status == 'SCHEDULED':
#             current_datetime = timezone.now()
#             given_datetime_str = instance.schedule_datetime
#             given_datetime = timezone.make_aware(given_datetime_str)
#
#             time_remaining = given_datetime - current_datetime
#             days = time_remaining.days
#             hours, remainder = divmod(time_remaining.seconds, 3600)
#             minutes, seconds = divmod(remainder, 60)
#
#             f"Time remaining: {days} days, {hours} hours, {minutes} minutes, {seconds} seconds.")
#
#             # time_remaining = instance.schedule_datetime - timezone.now()
#             # Schedule the task to publish the post on the scheduled date
#             try:
#                 schedule_publish_task.apply_async(args=(instance,), countdown=time_remaining.total_seconds())
#             except:
#                 return redirect(reverse("my_posts", kwargs={'pk': instance.user.id}))
#

# @receiver(m2m_changed, sender=PostModel.prepost_page.through)
# def handle_prepost_page_change(sender, instance, action, pk_set, **kwargs):
#     if action == 'post_add':
#         # The 'post_add' action is triggered when objects are added to the ManyToMany field
#         # Update the related objects here
#         # pk_set contains the primary keys of the related objects that were added
#         for pk in pk_set:
#             # Update the related objects as needed
#             related_obj = SharePage.objects.get(pk=pk)
#             # Perform the necessary updates
#             # ...
#
#     elif action == 'post_remove':
#         # The 'post_remove' action is triggered when objects are removed from the ManyToMany field
#         # Update the related objects here
#         # pk_set contains the primary keys of the related objects that were removed
#         for pk in pk_set:
#             # Update the related objects as needed
#             related_obj = SharePage.objects.get(pk=pk)
#             #

def publish_post_on_social_media(instance):
    # Put your code to publish the post on the social media platform here
    # For example, if the post platform is "linkedin," use your existing code to publish on LinkedIn
    # Remember to handle any exceptions that may occur during the publishing process
    share_page = instance.prepost_page.all()
    images = instance.images.all()


    for page in share_page:

        if page.provider == "linkedin":
            socialaccount = SocialAccount.objects.get(user=page.user.id, provider="linkedin_oauth2")
            access_token = SocialToken.objects.filter(account=socialaccount)[0]
            access_token_string = str(access_token)
            org_id = page.org_id
            image_m = PostModel.objects.get(id=instance.id)
            org = SharePage.objects.get(id=page.id)
            post = instance
            create_l_multimedia(images, org_id, access_token_string, clean_file,
                                get_video_urn, image_m, upload_video, post_video_linkedin,
                                org, get_img_urn, upload_img, post_single_image_linkedin,
                                    post, post_linkedin)
        elif page.provider == "facebook":

            post = instance
            page_id = page.org_id
            access_token = page.access_token
            media = images
            share_page = page

            create_fb_post(page_id, access_token, media, post, share_page)

        elif page.provider == "instagram":

            access_token = page.access_token
            post = instance
            page_id = page.org_id
            media = images
            create_insta_post(page_id,access_token,media,post,page)
        else:
            pass




@shared_task
def schedule_signals_task(instance):
    key = f"POST {instance.id} USER {instance.user.id}"
    task, created = CeleryTask.objects.get_or_create(key=key, task_name=f"POST {instance.id}")
    try:
        if (not created and task.status != "PROCESSING") or created:
            if instance:
                for image in instance.images.all():
                    try:
                        save_file1(image)
                    except Exception as e:
                        # f"An error occurred: {str(e)}")
                        instance.status = 'FAILED'
                        instance.save()


                if instance.status == 'DRAFT':
                    pass
                elif instance.status == 'PROCESSING':
                        publish_post_on_social_media(instance)
                elif instance.status == 'SCHEDULED':
                    current_datetime = timezone.now()
                    given_datetime_str = instance.schedule_datetime

                    if given_datetime_str < current_datetime:
                        schedule_publish_task(instance)
                    else:
                        pass
                task.status = "FINISHED"
                task.result = f"SUCCESS {instance.id}"
                task.save()
            else:
                pass

    except PostModel.DoesNotExist:
        pass
    except Exception as e:
        task.status = "FAILED"
        task.result = f"SUCCESS {instance.id}"
        task.save()





@shared_task
def schedule_publish_task(instance):
    publish_post_on_social_media(instance)



# @sync_to_async()
# def get_share_pages(id,provider):
#     qs = SharePage.objects.filter(user__id = id,provider= provider)
#     serialize_data = SharePageSerializer(qs,many=True)
#     return json.loads(json.dumps(serialize_data.data))
#
#
# @sync_to_async()
# def _get_post_urn(id):
#     qs = Post_urn.objects.filter(org__org_id=id,is_deleted = False).values_list('urn',flat=True)
#     seralized_data = list(qs)
#     return json.loads(json.dumps(seralized_data))
#
# @sync_to_async()
# def _make_fb_courtine(fb_share_pages):
#     fb_requests = []
#     since = datetime.now(timezone.utc).replace(minute=0, hour=0, second=0, microsecond=0)
#     until = datetime.now(timezone.utc)
#     for page in range(len(fb_share_pages)):
#         fb_post_urns =_get_post_urn(fb_share_pages[page].get('org_id'))
#         access_token = fb_share_pages[page].get('access_token')
#         org_id = fb_share_pages[page].get('org_id')
#         fb_requests.append(fb_post_insights(fb_post_urns, access_token, org_id, since, until))
#
#     return fb_requests
#
#
# async def process_page(share_page, since, until,task):
#     status(2)
#     access_token = share_page.get('access_token')
#     org_id = share_page.get('org_id')
#     provider = share_page.get('provider')
#     share = await get_share_pages(1,provider)
#     if provider == "facebook":
#         print("provider")
#         fb_post_urns = await _get_post_urn(share_page.get('org_id'))
#         task.append(fb_post_insights(fb_post_urns, access_token, org_id, since, until))
#     else:
#         pass
#
#     return task



@shared_task
def gather_post_insight(instance):

    try:
        since = datetime.now(timezone.utc).replace(minute=0,hour=0,second=0,microsecond=0)
        until = datetime.now(timezone.utc)


        if instance.provider == "facebook":
            urn_list = Post_urn.objects.filter(org=instance, is_deleted=False).values_list('urn', flat=True)
            result = fb_post_insights(urn_list,instance,since,until)
            # print(result)
            update_db_create_call( result[0], result[1], result[2], instance)

        elif instance.provider == "instagram":

            since = datetime.now(timezone.utc) - timedelta(days=1)
            until = datetime.now(timezone.utc)


            result = instagram_account_insights(instance , since , until)
            update_db_create_call(result[0], result[1], result[2], instance)
        elif instance.provider == "linkedin":
            result = linkedin_share_stats(instance, since, until)
            update_db_create_call(result[0], result[1], result[2], instance)
        else:
            pass
    except Exception as e:
        raise e



def update_db_create_call(total_likes,total_comments,total_followers,share_page):
    local_time = datetime.now()
    utc_date_time = local_time.astimezone(pytz.utc)
    day_start_time = utc_date_time.replace(minute=0, second=0,hour=0, microsecond=0)
    current_time = utc_date_time.replace(minute=0, second=0, microsecond=0)
    one_hour_ago = (current_time - timedelta(hours=1))


    try:
        previous_entry = SocialStats.objects.filter(org=share_page,
                                                      created_at__gte = day_start_time,created_at__lte = one_hour_ago)
        if previous_entry:
            previous_likes = previous_entry.values('t_likes').aggregate(Sum('t_likes'))['t_likes__sum'] or 0
            previous_comments = previous_entry.values('t_comments').aggregate(Sum('t_comments'))['t_comments__sum'] or 0
            previous_follower = previous_entry.last().t_followers

            new_followers = total_followers - previous_follower if total_followers - previous_follower > 0 else 0
            total_followers = total_followers
            total_likes = updated_likes(total_likes,previous_entry,previous_likes)
            # print(f"Total likes {total_likes}")
            # print(f"previous likes {previous_likes}")
            # print(f"previous comments {previous_comments}")
            # print(f"Total followers {total_followers}")

            total_comments = updated_comments(total_comments,previous_entry,previous_comments)
            # print(f"Total likes {total_comments}")



        else:
            total_likes = total_likes
            total_comments = total_comments

            previous_entry = SocialStats.objects.last()
            if previous_entry:
                previous_follower = previous_entry.t_followers
                new_followers = total_followers - previous_follower if total_followers - previous_follower > 0 else 0
                total_followers = total_followers
            else:
                new_followers = total_followers
                total_followers = total_followers



        current_entry , created = SocialStats.objects.get_or_create(org=share_page, created_at=current_time)
        current_entry.t_likes = total_likes
        current_entry.t_comments = total_comments
        current_entry.new_followers = new_followers
        current_entry.t_followers = total_followers

        current_entry.save()

    except Exception as e:
        raise e

    # if previous_entry:
    #     stats.t_followers = 0 if previous_entry - result[3] < 0 else previous_entry - result[3]
    # else:
    #     stats.t_followers = result[3]


def updated_likes(total_likes,previous_entry,previous_likes):

    if previous_likes != 0 and total_likes == 0:
        previous_entry.update(t_likes=0)
        previous_likes = 0
        # turn all the previous entries to 0
        return 0
    elif previous_likes > total_likes:

        deleted_count = previous_likes - total_likes
        exact_count = previous_entry.filter(t_likes=deleted_count)
        if exact_count.exists():
            exact_count.update(t_likes=0)
        else:
            entries = previous_entry.values('id').annotate(total_count=Sum('t_likes'))
            exact_count_entries = entries.filter(total_count=deleted_count)
            if exact_count_entries.exists():
                for entry in exact_count_entries:
                    previous_entry.filter(id=entry['id']).update(t_likes=0)
            else:
                candidates = entries.filter(total_count__gt=deleted_count)
                if candidates.exists():
                    i = 0
                    while (deleted_count != 0):
                        candidate = SocialStats.objects.get(id=candidates[i]['id'])
                        t_likes = candidate.t_likes
                        new_t_likes = t_likes - deleted_count if t_likes - deleted_count > 0 else 0
                        deleted_count = deleted_count - t_likes if deleted_count - t_likes > 0 else 0
                        candidate.t_likes = new_t_likes
                        candidate.save()
                        i = i + 1

        return 0

    # It means not all comments are delete but some comments are deleted so
    # we will first find which entry contain the value of new count deleted and subtract from them

    else:
        # it has two possible conditions and we are handling it with same condition
        # if previous likes are less than total new like just subtract and and create new value or update same value
        total_likes = total_likes - previous_likes
        return total_likes

def updated_comments(total_comments,previous_entry,previous_comments):
    if previous_comments != 0 and total_comments == 0:
        previous_entry.update(t_comments=0)
        # turn all the previous entries to 0

        return 0
    elif previous_comments > total_comments:

        deleted_count = previous_comments - total_comments
        exact_count = previous_entry.filter(t_comments=deleted_count)
        if exact_count.exists():
            exact_count.update(t_comments=0)
        else:
            entries = previous_entry.values('id').annotate(total_count=Sum('t_comments'))
            exact_count_entries = entries.filter(total_count=deleted_count)
            if exact_count_entries.exists():
                for entry in exact_count_entries:
                    previous_entry.filter(id=entry['id']).update(t_comments=0)
            else:
                candidates = entries.filter(total_count__gt=deleted_count)
                if candidates.exists():
                    i = 0
                    while (deleted_count != 0):
                        candidate = SocialStats.objects.get(id = candidates[i]['id'])
                        t_comments = candidate.t_comments
                        new_t_comments = t_comments - deleted_count if t_comments - deleted_count > 0 else 0
                        deleted_count = deleted_count - t_comments if deleted_count - t_comments > 0 else 0
                        candidate.t_comments= new_t_comments
                        candidate.save()
                        i = i+1


def update_db_create_call(total_likes,total_comments,total_followers,share_page):
    local_time = datetime.now()
    utc_date_time = local_time.astimezone(pytz.utc)
    day_start_time = utc_date_time.replace(minute=0, second=0,hour=0, microsecond=0)
    current_time = utc_date_time.replace(minute=0, second=0, microsecond=0)
    one_hour_ago = (current_time - timedelta(hours=1))


    try:
        previous_entry = SocialStats.objects.filter(org=share_page,
                                                      created_at__gte = day_start_time,created_at__lte = one_hour_ago)
        if previous_entry:
            previous_likes = previous_entry.values('t_likes').aggregate(Sum('t_likes'))['t_likes__sum'] or 0
            previous_comments = previous_entry.values('t_comments').aggregate(Sum('t_comments'))['t_comments__sum'] or 0
            previous_follower = previous_entry.last().t_followers

            new_followers = total_followers - previous_follower if total_followers - previous_follower > 0 else 0
            total_followers = total_followers
            total_likes = updated_likes(total_likes,previous_entry,previous_likes)
            # print(f"Total likes {total_likes}")
            # print(f"previous likes {previous_likes}")
            # print(f"previous comments {previous_comments}")
            # print(f"Total followers {total_followers}")

            total_comments = updated_comments(total_comments,previous_entry,previous_comments)
            # print(f"Total likes {total_comments}")



        else:
            total_likes = total_likes
            total_comments = total_comments

            previous_entry = SocialStats.objects.last()
            if previous_entry:
                previous_follower = previous_entry.t_followers
                new_followers = total_followers - previous_follower if total_followers - previous_follower > 0 else 0
                total_followers = total_followers
            else:
                new_followers = total_followers
                total_followers = total_followers



        current_entry , created = SocialStats.objects.get_or_create(org=share_page, created_at=current_time)
        current_entry.t_likes = total_likes
        current_entry.t_comments = total_comments
        current_entry.new_followers = new_followers
        current_entry.t_followers = total_followers

        current_entry.save()

    except Exception as e:
        raise e

    # if previous_entry:
    #     stats.t_followers = 0 if previous_entry - result[3] < 0 else previous_entry - result[3]
    # else:
    #     stats.t_followers = result[3]


def updated_likes(total_likes,previous_entry,previous_likes):

    if previous_likes != 0 and total_likes == 0:
        previous_entry.update(t_likes=0)
        previous_likes = 0
        # turn all the previous entries to 0
        return 0
    elif previous_likes > total_likes:

        deleted_count = previous_likes - total_likes
        exact_count = previous_entry.filter(t_likes=deleted_count)
        if exact_count.exists():
            exact_count.update(t_likes=0)
        else:
            entries = previous_entry.values('id').annotate(total_count=Sum('t_likes'))
            exact_count_entries = entries.filter(total_count=deleted_count)
            if exact_count_entries.exists():
                for entry in exact_count_entries:
                    previous_entry.filter(id=entry['id']).update(t_likes=0)
            else:
                candidates = entries.filter(total_count__gt=deleted_count)
                if candidates.exists():
                    i = 0
                    while (deleted_count != 0):
                        candidate = SocialStats.objects.get(id=candidates[i]['id'])
                        t_likes = candidate.t_likes
                        new_t_likes = t_likes - deleted_count if t_likes - deleted_count > 0 else 0
                        deleted_count = deleted_count - t_likes if deleted_count - t_likes > 0 else 0
                        candidate.t_likes = new_t_likes
                        candidate.save()
                        i = i + 1

        return 0

    # It means not all comments are delete but some comments are deleted so
    # we will first find which entry contain the value of new count deleted and subtract from them

    else:
        # it has two possible conditions and we are handling it with same condition
        # if previous likes are less than total new like just subtract and and create new value or update same value
        total_likes = total_likes - previous_likes
        return total_likes

def updated_comments(total_comments,previous_entry,previous_comments):
    if previous_comments != 0 and total_comments == 0:
        previous_entry.update(t_comments=0)
        # turn all the previous entries to 0

        return 0
    elif previous_comments > total_comments:

        deleted_count = previous_comments - total_comments
        exact_count = previous_entry.filter(t_comments=deleted_count)
        if exact_count.exists():
            exact_count.update(t_comments=0)
        else:
            entries = previous_entry.values('id').annotate(total_count=Sum('t_comments'))
            exact_count_entries = entries.filter(total_count=deleted_count)
            if exact_count_entries.exists():
                for entry in exact_count_entries:
                    previous_entry.filter(id=entry['id']).update(t_comments=0)
            else:
                candidates = entries.filter(total_count__gt=deleted_count)
                if candidates.exists():


                    i = 0
                    while (deleted_count != 0):
                        candidate = SocialStats.objects.get(id = candidates[i]['id'])
                        t_comments = candidate.t_comments
                        new_t_comments = t_comments - deleted_count if t_comments - deleted_count > 0 else 0
                        deleted_count = deleted_count - t_comments if deleted_count - t_comments > 0 else 0
                        candidate.t_comments= new_t_comments
                        candidate.save()
                        i = i+1


        return 0

    # It means not all comments are delete but some comments are deleted so
    # we will first find which entry contain the value of new count deleted and subtract from them

    else:
        # it has two possible conditions and we are handling it with same condition
        # if previous likes are less than total new like just subtract and and create new value or update same value
        total_likes = total_comments - previous_comments
        return total_likes
