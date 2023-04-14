from tortoise import fields, ForeignKeyFieldInstance
from tortoise import Model


class BaseModel(Model):
    async def to_dict(self):
        res = {}
        for field_name, field in self._meta.fields_map.items():
            if isinstance(field, ForeignKeyFieldInstance):
                related_instance_id = getattr(self, f"{field_name}_id")
                related_instance = await field.related_model.get(id=related_instance_id)
                related_dict = await related_instance.to_dict()
                res[field_name] = related_dict
            else:
                res[field_name] = getattr(self, field_name)
        return res


class LinkModel(BaseModel):
    name = fields.CharField(max_length=100, null=True, description="Song name")
    for_clubbers_url = fields.CharField(
        max_length=2000, null=True, unique=True, description="Forum url"
    )
    error = fields.BooleanField(
        default=False, description="If error occurs, set to True"
    )
    error_message = fields.CharField(
        max_length=2000, null=True, description="If error occurs, save message"
    )

    created = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "4clubbers_links"
        abstract = False

    def __str__(self):
        return f"{self.for_clubbers_url}"


class DownloadLinks(BaseModel):
    name = fields.CharField(
        max_length=1000, null=True, blank=True, description="Song name"
    )
    link = fields.CharField(
        max_length=2000,
        null=True,
        unique=True,
        description="Link to page where file is hosted",
    )
    link_model = fields.ForeignKeyField(
        "models.LinkModel",
        on_delete=fields.SET_NULL,
        null=True,
        description="Foreignkey to forum model",
    )
    download_link = fields.CharField(
        max_length=2000, null=True, blank=True, description="Direct download link"
    )
    downloaded = fields.BooleanField(
        default=False, description="State saying if file is download or not"
    )
    downloaded_date = fields.DateField(
        null=True, blank=True, description="Downloaded date"
    )
    error = fields.BooleanField(
        default=False, description="If error occurs set flag to True"
    )
    error_message = fields.CharField(
        max_length=2000,
        null=True,
        blank=True,
        description="If error occurs write error message",
    )
    not_exists = fields.BooleanField(
        default="False", description="if file not exists on server, set to True"
    )
    published_date = fields.DateField(
        max_length=100, null=True, blank=True, description="Published on server date"
    )
    category = fields.CharField(
        max_length=20, null=True, blank=True, description="Category: trance or house"
    )
    invalid_download_link = fields.BooleanField(
        default=False, description="If link is not valid, set to True"
    )

    created = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return f"Parsed name: {self.name}"

    class Meta:
        table = "download_links"
        abstract = False
