
from Automatation.celery import app
from .models import PostModel
from .signals import schedule_signals_task
from django.db.models import Q

@app.task
def task_one():
    print(" task one called and worker is running good")
    post = PostModel.objects.filter(Q(status='PROCESSING')|Q(status='SCHEDULED'))
    for _ in post:
        schedule_signals_task(_)

    return "success"

# @app.task
# def task_two(data, args, *kwargs):
#     print(f" task two called with the argument {data} and worker is running good")
#     return "success"