import os
import shutil
import string

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import EmailMessage
from django.db import IntegrityError
from django.db.models import Count
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.utils.translation import gettext as _
from honeypot.decorators import check_honeypot

from .utils import *

base_dir = settings.MEDIA_ROOT
LANG_COOKIE = getattr(settings, "LANGUAGE_COOKIE_NAME", "django_language")


def get_cities():
    """Cache cities query"""
    return Cities.objects.all().select_related()


def get_whatsapp_message():
    """Get or create default whatsapp message"""
    message, created = Message.objects.get_or_create(
        defaults={'message': _("Test")}
    )
    return message.message


def get_meta_data(page):
    """Get or create page metadata"""
    meta_data, created = Pages.objects.get_or_create(
        name=page,
        defaults={'title': page, 'description': '', 'keywords': ''}
    )
    return meta_data


def get_website_content():
    """Cache website content - called frequently"""
    return WebsiteContent.objects.select_related().first()


def get_search_filters():
    """Get all search filters in one query set"""
    projects = ProjectDetails.objects.all()
    return {
        'search_city': projects.values('city__name').distinct(),
        'search_type': projects.values('property_type').distinct(),
        'search_status': projects.values('project_status').distinct(),
        'search_builder': projects.values('builder__name').distinct(),
        'looking_for': projects.values('property_type_2').distinct(),
    }


def prepare_project_list(projects, request):
    """Prepare project list with images and pricing - optimized with prefetch"""
    project_list = []
    # Prefetch related images to avoid N+1 queries
    projects = projects.prefetch_related('propertyimages_set')

    for p in projects:
        img = p.propertyimages_set.all()
        price_info = display_price_for_project(p, request)
        project_list.append({
            'project': p,
            'img': img,
            'price_display': price_info['price_display'],
            'currency_code': price_info['code'],
        })
    return project_list


def get_common_context(request):
    """Get common context data used across multiple views"""
    return {
        'city': get_cities(),
        'website': get_website_content(),
        'num1': get_random(),
        'num2': get_random(),
        'chosen_currency': request.session.get("currency", BASE),
    }


def Index(request):
    chosen = request.session.get("currency", BASE)

    # Optimize with select_related and prefetch_related
    featured_proper = ProjectDetails.objects.filter(
        is_featured=True
    ).select_related('city', 'builder').prefetch_related('propertyimages_set')

    featured = prepare_project_list(featured_proper, request)

    # Optimize city count query with annotation
    cities_with_count = Cities.objects.annotate(
        project_count=Count('projectdetails')
    ).all()
    cities = [{'city': i, 'count': i.project_count} for i in cities_with_count]
    videos = Videos.objects.all()[:10]
    # Get search filters
    search_filters = get_search_filters()

    # Get other data
    associates = Association.objects.all()
    testimonials = Testimonials.objects.all()
    events = EventsAndCampaigns.objects.all()
    brokers = Brokers.objects.filter(is_active=True)
    message = get_whatsapp_message()
    meta_data = get_meta_data(_("Home"))

    data = {
        'current': 'home',
        'title': _(meta_data.title),
        'featured': featured,
        'cities': cities,
        'associates': associates,
        'testimonials': testimonials,
        'events': events,
        'brokers': brokers,
        'message': message,
        'page_description': _(meta_data.description),
        'page_keywords': _(meta_data.keywords),
        'videos': videos,
        **get_common_context(request),
        **search_filters,
    }
    return render(request, 'index.html', data)


def contact_us(request):
    meta_data = get_meta_data(_("Contact Us"))
    data = {
        'current': 'contact',
        'title': meta_data.title,
        'page_description': meta_data.description,
        'page_keywords': meta_data.keywords,
        **get_common_context(request),
    }
    return render(request, 'contact.html', data)


def about_us(request):
    meta_data = get_meta_data(_("About Us"))
    data = {
        'current': 'about',
        'title': meta_data.title,
        'slug': 'about-us',
        'page_description': meta_data.description,
        'page_keywords': meta_data.keywords,
        **get_common_context(request),
    }
    return render(request, 'about.html', data)


def why_planets_properties(request):
    meta_data = get_meta_data(_("Why Us"))
    data = {
        'current': 'about',
        'title': meta_data.title,
        'slug': 'why-planets-properties',
        'page_description': meta_data.description,
        'page_keywords': meta_data.keywords,
        **get_common_context(request),
    }
    return render(request, 'why.html', data)


def our_team(request):
    team = TeamMembers.objects.all()
    meta_data = get_meta_data(_("Our Team"))
    data = {
        'current': 'about',
        'title': meta_data.title,
        'slug': 'our-team',
        'team': team,
        'page_description': meta_data.description,
        'page_keywords': meta_data.keywords,
        **get_common_context(request),
    }
    return render(request, 'team.html', data)


def awards_and_recognitions(request):
    awards = AwardsAndRecognitions.objects.all()
    meta_data = get_meta_data(_("Awards & Recognitions"))
    data = {
        'current': 'about',
        'title': meta_data.title,
        'slug': 'awards',
        'awards': awards,
        'page_description': meta_data.description,
        'page_keywords': meta_data.keywords,
        **get_common_context(request),
    }
    return render(request, 'awards.html', data)


def events_all(request):
    events = EventsAndCampaigns.objects.all()
    meta_data = get_meta_data(_("Events & Campaigns"))
    data = {
        'current': 'about',
        'title': meta_data.title,
        'slug': 'events',
        'events': events,
        'page_description': meta_data.description,
        'page_keywords': meta_data.keywords,
        **get_common_context(request),
    }
    return render(request, 'events.html', data)


def disclaimer(request):
    data = {
        'current': 'about',
        'title': _("Disclaimer & Privacy Policy"),
        **get_common_context(request),
    }
    return render(request, 'disclaimer.html', data)


def events_single(request, slug):
    chosen = request.session.get("currency", BASE)
    events = get_object_or_404(EventsAndCampaigns, slug=slug)

    # Optimize featured properties query
    featured_proper = ProjectDetails.objects.filter(
        is_featured=True
    ).select_related('city', 'builder').prefetch_related('propertyimages_set')[:5]

    featured = prepare_project_list(featured_proper, request)

    data = {
        'current': 'about',
        'title': events.meta_title if events.meta_title else events.title,
        'slug': 'events',
        'events': events,
        'featured': featured,
        'page_description': events.meta_description,
        'page_keywords': events.meta_keywords,
        **get_common_context(request),
    }
    return render(request, 'events_single.html', data)


