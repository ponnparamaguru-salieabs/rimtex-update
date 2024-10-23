from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import UserForm
from .models import User, UserProfile, Machine
from django.http import JsonResponse
from django.core.files.storage import default_storage

# Login View
def login_view(request):
    return render(request, 'login.html')

# Machine List View
#@login_required
def machineList(request):
    machines = Machine.objects.all()  
    return render(request, 'machine_list.html', {
        'machines': machines,
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Machines', 'url': '#'}
        ],
        'active_menu': 'machine'
    })

# Add Machine View
#@login_required
def machineAdd(request):
    if request.method == 'POST':
        # Handle form data and file upload
        type = request.POST.get('type')
        code = request.POST.get('code')
        model = request.POST.get('model')
        make_year = request.POST.get('make_year')
        design = request.POST.get('design')
        manufacturer = request.POST.get('manufacturer')
        num_inputs = request.POST.get('num_inputs')
        num_outputs = request.POST.get('num_outputs')
        image = request.POST.get('image')  # This should be the URL or file path
        status = 'status' in request.POST

        # Save machine instance
        machine = Machine(
            type=type,
            code=code,
            model=model,
            make_year=make_year,
            design=design,
            manufacturer=manufacturer,
            num_inputs=num_inputs,
            num_outputs=num_outputs,
            image=image,
            status=status
        )
        machine.save()

        messages.success(request, 'Machine added successfully')
        return redirect('machineList')
    
    return render(request, 'machine_add.html', {
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Machines', 'url': '/machine-list'},
            {'name': 'Add Machine', 'url': '/machine-add'}
        ],
        'active_menu': 'machine'})

def file_upload(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        file_name = default_storage.save('machine_images/' + uploaded_file.name, uploaded_file)
        file_url = default_storage.url(file_name)
        return JsonResponse({'fileUrl': file_url})
    return JsonResponse({'error': 'Invalid request'}, status=400)

# Edit Machine View
#@login_required
def machineEdit(request, id):    
    machine = get_object_or_404(Machine, id=id)

    if request.method == 'POST':
        # Update machine fields with form data
        machine.type = request.POST.get('type')
        machine.code = request.POST.get('code')
        machine.model = request.POST.get('model')
        machine.make_year = request.POST.get('make_year')
        machine.design = request.POST.get('design')
        machine.manufacturer = request.POST.get('manufacturer')
        machine.num_inputs = request.POST.get('num_inputs')
        machine.num_outputs = request.POST.get('num_outputs')
        machine.status = 'status' in request.POST

        # Handle image upload
        image_url = request.POST.get('image')
        if image_url:
            machine.image = image_url
        machine.save()
        return redirect('machineList')  # Redirect to the machine list page after saving

    return render(request, 'machine_edit.html', {
        'machine': machine,
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Machines', 'url': '#'},
            {'name': 'Edit Machine', 'url': '#'}
        ],
        'active_menu': 'machine'
    })


# Delete Machine View
#@login_required
def machineDelete(request, id):
    if request.method == 'POST':
        # Get the machine object and delete it
        machine = get_object_or_404(Machine, id=id)
        machine.delete()
        return JsonResponse({'success': True})
    else:
        # For GET request (confirmation page)
        return render(request, 'machine_delete_confirm.html', {
            'breadcrumb': [
                {'name': 'Home', 'url': '/'},
                {'name': 'Machines', 'url': '/machine-list'},
                {'name': 'Delete Machine', 'url': f'/machine-delete/{id}'}
            ],
            'active_menu': 'machine'
        })

# User List View
#@login_required
def userList(request):
    users = User.objects.all()
    return render(request, 'user_list.html', {
        'users': users,
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'User Management', 'url': '/user-list'},
        ],
        'active_menu': 'user'
    })

