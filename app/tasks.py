import time

from celery.exceptions import Ignore
from django.core.cache import cache

from Automatation.celery import app
from allauth.socialaccount.models import SocialAccount
from .models import PostModel, SharePage,CeleryTask
from .signals import schedule_signals_task, gather_post_insight
from django.db.models import Q





@app.task
def task_one():
    # " task one called and worker is running good")
    post = PostModel.objects.filter(Q(status='PROCESSING') | Q(status='SCHEDULED'))
    for _ in post:
        schedule_signals_task(_)

    return "success"


# @app.task
# def task_two(data, args, *kwargs):
#     f" task two called with the argument {data} and worker is running good")
#     return "success"


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
        task.status = "FAILED"
        task.result = f"FAILED GATHERING {e}"
        task.save()

    return "success"


# @app.task
# def task_two():
#     # Getting all the social account user with provider facebook and linkedin
#     # getting share_pages of the users whose pages are connected
#     try:
#
#         users_with_social_accounts = SocialAccount.objects.filter(
#             Q(provider="facebook") | Q(provider='linkedin_oauth2')).values_list('user', flat=True).distinct()
#         share_pages = SharePage.objects.filter(user__in=users_with_social_accounts)
#         for pages in share_pages:
#             gather_post_insight(pages)
#     except Exception as e:
#         return e
#
#     return "success


# @app.task
# def task_three(users,lock_key):
#     cache.get(lock_key)
#     if not cache.get(lock_key):
#         try:
#             cache.set(lock_key, "1", None)
#             share_pages = SharePage.objects.filter(user__id__in=users)
#             for pages in share_pages:
#                 gather_post_insight(pages)
#             cache.delete(lock_key)
#         except Exception as e:
#             return e
#         finally:
#             cache.delete(lock_key)
#             cache.get(lock_key)
#     else:
#         raise Ignore()

@app.task
def task_three(users,task):
    task = CeleryTask.objects.get(id=task)
    try:
        share_pages = SharePage.objects.filter(user__id__in=users)
        for pages in share_pages:
            gather_post_insight(pages)

        task.status = "FINISHED"
        task.result = "REQUEST SUCCESSFUL"
        task.save()

    except Exception as e:
        task.status = "FAILED"
        task.result = f"REQUEST SUCCESSFUL {e}"
        task.save()