def properties(request):
    # Optimize with select_related and prefetch_related
    all_proper = ProjectDetails.objects.select_related(
        'city', 'builder'
    ).prefetch_related('propertyimages_set').order_by('-id')

    projects = prepare_project_list(all_proper, request)
    search_filters = get_search_filters()
    message = get_whatsapp_message()
    meta_data = get_meta_data(_("Properties"))

    data = {
        'current': 'properties',
        'title': meta_data.title,
        'projects': projects,
        'message': message,
        'page_description': meta_data.description,
        'page_keywords': meta_data.keywords,
        **get_common_context(request),
        **search_filters,
    }
    return render(request, 'listing.html', data)


def properties_city(request, slug):
    city = get_object_or_404(Cities, slug=slug)

    # Optimize query
    all_proper = ProjectDetails.objects.filter(
        city__slug=slug
    ).select_related('city', 'builder').prefetch_related('propertyimages_set')

    projects = prepare_project_list(all_proper, request)
    search_filters = get_search_filters()
    message = get_whatsapp_message()

    data = {
        'current': 'cities',
        'title': city.meta_title if city.meta_title else city.name,
        'city_title': city.name,
        'projects': projects,
        'slug': slug,
        'message': message,
        'page_description': city.meta_description,
        'page_keywords': city.meta_keywords,
        **get_common_context(request),
        **search_filters,
    }
    return render(request, 'listing.html', data)


def single_property(request, pro_name):
    chosen = request.session.get("currency", BASE)

    # Optimize with select_related and prefetch_related
    project = get_object_or_404(
        ProjectDetails.objects.select_related('city', 'builder'),
        slug=pro_name
    )

    # Fetch all related data efficiently
    images = PropertyImages.objects.filter(project=project)
    pricing = PropertyPricing.objects.filter(project=project)
    location = PropertyAdvantages.objects.filter(project=project)
    amenities = PropertyAmenities.objects.filter(project=project).select_related('amenity')
    floors = PropertyFloors.objects.filter(project=project)

    # Optimize featured properties
    featured_proper = ProjectDetails.objects.filter(
        is_featured=True
    ).select_related('city', 'builder').prefetch_related('propertyimages_set')[:5]

    featured = prepare_project_list(featured_proper, request)

    message = get_whatsapp_message()
    if project.builder:
        message = message.replace("[[property]]", project.title).replace(
            "[[builder]]", project.builder.name
        ).replace(" ", "%20").replace(",", "%2C").replace(".", "%2E")

    # Convert the main project price
    price_info = display_price_for_project(project, request)

    # Convert pricing
    pricing_converted = []
    for pr in pricing:
        try:
            price_aed = Decimal(str(pr.price))
            from .currency import convert_amount, format_money
            cv = convert_amount(price_aed, request)
            pr_display = format_money(cv, request)
        except Exception:
            pr_display = None
        pricing_converted.append({
            "obj": pr,
            "price_display": pr_display,
            "currency_code": chosen,
        })

    data = {
        'current': 'properties',
        'title': project.meta_title if project.meta_title else pro_name,
        'project': project,
        'images': images,
        'pricing': pricing_converted,
        'location': location,
        'amenities': amenities,
        'floors': floors,
        'featured': featured,
        'message': message,
        'page_description': project.meta_description,
        'page_keywords': project.meta_keywords,
        'project_price_display': price_info['price_display'],
        **get_common_context(request),
    }
    return render(request, 'single.html', data)


def search_property(request):
    # Build filters dynamically
    _filters = {}
    filter_params = {
        'city': 'city__name',
        'type': 'property_type',
        'type_2': 'property_type_2',
        'status': 'project_status',
        'builder': 'builder__name',
        'bhk': 'bhk',
        'budget': 'cost',
        'location': 'location_direction',
    }

    for param, field in filter_params.items():
        value = request.GET.get(param)
        if value and value != 'any':
            _filters[field] = value

    # Optimize query
    all_proper = ProjectDetails.objects.filter(
        **_filters
    ).select_related('city', 'builder').prefetch_related('propertyimages_set').order_by('-id')

    projects = prepare_project_list(all_proper, request)
    search_filters = get_search_filters()
    message = get_whatsapp_message()

    data = {
        'current': 'properties',
        'title': _('Search Properties'),
        'projects': projects,
        'message': message,
        **get_common_context(request),
        **search_filters,
    }
    return render(request, 'listing.html', data)


@check_honeypot(field_name='check_field')
def send_email(request):
    url = 'https://connect.leadrat.com/api/v1/integration/Website'
    api_key = "NDdmMjA4NGItNWQzZi00ZmJhLTk5MGUtZTY1ZTQwNDc0OGU4"
    headers = {
        "API-Key": api_key,
        "Content-Type": "application/json"
    }

    name = request.POST['name']
    email = request.POST['email']
    phone = request.POST['phone']
    message = request.POST['message']
    num1 = int(request.POST['num1'])
    num2 = int(request.POST['num2'])
    answer = int(request.POST['answer_quiz'])
    property_id = request.POST.get('property_id')
    subject = request.POST.get('subject')
    ip = get_ip(request)
    ContactForm.objects.create(
        name=name, email=email, phone=phone, message=message, subject=subject, ip=ip
    )
    email_check = check_email(email)
    ip_check = check_ip(ip)
    name_check = check_name(name)
    word_check = [check_word(word) for word in message.split(' ')]
    submitted_date = datetime.now().strftime('%Y-%m-%d')
    submitted_time = datetime.now().strftime('%H:%M:%S')
    project = None
    if property_id:
        project = get_object_or_404(ProjectDetails, id=property_id)

    if ip_check and email_check and name_check and False not in word_check:
        if num1 + num2 == answer:
            try:
                if subject:
                    subject = str(subject)
                else:
                    subject = "New Response from Website by " + str(name)
                # API call payload (based on available fields)
                payload_dict = {
                    "name": name,
                    "email": email,
                    "mobile": phone,
                    "notes": message,
                    "source": "Website",
                    "submittedDate": submitted_date,
                    "submittedTime": submitted_time,
                }

                if project:
                    payload_dict.update({
                        "leadStatus": f"Lead for {project.title}",
                        "propertyType": f"{project.property_type}, ({project.property_type_2})",
                        "project": project.title,
                        "property": project.title,
                    })

                payload = [payload_dict]

                # Make the API call
                response = requests.post(url, headers=headers, json=payload)

                email_template = "<table border='1'><tr><th>Name</th><td>" + str(
                    name) + "</td></tr><tr><th>Email</th><td>" + str(
                    email) + "</td></tr><tr><th>Mobile No.</th><td>" + str(
                    phone) + "</td></tr><tr><th>Message</th><td>" + str(message) + "</td></tr></table>"
                to = ['sales@planetsproperties.com']
                email_msg = EmailMessage(subject,
                                         email_template, 'info@planetsproperties.com',
                                         to,
                                         reply_to=[email])
                email_msg.content_subtype = 'html'
                email_msg.send(fail_silently=False)

                if response.status_code == 200:
                    messages.success(request, 'Message sent successfully and lead shared!')
                else:
                    messages.error(request, f"Failed to share lead: {response.text}")
            except Exception as e:
                messages.error(request,
                               f"Error occurred: {str(e)}. Please Report/Contact sales@planetsproperties.com for more details.'")
        else:
            messages.error(request, 'Wrong Answer!')
    else:
        messages.error(request, 'Validation failed. Please check your input.')

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def show_form_submissions(request):
    forms = ContactForm.objects.all().order_by('-id')[:150]
    data = {'forms': forms}
    return render(request, 'check_submissions.html', data)