# Add User View
#@login_required
def userAdd(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            phone = form.cleaned_data.get('phone')
            role = form.cleaned_data.get('role')
            permissions = {
                'mill_config_view': request.POST.get('permissions_mill_config_view') == 'on',
                'mill_config_edit': request.POST.get('permissions_mill_config_edit') == 'on',
                'line_config_view': request.POST.get('permissions_line_config_view') == 'on',
                'line_config_edit': request.POST.get('permissions_line_config_edit') == 'on',
                'reports_view': request.POST.get('permissions_reports_view') == 'on',
                'reports_edit': request.POST.get('permissions_reports_edit') == 'on',
            }

            # Check if username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect('userAdd')

            # Create the user
            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(password)  # Hash the password before saving
            )

            # Check if UserProfile already exists for this user
            user_profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'phone': phone,
                    'role': role,
                    'permissions': permissions
                }
            )

            if not created:
                # Update existing UserProfile
                user_profile.phone = phone
                user_profile.role = role
                user_profile.permissions = permissions
                user_profile.save()

            messages.success(request, 'User added/updated successfully!')
            return redirect('userList')
        else:
            return render(request, 'user_add.html', {'form': form})

    else:
        form = UserForm()

    return render(request, 'user_add.html', {
        'form': form,
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'User Management', 'url': '/user-list'},
            {'name': 'Add User', 'url': '/user-add'}
        ],
        'active_menu': 'user',
    })

# Edit User View
#@login_required
def userEdit(request, pk):
    user = get_object_or_404(User, id=pk)
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        role = request.POST.get('role')

        # Permissions
        permissions = {
            'mill_config_view': request.POST.get('permissions_mill_config_view') == 'on',
            'mill_config_edit': request.POST.get('permissions_mill_config_edit') == 'on',
            'line_config_view': request.POST.get('permissions_line_config_view') == 'on',
            'line_config_edit': request.POST.get('permissions_line_config_edit') == 'on',
            'reports_view': request.POST.get('permissions_reports_view') == 'on',
            'reports_edit': request.POST.get('permissions_reports_edit') == 'on',
        }

        if password and password == confirm_password:
            user.password = make_password(password)
        
        user.username = username
        user.email = email
        user.save()
        
        profile.phone = phone
        profile.role = role
        profile.permissions = permissions
        profile.save()

        messages.success(request, 'User updated successfully')
        return redirect('userList')

    # Prepare context for the template
    context = {
        'user': user,
        'profile': profile,
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'User Management', 'url': '/user-list'},
            {'name': 'Edit User', 'url': f'/user-edit/{pk}'}
        ],
        'active_menu': 'user'
    }

    return render(request, 'user_edit.html', context)

# Delete User View
#@login_required
def userDelete(request, pk):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('userList')

    user = get_object_or_404(User, pk=pk)
    return render(request, 'user_delete_confirm.html', {
        'user': user,
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'User Management', 'url': '/user-list'},
            {'name': 'Delete User', 'url': f'/user-delete/{pk}'}
        ],
        'active_menu': 'user'
    })

def millInfo(request):
    return render(request, 'mill_info.html', {
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Mill Information', 'url': '/mill-info'},
        ],
        'active_menu': 'millInfo'
    })

def millConfig(request):
    return render(request, 'mill_config.html', {
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Mill Configuration', 'url': '/mill-config'},
        ],
        'active_menu': 'millConfig'
    })

def millLayout(request):
    return render(request, 'mill_layout.html', {
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Mill Layout', 'url': '/mill-layout'},
        ],
        'active_menu': 'millLayout'
    })

def millLine(request):
    return render(request, 'mill_line.html', {
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Mill Line Configuration', 'url': '/mill-line'},
        ],
        'active_menu': 'millLine'
    })

def millReport(request):
    return render(request, 'mill_report.html', {
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Mill Report', 'url': '/mill-report'},
        ],
        'active_menu': 'millReport'
    })

# Base View (if needed)
""" def base(request):
    return render(request, 'topbar.html') """

def notAuth(request):
    return render(request, 'unauth.html')

def drawflow_view(request):
    return render(request, 'drawflow.html')
