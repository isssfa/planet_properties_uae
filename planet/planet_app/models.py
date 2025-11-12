from datetime import datetime

from django.db import models
from embed_video.fields import EmbedVideoField

# Create your models here.
from django.utils.text import slugify
from multiselectfield import MultiSelectField


class Amenities(models.Model):
    name = models.TextField()
    img = models.ImageField(upload_to='amenities/', default="amenities/default.png")


class BufferImages(models.Model):
    buffer_id = models.CharField(max_length=30)
    img = models.ImageField(upload_to='buffer/')


class Cities(models.Model):
    slug = models.SlugField(max_length=300, null=True, blank=True, unique=True)
    name = models.CharField(max_length=150, unique=True)
    img = models.ImageField(upload_to='city/', null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    meta_keywords = models.TextField(null=True, blank=True)
    meta_title = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Cities, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Builder(models.Model):
    slug = models.SlugField(max_length=300, null=True, blank=True, unique=True)
    name = models.CharField(max_length=300, unique=True)
    description = models.TextField(null=True, blank=True)
    disclaimer = models.TextField(null=True, blank=True)
    img = models.FileField(upload_to='builders/', blank=True, null=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Builder, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Blog(models.Model):
    slug = models.SlugField(max_length=300, null=True, blank=True, unique=True)
    title = models.TextField(null=True, blank=True, unique=True)
    description = models.TextField(null=True, blank=True)
    img = models.FileField(upload_to='blogs/', blank=True, null=True)
    meta_description = models.TextField(null=True, blank=True)
    meta_keywords = models.TextField(null=True, blank=True)
    meta_title = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        self.meta_title = self.title
        if not self.id:
            self.created_on = datetime.now()
        super(Blog, self).save(*args, **kwargs)

    def __str__(self):
        return self.title


class ProjectDetails(models.Model):
    BHK_Choices = (
        ("1 BHK", "1 BHK"),
        ("1.5 BHK", "1.5 BHK"),
        ("2 BHK", "2 BHK"),
        ("2.5 BHK", "2.5 BHK"),
        ("3 BHK", "3 BHK"),
        ("3.5 BHK", "3.5 BHK"),
        ("4 BHK", "4 BHK"),
        ("4+ BHK", "4+ BHK")
    )

    Location_Choices = (
        ("North", "North"),
        ("South", "South"),
        ("East", "East"),
        ("West", "West"),
        ("Central", "Central")
    )

    Cost_choices = (
        ("< 40L", "< 40L"),
        ("40L - 70L", "40L - 70L"),
        ("70L - 1Cr", "70L - 1Cr"),
        ("1Cr - 1.5Cr", "1Cr - 1.5Cr"),
        ("1Cr - 2Cr", "1Cr - 2Cr"),
        ("2Cr +", "2Cr +")
    )

    slug = models.SlugField(max_length=300, null=True, blank=True, unique=True)
    city = models.ForeignKey(Cities, on_delete=models.SET_NULL, null=True, blank=True)
    builder = models.ForeignKey(Builder, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.TextField(unique=True)
    description = models.TextField()
    # video_link = EmbedVideoField(null=True, blank=True)
    video_link = models.TextField(null=True, blank=True)
    map_link = models.TextField(null=True, blank=True)
    project_area = models.CharField(max_length=300)
    project_type = models.CharField(max_length=300)
    project_units = models.CharField(max_length=300)
    project_buildup = models.CharField(max_length=300)
    project_price = models.CharField(max_length=300)
    project_currency = models.CharField(max_length=10, choices=[("usd", "USD"),("aed", "AED"),("inr", "INR"),("eur", "EUR")], default="aed")
    project_status = models.CharField(max_length=300)
    project_status_1 = models.CharField(max_length=300, null=True, blank=True)
    contact_email = models.EmailField(null=True, blank=True)
    contact_phone = models.CharField(max_length=100, blank=True, null=True)
    contact_whatsapp = models.CharField(max_length=100, blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    brochure = models.FileField(upload_to='brochures/', blank=True, null=True)
    master_plan = models.FileField(upload_to='master_plan/', blank=True, null=True)
    master_plan_pdf = models.FileField(upload_to='master_plan_pdf/', blank=True, null=True)
    location = models.TextField(null=True, blank=True)

    rera_no = models.CharField(max_length=300, blank=True, null=True)
    dld_permit_number = models.CharField(max_length=300, blank=True, null=True, help_text="DLD Permit Number")
    dld_qr_code = models.ImageField(upload_to='properties/dld_qr/', blank=True, null=True)
    possession = models.TextField(blank=True, null=True)
    property_type = models.CharField(max_length=300, blank=True, null=True)
    property_type_2 = models.CharField(max_length=300, default="New Property")

    bhk = MultiSelectField(choices=BHK_Choices, max_length=30, blank=True, null=True)
    location_direction = models.CharField(max_length=20, choices=Location_Choices, blank=True, null=True)
    cost = MultiSelectField(choices=Cost_choices, max_length=30, blank=True, null=True)
    property_id = models.CharField(max_length=300, blank=True, null=True)
    meta_description = models.TextField(null=True, blank=True)
    meta_keywords = models.TextField(null=True, blank=True)
    meta_title = models.TextField(null=True, blank=True)


    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(ProjectDetails, self).save(*args, **kwargs)

    def __str__(self):
        return self.title


class DailyFxRates(models.Model):
    as_of_date = models.DateField(unique=True)  # e.g., date of rates normalized to AED
    aed_to_usd = models.DecimalField(max_digits=18, decimal_places=8)
    aed_to_eur = models.DecimalField(max_digits=18, decimal_places=8)
    aed_to_inr = models.DecimalField(max_digits=18, decimal_places=8)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-as_of_date"]

    def __str__(self):
        return f"AED rates {self.as_of_date}"



class PropertyAmenities(models.Model):
    project = models.ForeignKey(ProjectDetails, on_delete=models.CASCADE)
    amenity = models.ForeignKey(Amenities, on_delete=models.CASCADE)


class PropertyImages(models.Model):
    project = models.ForeignKey(ProjectDetails, on_delete=models.CASCADE)
    img = models.ImageField(upload_to='properties/')


class PropertyPricing(models.Model):
    project = models.ForeignKey(ProjectDetails, on_delete=models.CASCADE)
    property = models.CharField(max_length=300, null=True, blank=True)
    builtup = models.CharField(max_length=300, null=True, blank=True)
    carpet = models.CharField(max_length=300, null=True, blank=True)
    price = models.CharField(max_length=300, null=True, blank=True)


class PropertyAdvantages(models.Model):
    project = models.ForeignKey(ProjectDetails, on_delete=models.CASCADE)
    title = models.CharField(max_length=300, null=True, blank=True)
    distance = models.CharField(max_length=300, null=True, blank=True)


class PropertyFloors(models.Model):
    project = models.ForeignKey(ProjectDetails, on_delete=models.CASCADE)
    name = models.CharField(max_length=300, null=True, blank=True)
    tag1 = models.CharField(max_length=300, null=True, blank=True)
    tag2 = models.CharField(max_length=300, null=True, blank=True)
    tag3 = models.CharField(max_length=300, null=True, blank=True)
    tag4 = models.CharField(max_length=300, null=True, blank=True)
    img = models.ImageField(upload_to='floors/', null=True, blank=True)
    pdf = models.FileField(upload_to='floors/pdfs/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)


class Association(models.Model):
    img = models.ImageField(upload_to='associates/')


class Testimonials(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    designation = models.CharField(max_length=200, null=True, blank=True)
    testimonial = models.TextField(null=True, blank=True)
    img = models.ImageField(upload_to='testimonials/', null=True, blank=True)


class EventsAndCampaigns(models.Model):
    slug = models.SlugField(max_length=300, null=True, blank=True, unique=True)
    created_on = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    event_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=300, null=True, blank=True)
    img = models.ImageField(upload_to='events/', null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    meta_keywords = models.TextField(null=True, blank=True)
    meta_title = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        if not self.id:
            self.created_on = datetime.now()
        super(EventsAndCampaigns, self).save(*args, **kwargs)


class AwardsAndRecognitions(models.Model):
    title = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    img = models.ImageField(upload_to='events/', null=True, blank=True)


class Pages(models.Model):
    name = models.CharField(max_length=200)
    title = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    keywords = models.TextField(null=True, blank=True)


class WebsiteContent(models.Model):
    call_number = models.CharField(max_length=20, null=True, blank=True)
    active_listing = models.CharField(max_length=20, null=True, blank=True)
    worth_sold = models.CharField(max_length=20, null=True, blank=True)
    happy_customers = models.CharField(max_length=20, null=True, blank=True)
    relationship = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    footer_about = models.TextField(null=True, blank=True)
    featured = models.TextField(null=True, blank=True)
    header_script = models.TextField(null=True, blank=True)
    about_dream = models.TextField(null=True, blank=True)
    about_nri = models.TextField(null=True, blank=True)
    why_rera = models.TextField(null=True, blank=True)
    why_deals = models.TextField(null=True, blank=True)
    why_location = models.TextField(null=True, blank=True)
    why_providing = models.TextField(null=True, blank=True)
    disclaimer = models.TextField(null=True, blank=True)


class ContactForm(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    subject = models.TextField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    ip = models.GenericIPAddressField()
    submitted_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)


class Message(models.Model):
    message = models.TextField(null=True, blank=True)


class BlockedEmail(models.Model):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email


class BlockedIP(models.Model):
    ip = models.GenericIPAddressField(unique=True)

    def __str__(self):
        return self.ip


class BlockedWord(models.Model):
    word = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.word


class BlockedName(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class TeamMembers(models.Model):
    name = models.CharField(max_length=300, unique=True)
    description = models.TextField(null=True, blank=True)
    img = models.FileField(upload_to='team/', blank=True, null=True)


    def __str__(self):
        return self.name


class Brokers(models.Model):
    name = models.CharField(max_length=300)
    picture = models.ImageField(upload_to='brokers/', blank=True, null=True)
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True)
    brn = models.CharField(max_length=100, blank=True, null=True, help_text="Broker Registration Number")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Videos(models.Model):
    title = models.CharField(max_length=200)
    thumbnail = models.ImageField(upload_to='videos/thumbnails')
    video = models.FileField(upload_to='videos', help_text="Upload video file")
    created_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_on']
        verbose_name = 'Video'
        verbose_name_plural = 'Videos'

    def __str__(self):
        return self.title
