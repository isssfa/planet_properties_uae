from django.contrib import admin
from .models import *
from embed_video.admin import AdminVideoMixin
from import_export.admin import ImportExportModelAdmin


class AmenitiesSearch(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['id', 'name', 'img']


class ContactFormSearch(admin.ModelAdmin):
    search_fields = ['name', 'phone', 'email', 'ip']
    list_display = ['name', 'phone', 'email', 'ip', 'submitted_on']


class ProjectSearch(AdminVideoMixin, admin.ModelAdmin):
    search_fields = ['id', 'title']
    list_display = ['title', 'project_area', 'project_type', 'project_units', 'project_price', 'id']


class PropertyImagesSearch(AdminVideoMixin, admin.ModelAdmin):
    search_fields = ['id']
    list_display = ['id', 'img', 'project']

@admin.register(Pages)
class PagesSearch(ImportExportModelAdmin):
    # resource_classes = [Pages]
    search_fields = ['id', 'name']
    list_display = ['id', 'name', 'title', 'description', 'keywords']

@admin.register(TeamMembers)
class PagesSearch(ImportExportModelAdmin):
    # resource_classes = [Pages]
    search_fields = ['id', 'name']
    list_display = ['id', 'name', 'img']

class VideosSearch(admin.ModelAdmin):
    search_fields = ['id', 'title']
    list_display = ['id', 'title', 'thumbnail', 'created_on', 'is_active']
    list_filter = ['is_active', 'created_on']


class BlogSearch(admin.ModelAdmin):
    search_fields = ['id', 'name']
    list_display = ['id', 'title', 'created_on', 'updated_on']


admin.site.register(Amenities, AmenitiesSearch)
admin.site.register(ProjectDetails, ProjectSearch)
admin.site.register(PropertyFloors)
admin.site.register(Message)
admin.site.register(PropertyImages, PropertyImagesSearch)
admin.site.register(PropertyAmenities)
admin.site.register(PropertyAdvantages)
admin.site.register(PropertyPricing)
admin.site.register(Cities)
admin.site.register(Builder)
admin.site.register(BufferImages)
admin.site.register(WebsiteContent)
admin.site.register(EventsAndCampaigns)
admin.site.register(BlockedIP)
admin.site.register(BlockedEmail)
admin.site.register(BlockedName)
admin.site.register(DailyFxRates)
admin.site.register(BlockedWord)
admin.site.register(ContactForm, ContactFormSearch)
# admin.site.register(Pages, PagesSearch)
admin.site.register(Blog, BlogSearch)
admin.site.register(Videos, VideosSearch)