@login_required
def block_email(request):
    if request.method == 'POST':
        email = request.POST['email']
        create_blocked_email(email)
        return True
    else:
        return False


@login_required
def add_edit_messages(request):
    message = Message.objects.all().first()
    if request.method == 'POST':
        new_message = request.POST['message']
        message.message = new_message
        message.save()
        messages.success(request, 'Updated Successfully!')
        return redirect("/message")
    else:
        data = {"message": message.message}
        return render(request, 'admin_folder/message.html', data)


@login_required
def meta_details(request):
    if request.method == 'POST':
        id = request.POST['id']
        meta_title = request.POST['meta_title']
        meta_description = request.POST['meta_description']
        meta_keyword = request.POST['meta_keyword']
        meta_data = Pages.objects.get(id=id)
        meta_data.title = meta_title
        meta_data.description = meta_description
        meta_data.keywords = meta_keyword
        meta_data.save()
        messages.success(request, 'Updated Successfully!')
        return redirect("/meta")
    else:
        pages = Pages.objects.all()
        data = {"pages": pages}
        return render(request, 'admin_folder/meta.html', data)


@login_required
def block_ip(request):
    if request.method == 'POST':
        ip = request.POST['ip']
        create_blocked_ip(ip)
        return True
    else:
        return False


@login_required
def block_words(request):
    if request.method == 'POST':
        words = request.POST['message']
        for i in words.split(' '):
            create_blocked_word(i)
        return True
    else:
        return False


@login_required
def block_name(request):
    if request.method == 'POST':
        name = request.POST['name']
        create_blocked_name(name)
        return True
    else:
        return False


