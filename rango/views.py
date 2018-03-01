from django.shortcuts import render
# Import the Category model
from rango.models import Category, Page, UserProfile
from django.http import HttpResponse, HttpResponseRedirect
from rango.forms import CategoryForm
from rango.forms import PageForm, UserForm, UserProfileForm
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from datetime import datetime
from rango.webhose_search import run_query
from django.shortcuts import redirect


def index(request):
    request.session.set_test_cookie()
    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]

    context_dict = {'categories': category_list, 'pages': page_list}

    # Obtain our Response object early so we can add cookie information. 

    # Call the helper function to handle the cookies
    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']

    # Return response back to the user, updating any cookies that need changed
    response = render(request, 'rango/index.html', context_dict)
    return response


def about(request):
    if request.session.test_cookie_worked():
        print("TEST COOKIE WORKED!")
        request.session.delete_test_cookie()
    context_dict = {}
    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']

    response = render(request, 'rango/about.html', context_dict)
    return response


def show_category(request, category_name_slug):
    context_dict = {}

    try:
        category = Category.objects.get(slug=category_name_slug)
        pages = Page.objects.filter(category=category).order_by('-views')
        context_dict['pages'] = pages
        context_dict['category'] = category
    except Category.DoesNotExist:
        context_dict['category'] = None
        context_dict['pages'] = None

    context_dict['query'] = category.name
    result_list = []
    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            result_list = run_query(query)
            context_dict['query'] = query
            context_dict['result_list'] = result_list

    return render(request, 'rango/category.html', context_dict)


@login_required
def add_category(request):
    form = CategoryForm()

    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            print(form.errors)

    return render(request, 'rango/add_category.html', {'form': form})


@login_required
def add_page(request, category_name_slug):
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        category = None

    form = PageForm()
    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.views = 0
                page.save()
                return show_category(request, category_name_slug)
        else:
            print(form.errors)

    context_dict = {'form': form, 'category': category}
    return render(request, 'rango/add_page.html', context_dict)


# def register(request):
# A boolean value for telling the template
# whether the registration was successful.
# Set to False initially. Code changes values to
# True when registration succeeds.
# registered = False

# If it's a HTTP POST, we're interested in processing form data.
# if request.method == 'POST':
# Attempt to grab information from the raw form information.
# Note that we make use of both UserForm and UserProfileForm
# user_form = UserForm(data=request.POST)
# profile_form = UserProfileForm(data=request.POST)

# If the two forms are valid...
# if user_form.is_valid() and profile_form.is_valid():
# Save the user's data to the database.
# user = user_form.save()

# Now we hash the password with the set_password method
# Once hashed, we can update the user object.
# user.set_password(user.password)
# user.save()

# Now sort out the UserProfile instance.
# Since we need to set the user attribute ourselves,
# we set commit=False. This delays saving the model
# until we're ready to avoid integrity problems.
# profile = profile_form.save(commit=False)
# profile.user = user

# Did the user provide a profile picture?
# If so, we neew to get it from the input form and
# put it in the UserProfile model
# if 'picture' in request.FILES:
# profile.picture = request.FILES['picture']

# Now we save the UserProfile model instance.
# profile.save()

# Update our variable to indicate that the template
# registration was successful.
# registered = True
# else:
# Invalid form or forms - mistakes or something else?
# Print problems to the terminal.
# print(user_form.errors, profile_form.errors)

# else:
# Not a HTTP POST, so we render our form using two ModelForm instances.
# These forms will be blank, ready for user input.
# user_form = UserForm()
# profile_form = UserProfileForm()

# Render the template depending on the context.
# return render(request, 'rango/register.html', {'user_form': user_form,
# 'profile_form': profile_form,
# 'registered': registered})


# def user_login(request):
# If the request is a HTTP POST, try to pull out the relevant information.
# if request.method == 'POST':
# Gather the username and password provided by the user.
# This information is obtained from the login form.
# We use request.POST.get('<variable>') as opposed
# to request.POST['<variable>'], because the
# request.POST.get('<variable>') returns None if the
# value does not exist, while request.POST['<variable>']
# will raise a KeyError exception.
# username = request.POST.get('username')
# password = request.POST.get('password')

# Use Django's machinery to attempt to see if the username/password
# combination is valid - a User object is returned if it is.
# user = authenticate(username=username, password=password)

# If we have a User object, the details are correct
# If None (Python's way of representing the absense of a value),
# no user with the matching credentials was found
# if user:
# Is the account active? It could have been disabled.
# if user.is_active:
# If the account is valid and active, we can log the user in.
# We'll send the user back to the homepage.
# login(request, user)
# return HttpResponseRedirect(reverse('index'))
# else:
# An inactive account ws used - no logging in!
# return HttpResponse("Your Rango account is disabled.")
# else:
# Bad login details were provided. So we can't log the user in.
# print("Invalid login details supplied: {0}, {1}".format(username, password))
# context_dict = {}
# usr = User.objects.filter(username=username)
# if username == '' or not usr:
# context_dict['error'] = 'wronguser'
# else:
# if password == '':
# context_dict['error'] = 'Please enter your password!'
# else:
# context_dict['error'] = 'Wrong password!'
# return render(request, 'rango/login.html', context_dict)

