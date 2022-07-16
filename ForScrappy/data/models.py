from django.db import models
from django.utils.safestring import mark_safe


class LinkModel(models.Model):
    name = models.CharField(max_length=100, null=True)
    for_clubbers_url = models.CharField(max_length=2000, null=True, unique=True)
    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    error = models.BooleanField(default=False)
    error_message = models.CharField(max_length=2000, null=True)

    def __str__(self):
        return f'{self.for_clubbers_url}'


class ZippyLinks(models.Model):

    name = models.CharField(max_length=1000, null=True, blank=True)
    img_name = models.ImageField(upload_to='media/img_names/', null=True, blank=True)
    link = models.CharField(max_length=2000, null=True, unique=True)
    link_model = models.ForeignKey(LinkModel, on_delete=models.SET_NULL, null=True)
    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    download_link = models.CharField(max_length=2000, null=True, blank=True)
    downloaded = models.BooleanField(default=False)
    downloaded_date = models.DateField(null=True, blank=True)
    error = models.BooleanField(default=False)
    error_message = models.CharField(max_length=2000, null=True, blank=True)
    not_exists = models.BooleanField(default='False')
    published_date = models.DateField(max_length=100, null=True, blank=True)
    category = models.CharField(max_length=20, null=True, blank=True)
    invalid_download_link = models.BooleanField(default=False)

    def __str__(self):
        return f'Parser zippy: {self.name}'
