from django.contrib import admin
from .models import ZippyLinks, LinkModel


@admin.register(ZippyLinks)
class ZippyAdmin(admin.ModelAdmin):
    fields = [
        'image_tag', 'name', 'link', 'link_model', 'created', 'downloaded', 'downloaded_date', 'error',
        'error_message', 'published_date', 'download_link', 'invalid_download_link'
    ]
    readonly_fields = [
        'image_tag', 'created', 'link_model', 'link', 'download_link', 'published_date', 'downloaded_date'
    ]

    list_display = ('id', 'name', 'published_date', 'created', 'downloaded', 'error', 'error_message', 'category')
    search_fields = ('link', 'name')

    def image_tag(self, obj):
        from django.utils.html import format_html

        return format_html(f'<img src="{obj.img_name.url}" />')

    image_tag.short_description = 'img_name'

    # list_display = ['image_tag', ]


@admin.register(LinkModel)
class LinkModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'for_clubbers_url', 'created', 'error', 'error_message']


