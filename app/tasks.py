import functools
import time

from asgiref.sync import sync_to_async
from celery.exceptions import Ignore
from django.core.cache import cache

from Automatation.celery import app
from allauth.socialaccount.models import SocialAccount
from .models import PostModel, SharePage,CeleryTask,Post_urn,User
from .signals import schedule_signals_task, gather_post_insight
from django.db.models import Q




@app.task
def task_one():
    # " task one called and worker is running good")
    post = PostModel.objects.filter(Q(status='PROCESSING') | Q(status='SCHEDULED'))
    for _ in post:
        schedule_signals_task(_)

    return "success"




@app.task
def task_two():
    # Getting all the social account user with provider facebook and linkedin
    # getting share_pages of the users whose pages are connected
    users_with_social_accounts = SocialAccount.objects.filter(
        Q(provider="facebook") | Q(provider='linkedin_oauth2')).values_list('user', flat=True).distinct()
    key = f"GATHERING INSIGHTS (TASK 2)"


    task = CeleryTask.objects.filter(key=key,task_name = "GATHERING POST INSIGHTS").last()
    created = False
    if (task is None) or task.status != "PROCESSING":
        # Task does not exist, create a new task.
        task = CeleryTask.objects.create(key=key,task_name = f"GATHERING POST INSIGHTS")
        created = True
    else:
        if task.status == "PROCESSING":
            created = False
    try:
        if (not created and task.status != "PROCESSING") or created:
            share_pages = SharePage.objects.filter(user__in=users_with_social_accounts)
            for pages in share_pages:
                gather_post_insight(pages)

            task.status = "FINISHED"
            task.result = f"SUCCESSFULLY GATHERED "
            task.save()

    except Exception as e:
        print(e)
        task.status = "FAILED"
        task.result = f"FAILED GATHERING {e}"
        task.save()




    return "success"




@app.task
def task_three(users,task):
    task = CeleryTask.objects.get(id=task)
    try:
        share_pages = SharePage.objects.filter(user__id__in=users)
        for page in share_pages:
            gather_post_insight(page)

        task.status = "FINISHED"
        task.result = "REQUEST SUCCESSFUL"
        task.save()



    except Exception as e:
        task.status = "FAILED"
        task.result = f"REQUEST SUCCESSFUL {e}"
        task.save()








# async def get_sharepage_data(user):
#     async for entry in SharePage.objects.all():
#         try:
#             # print(entry.org_id)
#             pass
#         except Exception as e:
#             print(e)
#


# @sync_to_async
# def get_post_urns(page):
#     return list(Post_urn.objects.filter(org=page, is_deleted=False).values_list('urn', flat=True))
# @app.task()
# def task_four(user,since,until):
#     async def facebook(user,share_page,post_urn,since, until):
#
#         tasks = []
#         for page in share_page:
#             id = page[0]
#             access_token = page[1]
#             post_urn_list = post_urn.get(id)
#
#             tasks.append(fb_post_insights(post_urn_list,access_token ,id, since, until))
#
#         task = await asyncio.gather(*tasks)
#
#     start = time.perf_counter()
#     share_pages = SharePage.objects.filter(provider = "facebook")
#     share_pages_tuple = tuple(SharePage.objects.filter(provider = "facebook").values_list("org_id","access_token"))
#
#     post_urn_dict = {}
#     for pages in share_pages:
#         post_urn = tuple(Post_urn.objects.filter(org=pages, is_deleted=False).values_list('urn', flat=True))
#         post_urn_dict[pages.org_id] = post_urn
#
#
#
#
#     asyncio.run(facebook(user,share_pages_tuple,post_urn_dict,since,until))
#
#     end = time.perf_counter()
#
#     print(end - start)
#
#
#
#







