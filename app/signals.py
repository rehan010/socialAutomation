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

from django.db.models.signals import m2m_changed, pre_delete




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


@shared_task
def gather_post_insight(instance):

    try:
        # key = f"{instance.id} {instance.user.id}"
        since = datetime.now(timezone.utc).replace(minute=0,hour=0,second=0,microsecond=0)
        until = datetime.now(timezone.utc)
        post_urns = Post_urn.objects.filter(org=instance, is_deleted=False).values_list('urn', flat=True)

        if instance.provider == "facebook":

            fb_post_insights(post_urns, instance, since, until)
        elif instance.provider == "instagram":

            since = datetime.now(timezone.utc) - timedelta(days=1)
            until = datetime.now(timezone.utc)

            instagram_account_insights(instance, since, until)
        elif instance.provider == "linkedin":
            linkedin_share_stats(instance, since, until)
        else:
            pass


    except Exception as e:
        pass





