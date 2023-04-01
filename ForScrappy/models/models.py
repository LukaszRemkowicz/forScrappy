from tortoise import fields
from tortoise import Model


class LinkModel(Model):
    name = fields.CharField(max_length=100, null=True)
    for_clubbers_url = fields.CharField(max_length=2000, null=True, unique=True)
    created = fields.DatetimeField(auto_now_add=True)
    error = fields.BooleanField(default=False)
    error_message = fields.CharField(max_length=2000, null=True)

    class Meta:
        table = "4clubbers_links"
        abstract = False

    def __str__(self):
        return f'{self.for_clubbers_url}'


class DownloadLinks(Model):

    name = fields.CharField(max_length=1000, null=True, blank=True)
    link = fields.CharField(max_length=2000, null=True, unique=True)
    link_model = fields.ForeignKeyField('models.LinkModel', on_delete=fields.SET_NULL, null=True)
    created = fields.DatetimeField(auto_now_add=True)
    download_link = fields.CharField(max_length=2000, null=True, blank=True)
    downloaded = fields.BooleanField(default=False)
    downloaded_date = fields.DateField(null=True, blank=True)
    error = fields.BooleanField(default=False)
    error_message = fields.CharField(max_length=2000, null=True, blank=True)
    not_exists = fields.BooleanField(default='False')
    published_date = fields.DateField(max_length=100, null=True, blank=True)
    category = fields.CharField(max_length=20, null=True, blank=True)
    invalid_download_link = fields.BooleanField(default=False)

    def __str__(self):
        return f'Parsed name: {self.name}'