def login_function(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/dashboard")
        else:
            messages.error(request, 'Invalid Credentials!')
            return redirect("/login")
    else:
        if request.user.is_authenticated:
            return redirect('/dashboard')
        else:
            website = WebsiteContent.objects.first()
            data = {'current': 'login', 'title': 'Login', 'city': get_cities(), 'website': website}
            return render(request, 'login.html', data)


def accounts_login(request):
    messages.info(request, 'Invalid User. Login Required!')
    return redirect('/login')


def logout_fun(request):
    logout(request)
    return redirect('/login')


@login_required
def change_password(request):
    if request.method == 'POST':
        current = request.POST.get('old_password')
        new = request.POST.get('new_password')
        confirm = request.POST.get('confirm_password')

        # Check if new and confirm passwords match
        if new != confirm:
            messages.error(request, "New and Confirm passwords don't match")
            return redirect('/settings')

        # Authenticate the user with the provided old password
        user = authenticate(username=request.user.username, password=current)

        # If user is authenticated, update the password
        if user is not None:
            # Update the user's password
            user.set_password(new)
            user.save()

            # Log the user in with the new password
            login(request, user)

            messages.success(request, 'Your password was successfully updated!')
            return redirect('/dashboard')  # Redirect to the dashboard or any desired page after password change
        else:
            messages.error(request, 'Wrong current password')

    # If the request method is not POST, render the settings page
    return render(request, 'admin_folder/settings.html', {'title': 'Settings'})


@login_required
def IndexCheck(request):
    amenities = Amenities.objects.all().count()
    properties = ProjectDetails.objects.all().count()
    data = {'amenities': amenities, 'properties': properties}
    return render(request, 'admin_folder/dashboard.html', data)


@login_required
def add_amenities(request):
    if request.method == 'POST':
        img = request.FILES.get('img')
        name = request.POST['name']
        try:
            if img:
                Amenities.objects.create(img=img, name=name)
            else:
                Amenities.objects.create(name=name)
            messages.error(request, 'Amenity Added successfully')
        except IntegrityError:
            messages.error(request, 'Amenity with same name already exists!')
        return redirect('/add-amenities')
    else:
        amenities = Amenities.objects.all()
        data = {'amenities': amenities}
        return render(request, 'admin_folder/add_amenities.html', data)


@login_required
def edit_amenities(request):
    if request.method == 'POST':
        pk = request.POST['id']
        img = request.FILES.get('img')
        name = request.POST['name']
        a = Amenities.objects.get(id=pk)
        if a.name != name:
            amenities = Amenities.objects.filter(name=name).exclude(id=pk)
            if amenities.count() > 0:
                messages.error(request, 'Amenity with same name already exists!')
                return redirect('/add-amenities')
        if img:
            a.img = img
        a.name = name
        a.save()
        messages.success(request, 'Amenity Saved successfully')
        return redirect('/add-amenities')
    else:
        messages.info(request, 'Invalid Request')
        return redirect('/add-amenities')


@login_required
def delete_amenities(request):
    if request.method == 'POST':
        id = request.POST['id']
        Amenities.objects.get(id=id).delete()
        return redirect('/add-amenities')
    else:
        messages.info(request, 'Invalid Request!')
        return redirect('/add-amenities')


@login_required
def add_builder(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST.get('description')
        disclaimer = request.POST.get('disclaimer')
        img = request.FILES.get('img')
        try:
            Builder.objects.create(name=name, description=description, disclaimer=disclaimer, img=img)
            messages.success(request, 'Builder Added successfully')
        except IntegrityError:
            messages.error(request, 'Builder with same name already exists!')
        return redirect('/add-builder')
    else:
        builder = Builder.objects.all()
        data = {'builder': builder}
        return render(request, 'admin_folder/add_builder.html', data)


@login_required
def edit_builder(request):
    if request.method == 'POST':
        pk = request.POST['id']
        name = request.POST['name']
        description = request.POST.get('description')
        disclaimer = request.POST.get('disclaimer')
        img = request.FILES.get('img')
        a = Builder.objects.get(id=pk)
        if a.name != name:
            slug = slugify(name)
            builder = Builder.objects.filter(slug=slug).exclude(id=pk)
            if builder.count() > 0:
                messages.error(request, 'Builder with same name already exists!')
                return redirect('/add-builder')
        if img:
            a.img = img
        a.name = name
        a.description = description
        a.disclaimer = disclaimer
        a.save()
        messages.success(request, 'Builder Saved successfully')
        return redirect('/add-builder')
    else:
        messages.info(request, 'Invalid Request')
        return redirect('/add-builder')


@login_required
def delete_builder(request):
    if request.method == 'POST':
        pk = request.POST['id']
        Builder.objects.get(id=pk).delete()
        return redirect('/add-builder')
    else:
        messages.info(request, 'Invalid Request!')
        return redirect('/add-builder')


@login_required
def add_events(request):
    if request.method == 'POST':
        title = request.POST['title']
        location = request.POST.get('location')
        event_date = request.POST.get('date')
        description = request.POST.get('description')
        img = request.FILES.get('img')
        try:
            EventsAndCampaigns.objects.create(title=title, description=description, img=img,
                                              location=location, event_date=event_date)
            messages.success(request, 'Event Added successfully')
        except IntegrityError:
            messages.error(request, 'Events with same title already exists!')
        return redirect('/add-events')
    else:
        events = [{'title': i.title, 'description': i.description, 'event_date': str(i.event_date),
                   'location': i.location, 'img': i.img
                   } for i in EventsAndCampaigns.objects.all()]
        data = {'events': events}
        return render(request, 'admin_folder/add_events.html', data)


@login_required
def edit_events(request):
    if request.method == 'POST':
        pk = request.POST['id']
        name = request.POST['name']
        location = request.POST.get('location')
        event_date = request.POST.get('date')
        description = request.POST.get('description')
        img = request.FILES.get('img')
        a = EventsAndCampaigns.objects.get(id=pk)
        if a.name != name:
            slug = slugify(name)
            builder = EventsAndCampaigns.objects.filter(slug=slug).exclude(id=pk)
            if builder.count() > 0:
                messages.error(request, 'Event with same title already exists!')
                return redirect('/add-events')
        if img:
            a.img = img
        a.name = name
        a.description = description
        a.save()
        messages.success(request, 'Event Saved successfully')
        return redirect('/add-events')
    else:
        messages.info(request, 'Invalid Request')
        return redirect('/add-events')


@login_required
def delete_events(request):
    if request.method == 'POST':
        pk = request.POST['id']
        EventsAndCampaigns.objects.get(id=pk).delete()
        return redirect('/add-events')
    else:
        messages.info(request, 'Invalid Request!')
        return redirect('/add-events')


@login_required
def add_awards(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST.get('description')
        img = request.FILES.get('img')
        AwardsAndRecognitions.objects.create(title=name, description=description, img=img)
        messages.success(request, 'Award Added successfully')
        return redirect('/add-awards')
    else:
        awards = AwardsAndRecognitions.objects.all()
        data = {'awards': awards}
        return render(request, 'admin_folder/add_awards.html', data)


@login_required
def edit_awards(request):
    if request.method == 'POST':
        pk = request.POST['id']
        name = request.POST['name']
        description = request.POST.get('description')
        img = request.FILES.get('img')
        a = AwardsAndRecognitions.objects.get(id=pk)
        if img:
            a.img = img
        a.title = name
        a.description = description
        a.save()
        messages.success(request, 'Builder Saved successfully')
        return redirect('/add-awards')
    else:
        messages.info(request, 'Invalid Request')
        return redirect('/add-awards')


@login_required
def delete_awards(request):
    if request.method == 'POST':
        pk = request.POST['id']
        AwardsAndRecognitions.objects.get(id=pk).delete()
        return redirect('/add-awards')
    else:
        messages.info(request, 'Invalid Request!')
        return redirect('/add-awards')


@login_required
def add_testimonial(request):
    if request.method == 'POST':
        name = request.POST['name']
        testimonial = request.POST.get('testimonial')
        designation = request.POST.get('designation')
        img = request.FILES.get('img')
        try:
            Testimonials.objects.create(
                name=name, testimonial=testimonial, img=img, designation=designation
            )
            messages.success(request, 'Testimonial Added successfully')
        except IntegrityError:
            messages.error(request, 'Testimonial with same name already exists!')
        return redirect('/add-testimonial')
    else:
        testimonial = Testimonials.objects.all()
        data = {'testimonial': testimonial}
        return render(request, 'admin_folder/add_testimonial.html', data)


@login_required
def edit_testimonial(request):
    if request.method == 'POST':
        pk = request.POST['id']
        name = request.POST['name']
        testimonial = request.POST.get('testimonial')
        designation = request.POST.get('testimonial')
        img = request.FILES.get('img')
        a = Testimonials.objects.get(id=pk)
        if a.name != name:
            slug = slugify(name)
            testimonial = Testimonials.objects.filter(slug=slug).exclude(id=pk)
            if testimonial.count() > 0:
                messages.error(request, 'Testimonial with same name already exists!')
                return redirect('/add-testimonial')
        if img:
            a.img = img
        a.name = name
        a.testimonial = testimonial
        a.designation = designation
        a.save()
        messages.success(request, 'Testimonial Saved successfully')
        return redirect('/add-testimonial')
    else:
        messages.info(request, 'Invalid Request')
        return redirect('/add-testimonial')


@login_required
def delete_testimonial(request):
    if request.method == 'POST':
        pk = request.POST['id']
        Testimonials.objects.get(id=pk).delete()
        return redirect('/add-testimonial')
    else:
        messages.info(request, 'Invalid Request!')
        return redirect('/add-testimonial')


@login_required
def add_associate(request):
    if request.method == 'POST':
        img = request.FILES.get('img')
        Association.objects.create(img=img)
        messages.success(request, 'Associate Added successfully')
        return redirect('/association')
    else:
        association = Association.objects.all()
        data = {'association': association}
        return render(request, 'admin_folder/association.html', data)


@login_required
def delete_associate(request):
    if request.method == 'POST':
        pk = request.POST['id']
        Association.objects.get(id=pk).delete()
        return redirect('/association')
    else:
        messages.info(request, 'Invalid Request!')
        return redirect('/association')


@login_required
def add_property(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')

        video_link = request.POST.get('video_link')
        map_link = request.POST.get('map_link')

        rera_no = request.POST.get('rera_no')
        dld_permit_number = request.POST.get('dld_permit_number')
        possession = request.POST.get('possession')
        property_type = request.POST.get('property_type')

        city_id = request.POST.get('city')
        city = Cities.objects.get(id=city_id)
        builder_id = request.POST.get('builder')
        meta_title = request.POST.get('meta_title')
        meta_keywords = request.POST.get('meta_keywords')
        meta_description = request.POST.get('meta_description')

        location = request.POST.get('location')
        if builder_id:
            builder = Builder.objects.get(id=builder_id)
        else:
            builder = None

        project_area = request.POST.get('project_area')
        project_type = request.POST.get('project_type')
        property_type_2 = request.POST.get('property_type_2')
        project_units = request.POST.get('project_units')
        project_buildup = request.POST.get('project_buildup')
        project_price = request.POST.get('project_price')
        project_status = request.POST.get('project_status')
        project_status_1 = request.POST.get('project_status_1')

        email = request.POST.get('email')
        phone = request.POST.get('phone')
        whatsapp = request.POST.get('whatsapp')
        property_id = request.POST.get('property_id')

        master_plan = request.FILES.get('master_plan')
        master_plan_pdf = request.FILES.get('master_plan_pdf')
        brochure = request.FILES.get('brochure')

        is_featured = True if request.POST.get('is_featured') == 'Yes' else False
        project = ProjectDetails.objects.create(
            title=title, description=description, video_link=video_link, map_link=map_link,
            project_area=project_area, project_type=project_type, project_units=project_units,
            project_buildup=project_buildup, project_price=project_price, project_status=project_status,
            contact_email=email, contact_phone=phone, contact_whatsapp=whatsapp, is_featured=is_featured,
            city=city, builder=builder, master_plan=master_plan, location=location, rera_no=rera_no,
            dld_permit_number=dld_permit_number, possession=possession, property_type=property_type, master_plan_pdf=master_plan_pdf,
            brochure=brochure, project_status_1=project_status_1, property_id=property_id,
            meta_keywords=meta_keywords, meta_description=meta_description, meta_title=meta_title,
            property_type_2=property_type_2
        )

        num_of_pricing = request.POST.get('num_of_pricing')
        for i in range(1, int(num_of_pricing) + 1):
            propertyy = request.POST.get('property_' + str(i))
            builtup = request.POST.get('builtup_area_' + str(i))
            carpet = request.POST.get('carpet_area_' + str(i))
            price = request.POST.get('basic_pricing_' + str(i))
            if propertyy:
                PropertyPricing.objects.create(
                    project=project, property=propertyy, builtup=builtup, carpet=carpet, price=price
                )

        num_of_locations = request.POST.get('num_of_locations')
        for i in range(1, int(num_of_locations) + 1):
            location_title = request.POST.get('title_' + str(i))
            distance = request.POST.get('distance_' + str(i))
            if location_title:
                PropertyAdvantages.objects.create(
                    project=project, title=location_title, distance=distance
                )

        num_of_floors = request.POST.get('num_of_floors')
        for i in range(1, int(num_of_floors) + 1):
            name = request.POST.get('floor_' + str(i))
            tag1 = request.POST.get('tag_1_' + str(i))
            tag2 = request.POST.get('tag_2_' + str(i))
            tag3 = request.POST.get('tag_3_' + str(i))
            tag4 = request.POST.get('tag_4_' + str(i))
            flor_img = request.FILES.get('floor_img_' + str(i))
            flor_pdf = request.FILES.get('floor_pdf_' + str(i))
            des = request.POST.get('floor_dec_' + str(i))
            if name:
                PropertyFloors.objects.create(
                    project=project, name=name, tag1=tag1, tag2=tag2, tag3=tag3, tag4=tag4,
                    img=flor_img, description=des, pdf=flor_pdf
                )

        for i in Amenities.objects.all():
            checkbox = bool(request.POST.get('check' + str(i.id)))
            if checkbox:
                PropertyAmenities.objects.create(
                    project=project, amenity=i
                )

        buffer_id = request.POST.get('buffer_id')
        buffer_images = BufferImages.objects.filter(buffer_id=buffer_id)
        counter = 0
        for i in buffer_images:
            counter += 1
            extension = str(i.img).split('.')[-1]
            new_name = os.path.join(base_dir, str('properties/' + str(buffer_id) + str(counter) + '.' + extension))
            print(shutil.move(os.path.join(base_dir, str(i.img)), new_name))

            PropertyImages.objects.create(
                project=project, img=new_name.split('media/')[-1]
            )
        buffer_images.delete()
        messages.info(request, 'Property Added Successfully.')
        return redirect('/view-properties')
    else:
        buffer_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        amenities = Amenities.objects.all()
        builder = Builder.objects.all()
        cities = Cities.objects.all()
        data = {'amenities': amenities, 'buffer_id': buffer_id, 'builder': builder, 'cities': cities,
                "BHK": [i[0] for i in ProjectDetails.BHK_Choices],
                "location": [i[0] for i in ProjectDetails.Location_Choices],
                "budget": [i[0] for i in ProjectDetails.Cost_choices]}
        return render(request, 'admin_folder/add_property.html', data)


@login_required
def view_properties(request):
    projects = ProjectDetails.objects.all()
    data = {'projects': projects}
    return render(request, 'admin_folder/view_properties.html', data)


@login_required
def delete_property(request):
    if request.method == 'POST':
        pro_id = request.POST['id']
        project = ProjectDetails.objects.get(id=pro_id)
        project.delete()
        messages.info(request, 'Property deleted successfully!')
        return redirect('/view-properties')
    else:
        messages.info(request, 'Invalid Request!')
        return redirect('/view-properties')


@login_required
def check_property_exist(request):
    if request.method == 'POST':
        title = request.POST['title']
        pk = request.POST.get('id')
        slug = slugify(title)
        if pk:
            project = ProjectDetails.objects.filter(slug=slug).exclude(id=pk)
        else:
            project = ProjectDetails.objects.filter(slug=slug)

        if project.count() > 0:
            return HttpResponse('no')
        else:
            return HttpResponse('yes')


@login_required
def edit_property(request):
    if request.method == 'POST':
        pro_id = request.POST['id']
        project = ProjectDetails.objects.get(id=pro_id)
        buffer_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        project_amenities = [i.amenity.id for i in PropertyAmenities.objects.filter(project=project)]
        floor_num = 0
        floor = []
        for i in PropertyFloors.objects.filter(project=project):
            floor_num += 1
            floor.append({'floor': i, 'num': floor_num})
        pricing_num = 0
        pricing = []
        for i in PropertyPricing.objects.filter(project=project):
            pricing_num += 1
            pricing.append({'floor': i, 'num': pricing_num})
        loc_num = 0
        locations = []
        for i in PropertyAdvantages.objects.filter(project=project):
            loc_num += 1
            locations.append({'floor': i, 'num': loc_num})
        gallery = PropertyImages.objects.filter(project=project)
        builder = Builder.objects.all()
        cities = Cities.objects.all()
        amenities = Amenities.objects.all()
        num_of_floors = len(floor)
        num_of_pricing = len(pricing)
        num_of_locations = len(locations)
        data = {'project_amenities': project_amenities, 'buffer_id': buffer_id, 'project': project,
                'floor': floor, 'pricing': pricing, 'locations': locations, 'num_of_pricing': num_of_pricing,
                'gallery': gallery, 'builder': builder, 'cities': cities, 'num_of_locations': num_of_locations,
                'amenities': amenities, 'num_of_floors': num_of_floors,
                "BHK": [i[0] for i in ProjectDetails.BHK_Choices],
                "location": [i[0] for i in ProjectDetails.Location_Choices],
                "budget": [i[0] for i in ProjectDetails.Cost_choices]
                }
        return render(request, 'admin_folder/edit_property.html', data)
    else:
        messages.info(request, 'Invalid Request!')
        return redirect('/view-properties')


@login_required
def edit_property_details(request, pk):
    if request.method == 'POST':
        project = ProjectDetails.objects.get(id=pk)
        title = request.POST.get('title')
        description = request.POST.get('description')
        city_id = request.POST.get('city')
        city = Cities.objects.get(id=city_id)
        builder_id = request.POST.get('builder')
        location = request.POST.get('location')

        rera_no = request.POST.get('rera_no')
        dld_permit_number = request.POST.get('dld_permit_number')
        possession = request.POST.get('possession')
        property_type = request.POST.get('property_type')
        meta_keywords = request.POST.get('meta_keywords')
        meta_description = request.POST.get('meta_description')
        meta_title = request.POST.get('meta_title')

        if builder_id:
            builder = Builder.objects.get(id=builder_id)
        else:
            builder = None
        video_link = request.POST.get('video_link')
        map_link = request.POST.get('map_link')
        project_area = request.POST.get('project_area')
        project_type = request.POST.get('project_type')
        property_type_2 = request.POST.get('property_type_2')
        project_units = request.POST.get('project_units')
        project_buildup = request.POST.get('project_buildup')
        project_price = request.POST.get('project_price')
        project_status = request.POST.get('project_status')
        project_status_1 = request.POST.get('project_status_1')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        whatsapp = request.POST.get('whatsapp')
        property_id = request.POST.get('property_id')
        master_plan = request.FILES.get('master_plan')
        master_plan_pdf = request.FILES.get('master_plan_pdf')
        brochure = request.FILES.get('brochure')

        is_featured = True if request.POST.get('is_featured') == 'Yes' else False
        project.rera_no = rera_no
        project.dld_permit_number = dld_permit_number
        project.possession = possession
        project.property_type = property_type
        project.title = title
        project.description = description
        project.video_link = video_link
        project.map_link = map_link
        project.project_area = project_area
        project.project_type = project_type
        project.property_type_2 = property_type_2
        project.project_units = project_units
        project.project_buildup = project_buildup
        project.project_price = project_price
        project.project_status = project_status
        project.project_status_1 = project_status_1
        project.contact_email = email
        project.contact_phone = phone
        project.contact_whatsapp = whatsapp
        project.is_featured = is_featured
        project.city = city
        project.builder = builder
        project.location = location
        project.property_id = property_id
        # meta details
        project.meta_keywords = meta_keywords
        project.meta_description = meta_description
        project.meta_title = meta_title
        if master_plan:
            project.master_plan = master_plan
        if master_plan_pdf:
            project.master_plan_pdf = master_plan_pdf
        if brochure:
            project.brochure = brochure
        project.save()

        PropertyPricing.objects.filter(project=project).delete()
        num_of_pricing = request.POST.get('num_of_pricing')
        for i in range(1, int(num_of_pricing) + 1):
            propertyy = request.POST.get('property_' + str(i))
            builtup = request.POST.get('builtup_area_' + str(i))
            carpet = request.POST.get('carpet_area_' + str(i))
            price = request.POST.get('basic_pricing_' + str(i))
            if propertyy:
                PropertyPricing.objects.create(
                    project=project, property=propertyy, builtup=builtup, carpet=carpet, price=price
                )

        PropertyAdvantages.objects.filter(project=project).delete()
        num_of_locations = request.POST.get('num_of_locations')
        for i in range(1, int(num_of_locations) + 1):
            location_title = request.POST.get('title_' + str(i))
            distance = request.POST.get('distance_' + str(i))
            if location_title:
                PropertyAdvantages.objects.create(
                    project=project, title=location_title, distance=distance
                )

        num_of_floors = request.POST.get('num_of_floors')
        floor_delete_list = []
        for i in range(1, int(num_of_floors) + 1):
            floor = request.POST.get('floorid_' + str(i))
            if floor:
                floor = floor.split('_')[-1]
                floor_delete_list.append(floor)
            else:
                floor = False
            name = request.POST.get('floor_' + str(i))
            tag1 = request.POST.get('tag_1_' + str(i))
            tag2 = request.POST.get('tag_2_' + str(i))
            tag3 = request.POST.get('tag_3_' + str(i))
            tag4 = request.POST.get('tag_4_' + str(i))
            des = request.POST.get('floor_dec_' + str(i))
            flor_img = request.FILES.get('floor_img_' + str(i))
            flor_pdf = request.FILES.get('floor_pdf_' + str(i))
            if floor:
                f = PropertyFloors.objects.get(id=floor)
                f.name = name
                f.tag1 = tag1
                f.tag2 = tag2
                f.tag3 = tag3
                f.tag4 = tag4
                if flor_img:
                    f.img = flor_img
                if flor_pdf:
                    f.pdf = flor_pdf
                f.description = des
                f.save()
            else:
                if name:
                    property_floor = PropertyFloors.objects.create(
                        project=project, name=name, tag1=tag1, tag2=tag2, tag3=tag3, tag4=tag4,
                        img=flor_img, description=des
                    )
                    floor_delete_list.append(property_floor.id)
        PropertyFloors.objects.filter(project=project).exclude(id__in=floor_delete_list).delete()

        PropertyAmenities.objects.filter(project=project).delete()
        for i in Amenities.objects.all():
            checkbox = bool(request.POST.get('check' + str(i.id)))
            if checkbox:
                PropertyAmenities.objects.create(
                    project=project, amenity=i
                )

        buffer_id = request.POST.get('buffer_id')
        buffer_images = BufferImages.objects.filter(buffer_id=buffer_id)
        counter = 0
        for i in buffer_images:
            counter += 1
            extension = str(i.img).split('.')[-1]
            new_name = os.path.join(base_dir, str('properties/' + str(buffer_id) + str(counter) + '.' + extension))
            shutil.move(os.path.join(base_dir, str(i.img)), new_name)

            PropertyImages.objects.create(
                project=project, img=new_name.split('media/')[-1]
            )
        buffer_images.delete()

        return redirect('/view-properties')
    else:
        return redirect('/view-properties')


@login_required
def upload_buffer_image(request):
    buffer_id = request.POST.get('buffer_id')
    img = request.FILES.get('file')
    BufferImages.objects.create(
        img=img, buffer_id=buffer_id
    )
    image_list = [{'img': str(i.img), 'id': i.id} for i in BufferImages.objects.filter(buffer_id=buffer_id)]
    return HttpResponse(json.dumps(image_list))


@login_required
def remove_buffer_image(request):
    buffer_id = request.POST['buffer_id']
    pk = request.POST['id']
    buffer = BufferImages.objects.get(id=pk)
    os.remove(os.path.join(base_dir, str(buffer.img)))
    buffer.delete()
    image_list = [{'img': str(i.img), 'id': i.id} for i in BufferImages.objects.filter(buffer_id=buffer_id)]
    return HttpResponse(json.dumps(image_list))


@login_required
def remove_previous_image(request):
    project_id = request.POST['project_id']
    pk = request.POST['id']
    image = PropertyImages.objects.get(id=pk)
    os.remove(os.path.join(base_dir, str(image.img)))
    image.delete()
    image_list = [{'img': str(i.img), 'id': i.id} for i in PropertyImages.objects.filter(project__id=project_id)]
    return HttpResponse(json.dumps(image_list))


@login_required
def settings_page(request):
    form = PasswordChangeForm(request.user)
    data = {'form': form, 'title': 'Settings'}
    return render(request, 'admin_folder/settings.html', data)


@login_required
def website_content(request):
    if request.method == 'POST':
        pk = request.POST['id']
        call_number = request.POST['call_number']
        active_listing = request.POST['active_listing']
        worth_sold = request.POST['worth_sold']
        happy_customers = request.POST['happy_customers']
        relationship = request.POST['relationship']
        address = request.POST['address']
        footer_about = request.POST['footer_about']
        featured = request.POST['featured']
        header_script = request.POST['header_script']
        website = WebsiteContent.objects.get(id=pk)
        website.call_number = call_number
        website.active_listing = active_listing
        website.worth_sold = worth_sold
        website.happy_customers = happy_customers
        website.relationship = relationship
        website.address = address
        website.footer_about = footer_about
        website.featured = featured
        website.header_script = header_script
        website.save()
        messages.info(request, 'Website Content Changed Successfully!')
        return redirect('/website-content')
    else:
        website = WebsiteContent.objects.first()
        data = {'website': website, 'title': 'Website Content'}
        return render(request, 'admin_folder/website_content.html', data)


@login_required
def about_content(request):
    if request.method == 'POST':
        pk = request.POST['id']
        website = WebsiteContent.objects.get(id=pk)
        website.about_dream = request.POST.get('about_dream', '')
        website.about_nri = request.POST.get('about_nri', '')
        website.why_rera = request.POST.get('why_rera', '')
        website.why_deals = request.POST.get('why_deals', '')
        website.why_location = request.POST.get('why_location', '')
        website.why_providing = request.POST.get('why_providing', '')
        website.disclaimer = request.POST.get('disclaimer', '')
        website.save()
        messages.info(request, 'Content Changed Successfully!')
        return redirect('/about-content')
    else:
        website = WebsiteContent.objects.first()
        data = {'website': website, 'title': 'Website Content'}
        return render(request, 'admin_folder/about_content.html', data)


def get_project_images(request):
    if request.method == 'POST':
        pk = request.POST['id']
        image_list = [str(i.img) for i in PropertyImages.objects.filter(project__id=pk)]
        return HttpResponse(json.dumps(image_list))
    else:
        return redirect('/')


def error_handling(request, exception=None):
    return redirect('/')


def sitemap_xml(request):
    urls = []

    # Static pages
    static_urls = [
        reverse('index'),
        reverse('properties'),
        reverse('contact_us'),
        reverse('about_us'),
        reverse('why_planets_properties'),
        reverse('our_team'),
        reverse('awards_and_recognitions'),
        reverse('events_all'),
    ]
    for url in static_urls:
        urls.append({
            'location': request.build_absolute_uri(url),
            'lastmod': None,
        })

    # Dynamic URLs for models
    # Cities
    cities = Cities.objects.all()
    for city in cities:
        urls.append({
            'location': request.build_absolute_uri(reverse('properties_city', args=[city.slug])),
            'lastmod': city.updated_on if hasattr(city, 'updated_on') else None,
        })

    # ProjectDetails
    projects = ProjectDetails.objects.all()
    for project in projects:
        urls.append({
            'location': request.build_absolute_uri(reverse('single_property', args=[project.slug])),
            'lastmod': project.updated_on if hasattr(project, 'updated_on') else None,
        })

    # Blogs
    blogs = Blog.objects.all()
    for blog in blogs:
        urls.append({
            'location': request.build_absolute_uri(reverse('blog_detail', args=[blog.slug])),
            'lastmod': blog.updated_on if hasattr(blog, 'updated_on') else None,
        })

    # Events
    events = EventsAndCampaigns.objects.all()
    for event in events:
        urls.append({
            'location': request.build_absolute_uri(reverse('events_single', args=[event.slug])),
            'lastmod': event.updated_on if hasattr(event, 'updated_on') else None,
        })

    # Render XML
    return render(request, 'sitemap.xml', {'urls': urls}, content_type='application/xml')


from django.shortcuts import render
from django.urls import reverse
from .models import Cities, ProjectDetails, Blog, EventsAndCampaigns, Brokers


def html_sitemap(request):
    # Collect URLs for static pages
    static_urls = [
        {'name': 'Home', 'url': reverse('index')},
        {'name': 'Properties', 'url': reverse('properties')},
        {'name': 'Contact Us', 'url': reverse('contact_us')},
        {'name': 'About Us', 'url': reverse('about_us')},
        {'name': 'Why Planets Properties', 'url': reverse('why_planets_properties')},
        {'name': 'Our Team', 'url': reverse('our_team')},
        {'name': 'Awards and Recognitions', 'url': reverse('awards_and_recognitions')},
        {'name': 'All Events', 'url': reverse('events_all')},
    ]

    # Collect URLs for dynamic pages from models
    # Cities
    cities_urls = [{'name': city.name, 'url': reverse('properties_city', args=[city.slug])} for city in
                   Cities.objects.all()]

    # Projects
    projects_urls = [{'name': project.title, 'url': reverse('single_property', args=[project.slug])} for project in
                     ProjectDetails.objects.all()]

    # Blogs
    blogs_urls = [{'name': blog.title, 'url': reverse('blog_detail', args=[blog.slug])} for blog in Blog.objects.all()]

    # Events
    events_urls = [{'name': event.title, 'url': reverse('events_single', args=[event.slug])} for event in
                   EventsAndCampaigns.objects.all()]

    context = {
        'static_urls': static_urls,
        'cities_urls': cities_urls,
        'projects_urls': projects_urls,
        'blogs_urls': blogs_urls,
        'events_urls': events_urls,
    }

    return render(request, 'sitemap.html', context)


def blog_list(request):
    blogs = Blog.objects.all().order_by('-created_on')  # Order by latest created
    context = {
        'title': 'Blog List',
        'page_description': 'Explore our latest blog posts and insights.',
        'page_keywords': 'Blog, Articles, Real Estate, Updates',
        'blogs': blogs,
    }
    return render(request, 'blogs.html', context)


def blog_detail(request, slug):
    blog = get_object_or_404(Blog, slug=slug)
    context = {
        'title': blog.meta_title if blog.meta_title else blog.title,
        'page_description': blog.meta_description,
        'page_keywords': blog.meta_keywords,
        'blog': blog,
    }
    return render(request, 'blog_detail.html', context)


def blog_manage(request):
    if request.method == "POST":
        if "id" in request.POST:
            blog = get_object_or_404(Blog, id=request.POST["id"])
            blog.title = request.POST["title"]
            blog.meta_keywords = request.POST["meta_keywords"]
            blog.meta_description = request.POST["meta_description"]
            blog.description = request.POST.get("description", "")
            if request.FILES.get("img"):
                blog.img = request.FILES["img"]
            blog.save()
            messages.success(request, "Blog updated successfully!")
        else:
            title = request.POST["title"]
            meta_keywords = request.POST["meta_keywords"]
            meta_description = request.POST["meta_description"]
            description = request.POST.get("description", "")
            img = request.FILES.get("img")
            Blog.objects.create(title=title, meta_keywords=meta_keywords, meta_description=meta_description,
                                description=description, img=img)
            messages.success(request, "Blog created successfully!")
        return redirect("blog_manage")

    blogs = Blog.objects.all().order_by("-created_on")
    return render(request, "admin_folder/blog_manage.html", {"blogs": blogs})


def blog_delete(request, id):
    blog = get_object_or_404(Blog, id=id)
    blog.delete()
    messages.success(request, "Blog deleted successfully!")
    return redirect("blog_manage")


def manage_team(request):
    team = TeamMembers.objects.all()
    if request.method == "POST":
        # Get data from form
        member_id = request.POST.get('id')  # Check if an ID is provided
        name = request.POST.get('name')
        description = request.POST.get('description')
        img = request.FILES.get('img')

        if member_id:  # Update existing member
            member = get_object_or_404(TeamMembers, id=member_id)
            member.name = name
            member.description = description
            if img:  # Update image only if a new one is uploaded
                member.img = img
            member.save()
            messages.success(request, "Team member updated successfully!")
        else:  # Add new member
            if not TeamMembers.objects.filter(name=name).exists():
                new_member = TeamMembers(name=name, description=description, img=img)
                new_member.save()
                messages.success(request, "Team member added successfully!")
            else:
                messages.error(request, "A team member with this name already exists.")

        return redirect('manage_team')

    return render(request, 'admin_folder/add_team.html', {'team': team})


def delete_team_member(request):
    if request.method == "POST":
        member_id = request.POST.get('id')
        member = get_object_or_404(TeamMembers, id=member_id)
        member.delete()
        messages.success(request, "Team member deleted successfully!")
    return redirect('manage_team')


def manage_cities(request):
    if request.method == "POST":
        city_id = request.POST.get("id")
        if city_id:  # Edit existing city
            city = get_object_or_404(Cities, id=city_id)
            city.name = request.POST.get("title")
            city.meta_title = request.POST.get("meta_title")
            city.meta_keywords = request.POST.get("meta_keywords")
            city.meta_description = request.POST.get("meta_description")
            if 'img' in request.FILES:
                city.img = request.FILES['img']
            city.save()
            messages.success(request, "City updated successfully.")
        else:  # Add new city
            city = Cities(
                name=request.POST.get("title"),
                meta_title=request.POST.get("meta_title"),
                meta_keywords=request.POST.get("meta_keywords"),
                meta_description=request.POST.get("meta_description"),
            )
            if 'img' in request.FILES:
                city.img = request.FILES['img']
            city.save()
            messages.success(request, "City added successfully.")
        return redirect("manage_cities")

    # Serialize city data for JavaScript
    cities = list(Cities.objects.values(
        "id", "name", "meta_title", "meta_keywords", "meta_description"
    ))
    for city in cities:
        obj = Cities.objects.get(id=city["id"])
        city["img_url"] = obj.img.url if obj.img else None

    # Convert to JSON with null instead of None
    cities_json = json.dumps(cities)

    return render(request, "admin_folder/cities_manage.html", {
        "cities": Cities.objects.all(),
        "cities_data": cities_json
    })
