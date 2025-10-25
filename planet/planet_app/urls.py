from django.urls import path
from .views_currency import set_currency
from .views import *


urlpatterns = [
    path('', Index, name='index'),
    path('cities/<str:slug>', properties_city, name='properties_city'),
    path('properties/', properties, name='properties'),
    path('properties/<str:pro_name>', single_property, name='single_property'),
    path('contact-us', contact_us, name='contact_us'),
    path('about-us', about_us, name='about_us'),
    path('why-planets-properties', why_planets_properties, name='why_planets_properties'),
    path('our-team', our_team, name='our_team'),
    path('awards-and-recognitions', awards_and_recognitions, name='awards_and_recognitions'),
    path('events', events_all, name='events_all'),
    path('events/<str:slug>', events_single, name='events_single'),
    path('disclaimer', disclaimer, name='disclaimer'),
    path("set-currency/", set_currency, name="set_currency"),


    path('search', search_property),

    path('get-project-images', get_project_images),

    path('login', login_function),
    path('accounts/login/', accounts_login),
    path('logout', logout_fun),
    path('change-password', change_password),

    path('dashboard', IndexCheck),

    path('add-property', add_property),
    path('view-properties', view_properties),
    path('edit-property', edit_property),
    path('delete-property', delete_property),
    path('check-property-exist', check_property_exist),
    path('edit-property/<int:pk>', edit_property_details),

    path('upload-buffer-image', upload_buffer_image),
    path('remove-buffer-image', remove_buffer_image),
    path('remove-previous-image', remove_previous_image),

    path('add-amenities', add_amenities),
    path('edit-amenities', edit_amenities),
    path('delete-amenities', delete_amenities),

    path('add-awards', add_awards),
    path('edit-awards', edit_awards),
    path('delete-awards', delete_awards),

    path('add-builder', add_builder),
    path('edit-builder', edit_builder),
    path('delete-builder', delete_builder),

    path('add-events', add_events),
    path('edit-events', edit_events),
    path('delete-events', delete_events),

    path('add-testimonial', add_testimonial),
    path('edit-testimonial', edit_testimonial),
    path('delete-testimonial', delete_testimonial),

    path('settings', settings_page),

    path('website-content', website_content),
    path('about-content', about_content),
    path('message', add_edit_messages),

    path('meta', meta_details),

    path('association', add_associate),
    path('delete-associate', delete_associate),

    path('send-email', send_email),
    path('show-form-submissions', show_form_submissions),
    path('block-email', block_email),
    path('block-ip', block_ip),
    path('block-words', block_words),
    path('block-name', block_name),

    path('sitemap.xml', sitemap_xml, name='sitemap'),
    path('sitemap/', html_sitemap, name='html_sitemap'),

    path('blogs/', blog_list, name='blog_list'),
    path('blogs/<str:slug>/', blog_detail, name='blog_detail'),
    path('blogs-manage', blog_manage, name='blog_manage'),
    path('blog-delete/<str:id>', blog_delete, name='blog_delete'),

    path('manage-team/', manage_team, name='manage_team'),
    path('delete-team/', delete_team_member, name='delete_team'),

    path('manage-cities/', manage_cities, name='manage_cities'),

]