# The request is not a HTTP POST, so display the login form.
# The scenario would most likely be a HTTP GET
# else:
# No context variables to pass to the template system, hence the
# blank dictionary object...
# return render(request, 'rango/login.html', {})


@login_required
def restricted(request):
    return render(request, 'rango/restricted.html', {})


# @login_required
# def user_logout(request):
#     # Since we know the user is logged in, we can just log them out.
#     logout(request)
#     # Take the user back to the homepage
#     return HttpResponseRedirect(reverse('index'))


# A helper method
def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val


# Updated the function definition
def visitor_cookie_handler(request):
    # Get the number of visits to the site.
    # We use the COOKIES.get() function to obtain the visits cookie. 
    # If the cookie exists, the value returned is casted to an integer. 
    # If the cookie doesn't exist, then the default value of 1 is used. 
    visits = int(get_server_side_cookie(request, 'visits', '1'))

    last_visit_cookie = get_server_side_cookie(request, 'last_visit', str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7], '%Y-%m-%d %H:%M:%S')

    # If it's been more than a day since the last visit...
    if (datetime.now() - last_visit_time).days > 0:
        visits = visits + 1
        # Update the last visit cookie now that we have updated the count
        request.session['last_visit'] = str(datetime.now())
    else:

        # Set the last visit cookie
        request.session['last_visit'] = last_visit_cookie

    # Update/set the visits cookie
    request.session['visits'] = visits


def search(request):
    result_list = []
    query = ''

    if request.method == 'POST':
        query = request.POST['query'].strip()
        if query:
            result_list = run_query(query)
    context_dictionary = {'previous_query': query, 'result_list': result_list}
    return render(request, 'rango/search.html', context_dictionary)


def track_url(request):
    page_id = None
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
    if page_id:
        try:
            page = Page.objects.get(id=page_id)
            page.views = page.views + 1
            page.save()
            return redirect(page.url)
        except:
            print("No page_id in get string")
            return HttpResponse("Page id {0} not found".format(page_id))

        return redirect(reverse('index'))

@login_required
def register_profile(request):
    form = UserProfileForm

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            user_profile = form.save(commit=False)
            user_profile.user = request.user
            user_profile.save()

            return redirect('index')
        else:
            print(form.errors)

    context_dict = {'form': form}

    return render(request, 'rango/profile_registration.html', context_dict)

@login_required
def profile(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect('index')

    userprofile = UserProfile.objects.get_or_create(user=user)[0]
    form = UserProfileForm(
        {'website': userprofile.website, 'picture': userprofile.picture}
    )
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if form.is_valid():
            form.save(commit=True)
            return redirect('profile', user.username)
        else:
            print(form.errors)

    return render(request, 'rango/profile.html',
                  {'userprofile': userprofile, 'selecteduser': user, 'form': form})

@login_required
def list_profiles(request):
    userprofile_list = UserProfile.objects.all()

    return render(request, 'rango/list_profiles.html',{'userprofile_list': userprofile_list})

@login_required
def like_category(request):
    cat_id = None
    if request.method == 'GET':
        cat_id = request.GET['category_id']
        likes = 0
        if cat_id:
            cat = Category.objects.get(id=int(cat_id))
            if cat:
                likes = cat.likes + 1
                cat.likes = likes
                cat.save()
        return HttpResponse(likes)


def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    if starts_with:
        cat_list = Category.objects.filter(name__istartswith=starts_with)

    if max_results > 0:
        if len(cat_list) > max_results:
            cat_list = cat_list[:max_results]
    return cat_list

def suggest_category(request):
    cat_list = []
    starts_with = ''
    if request.method == 'GET':
        starts_with = request.GET['suggestion']
    cat_list = get_category_list(8, starts_with)

    return render(request, 'rango/cats.html', {'cats': cat_list})

@login_required
def auto_add_page(request):
    cat_id =None
    url = None
    title = None
    context_dict = {}
    if request.method == 'GET':
        cat_id = request.GET['category_id']
        url = request.GET['url']
        title = request.GET['title']
        if cat_id:
            category = Category.objects.get(id=int(cat_id))
            p = Page.objects.get_or_create(category=category, title=title, url=url)
            pages = Page.objects.filter(category=category).order_by('-views')
            context_dict['pages'] = pages
    return render(request, 'rango/page_list.html', context_dict)
