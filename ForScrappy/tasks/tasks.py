from celery import shared_task


@shared_task
def download_file(download_link, obj_id, file_name):
    ...
