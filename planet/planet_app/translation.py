# planet_app/translation.py

from modeltranslation.translator import translator, TranslationOptions
from .models import (
    Amenities, Cities, Builder, Blog, ProjectDetails,
    PropertyPricing, PropertyAdvantages, PropertyFloors,
    Testimonials, EventsAndCampaigns, AwardsAndRecognitions,
    Pages, WebsiteContent, TeamMembers
)


# --- 1. Static Text / Choices Translation ---
# Fields defined as choices on models need special handling.
# However, for most of your choices (like BHK_Choices, Location_Choices, Cost_choices),
# the values are technical (e.g., "1 BHK", "< 40L").
# The translatable text for these should be handled with static i18n (.po files)
# where you translate "1 BHK" or "North" within the template itself.
# We will focus on the models that hold dynamic content.


# --- 2. Dynamic Content Translation ---

class AmenitiesTranslationOptions(TranslationOptions):
    fields = ('name',) # e.g., 'Swimming Pool', 'Gym'

class CitiesTranslationOptions(TranslationOptions):
    fields = ('name', 'meta_description', 'meta_keywords', 'meta_title')
    # Note: Slug is auto-generated from 'name' and typically does not need translation.

class BuilderTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'disclaimer')

class BlogTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'meta_description', 'meta_keywords', 'meta_title')
    # Note: Slug is auto-generated from 'title'.

class ProjectDetailsTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'description',
        'project_area',     # If it's descriptive text (e.g., "30 Acres of Land")
        'project_type',     # e.g., "Residential Apartments"
        'project_units',    # e.g., "500 Total Units"
        'project_buildup',  # e.g., "2000 sq ft"
        'project_price',    # If it's descriptive text (e.g., "Starting from...")
        'project_status',   # e.g., "Ready to Move"
        'project_status_1', # e.g., "Under Construction"
        'location',         # Detailed text description of the location
        'possession',       # e.g., "Q4 2025" or "Immediate"
        'property_type',    # e.g., "Flat" or "Villa"
        'property_type_2',  # e.g., "New Property"
        'meta_description',
        'meta_keywords',
        'meta_title',
    )


class PropertyPricingTranslationOptions(TranslationOptions):
    fields = ('property', 'builtup', 'carpet', 'price')
    # These often contain units (e.g., "3 BHK Type A", "1200 sq.ft.").
    # Translate the descriptive part where possible.

class PropertyAdvantagesTranslationOptions(TranslationOptions):
    fields = ('title', 'distance') # e.g., 'Near Airport', '10 KM from Downtown'

class PropertyFloorsTranslationOptions(TranslationOptions):
    fields = ('name', 'tag1', 'tag2', 'tag3', 'tag4', 'description')
    # e.g., 'Penthouse Floor', 'Exclusive Amenities', 'Top View'

class TestimonialsTranslationOptions(TranslationOptions):
    fields = ('name', 'designation', 'testimonial')

class EventsAndCampaignsTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'description',
        'location',
        'meta_description',
        'meta_keywords',
        'meta_title',
    )
    # Note: Slug is auto-generated from 'title'.

class AwardsAndRecognitionsTranslationOptions(TranslationOptions):
    fields = ('title', 'description')

class PagesTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'keywords')

class WebsiteContentTranslationOptions(TranslationOptions):
    fields = (
        'address',
        'footer_about',
        'featured', # If this holds text content
        'about_dream',
        'about_nri',
        'why_rera',
        'why_deals',
        'why_location',
        'why_providing',
        'disclaimer',
    )
    # Fields like 'call_number', 'active_listing', etc. are usually numerical/identifiers
    # and shouldn't be translated, but their surrounding text (labels) should be translated
    # using static i18n (.po files).

class TeamMembersTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


# --- Registering the Models ---

translator.register(Amenities, AmenitiesTranslationOptions)
translator.register(Cities, CitiesTranslationOptions)
translator.register(Builder, BuilderTranslationOptions)
translator.register(Blog, BlogTranslationOptions)
translator.register(ProjectDetails, ProjectDetailsTranslationOptions)
translator.register(PropertyPricing, PropertyPricingTranslationOptions)
translator.register(PropertyAdvantages, PropertyAdvantagesTranslationOptions)
translator.register(PropertyFloors, PropertyFloorsTranslationOptions)
translator.register(Testimonials, TestimonialsTranslationOptions)
translator.register(EventsAndCampaigns, EventsAndCampaignsTranslationOptions)
translator.register(AwardsAndRecognitions, AwardsAndRecognitionsTranslationOptions)
translator.register(Pages, PagesTranslationOptions)
translator.register(WebsiteContent, WebsiteContentTranslationOptions)
translator.register(TeamMembers, TeamMembersTranslationOptions)