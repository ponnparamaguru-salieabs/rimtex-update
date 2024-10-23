from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required,  user_passes_test
from django.contrib.auth.hashers import make_password
from django.contrib.auth import login as auth_login, authenticate
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.serializers import serialize
from django.http import JsonResponse, HttpResponseForbidden
from django.core.files.storage import default_storage
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from .forms import UserForm, MillLayoutForm
from .models import UserProfile, Machine, Mill, MillMachine, MillInfo, MillShift, MillLayout, MillLine, SetupMachine, MachineType
from .decorators import role_required, permission_required
from django.views.decorators.csrf import csrf_exempt
import json
import uuid

def is_superuser(user):
    return user.is_superuser

def is_staff(user):
    return user.is_staff

def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            if user.is_superuser:
                return redirect('machineList')
            else:
                return redirect('dashboard')
        else:
            error_message = 'Invalid username or password.'
            messages.error(request, error_message)
            error = error_message

    return render(request, 'login.html', {'error': error})

# Machine List View
@login_required
@user_passes_test(is_superuser)
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

@login_required
@user_passes_test(is_superuser)
def machineAdd(request):
    if request.method == 'POST':
        type = request.POST.get('type')
        code = request.POST.get('code')
        model = request.POST.get('model')
        make_year = request.POST.get('make_year')
        design = request.POST.get('design')
        manufacturer = request.POST.get('manufacturer')
        num_inputs = request.POST.get('num_inputs')
        num_outputs = request.POST.get('num_outputs')
        image = request.POST.get('image')  
        status = 'status' in request.POST

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
        
        relative_file_url = file_url.replace('/media/', '')

        return JsonResponse({'fileUrl': relative_file_url})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@user_passes_test(is_superuser)
def machineEdit(request, id):    
    machine = get_object_or_404(Machine, id=id)

    if request.method == 'POST':
        machine.type = request.POST.get('type')
        machine.code = request.POST.get('code')
        machine.model = request.POST.get('model')
        machine.make_year = request.POST.get('make_year')
        machine.design = request.POST.get('design')
        machine.manufacturer = request.POST.get('manufacturer')
        machine.num_inputs = request.POST.get('num_inputs')
        machine.num_outputs = request.POST.get('num_outputs')
        machine.status = 'status' in request.POST

        if request.POST.get('image'):
            machine.image = request.POST.get('image')

        machine.save()
        return redirect('machineList') 
    
    return render(request, 'machine_edit.html', {
        'machine': machine,
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Machines', 'url': '#'},
            {'name': 'Edit Machine', 'url': '#'}
        ],
        'active_menu': 'machine'
    })

@login_required
@user_passes_test(is_superuser)
def machineDelete(request, id):
    if request.method == 'POST':
        machine = get_object_or_404(Machine, id=id)
        machine.delete()
        return JsonResponse({'success': True})
    return render(request, 'machine_delete_confirm.html', {
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Machines', 'url': '/machine-list'},
            {'name': 'Delete Machine', 'url': f'/machine-delete/{id}'}
        ],
        'active_menu': 'machine'
    })

@login_required
@user_passes_test(is_superuser)
def userList(request):
    users = User.objects.filter(is_staff=True, is_superuser=False)
    return render(request, 'user_list.html', {
        'users': users,
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'User Management', 'url': '/user-list'},
        ],
        'active_menu': 'user'
    })

@login_required
@user_passes_test(is_superuser)
def userAdd(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone = request.POST.get('phone')

        if len(username) < 2:
            messages.error(request, 'Username must be at least 2 characters long.')
            return redirect('userAdd')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('userAdd')

        if not email or '@' not in email:
            messages.error(request, 'Please enter a valid email address.')
            return redirect('userAdd')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('userAdd')

        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return redirect('userAdd')

        mill_id = str(uuid.uuid4())
        mill = Mill.objects.create(mill_id=mill_id)

        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            is_staff=True
        )

        user_profile, created = UserProfile.objects.get_or_create(user=user)

        user_profile.mill = mill
        user_profile.phone = phone
        user_profile.role = 'Admin'
        user_profile.save()

        machine_types = [
            'Carding',
            'Breaker',
            'Unilap',
            'Comber',
            'Finisher',
            'Roving'
        ]

        for machine_name in machine_types:
            machine_type, created = MachineType.objects.get_or_create(
                type=machine_name
            )
            mill.machine_types.add(machine_type)

        messages.success(request, 'Mill and admin user created successfully!')
        return redirect('userList')

    return render(request, 'user_add.html', {
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'User Management', 'url': '/user-list'},
            {'name': 'Add User', 'url': '/user-add'}
        ],
        'active_menu': 'user',
    })

@login_required
@user_passes_test(is_superuser)
def userEdit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user_profile = get_object_or_404(UserProfile, user=user)

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone = request.POST.get('phone')

        if len(username) < 2:
            messages.error(request, 'Username must be at least 2 characters long.')
            return redirect('userEdit', user_id=user.id)

        if User.objects.exclude(id=user.id).filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('userEdit', user_id=user.id)

        if not email or '@' not in email:
            messages.error(request, 'Please enter a valid email address.')
            return redirect('userEdit', user_id=user.id)

        if password and password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('userEdit', user_id=user.id)
        
        user.username = username
        user.email = email

        if password:
            user.password = make_password(password)
        user.save()
        user_profile.phone = phone
        user_profile.save()

        messages.success(request, 'User updated successfully!')
        return redirect('userList')

    return render(request, 'user_edit.html', {
        'user': user,
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'User Management', 'url': '/user-list'},
            {'name': 'Edit User', 'url': f'/mill-user-edit/{user.id}'}
        ],
        'active_menu': 'user',
    })

@login_required
@user_passes_test(is_superuser)
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

# Mill Info View
""" @login_required
@role_required(['Admin', 'Manager', 'Supervisor'])
@permission_required(['mill_config_view']) """
def millUserList(request):
    user_profile = UserProfile.objects.get(user=request.user)
    admin_mill = user_profile.mill

    users = User.objects.filter(is_staff=False, userprofile__mill=admin_mill)

    return render(request, 'mill_user_list.html', {
        'users': users,
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Mill Users', 'url': '/mill_user_list'},
        ],
        'active_menu': 'millUser'
    })

# Add User View
""" @login_required
@role_required(['Admin']) """
def millUserAdd(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            phone = form.cleaned_data.get('phone')
            role = form.cleaned_data.get('role')

            user_profile = UserProfile.objects.get(user=request.user)
            admin_mill = user_profile.mill

            print(admin_mill.id) 

            permissions = {
                'setup_machine_view': request.POST.get('permissions_setup_machine_view') == 'on',
                'setup_machine_edit': request.POST.get('permissions_setup_machine_edit') == 'on',
                'set_shift_view': request.POST.get('permissions_set_shift_view') == 'on',
                'set_shift_edit': request.POST.get('permissions_set_shift_edit') == 'on',
                'mill_layout_view': request.POST.get('permissions_mill_layout_view') == 'on',
                'mill_layout_edit': request.POST.get('permissions_mill_layout_edit') == 'on',
                'line_config_view': request.POST.get('permissions_line_config_view') == 'on',
                'line_config_edit': request.POST.get('permissions_line_config_edit') == 'on',
                'red_flag_view': request.POST.get('permissions_red_flag_view') == 'on',
                'red_flag_edit': request.POST.get('permissions_red_flag_edit') == 'on',
                'can_manage_view': request.POST.get('permissions_can_manage_view') == 'on',
                'can_manage_edit': request.POST.get('permissions_can_manage_edit') == 'on',
                'non_scan_view': request.POST.get('permissions_non_scan_view') == 'on',
                'non_scan_edit': request.POST.get('permissions_non_scan_edit') == 'on',
                'reports_view': request.POST.get('permissions_reports_view') == 'on',
            }

            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect('millUserAdd')

            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                is_staff=False
            )

            user_profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'phone': phone,
                    'role': role,
                    'permissions': permissions,
                    'mill': admin_mill
                }
            )

            if not created:
                # Update existing UserProfile
                user_profile.phone = phone
                user_profile.role = role
                user_profile.permissions = permissions
                user_profile.mill = admin_mill  # Ensure mill ID is set
                user_profile.save()

            messages.success(request, 'User added/updated successfully!')
            return redirect('millUserList')
        else:
            for field in form:
                for error in field.errors:
                    print(f"Error in {field.name}: {error}")
            messages.error(request, 'Please correct the errors below.')

    else:
        form = UserForm()

    return render(request, 'mill_user_add.html', {
        'form': form,
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'User Management', 'url': '/user-list'},
            {'name': 'Add Mill User', 'url': '/mill-user-add'}
        ],
        'active_menu': 'millUser',
    })

# Edit User View
""" @login_required
@role_required(['Admin']) """
def millUserEdit(request, pk):
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
                'setup_machine_view': request.POST.get('permissions_setup_machine_view') == 'on',
                'setup_machine_edit': request.POST.get('permissions_setup_machine_edit') == 'on',
                'set_shift_view': request.POST.get('permissions_set_shift_view') == 'on',
                'set_shift_edit': request.POST.get('permissions_set_shift_edit') == 'on',
                'mill_layout_view': request.POST.get('permissions_mill_layout_view') == 'on',
                'mill_layout_edit': request.POST.get('permissions_mill_layout_edit') == 'on',
                'line_config_view': request.POST.get('permissions_line_config_view') == 'on',
                'line_config_edit': request.POST.get('permissions_line_config_edit') == 'on',
                'red_flag_view': request.POST.get('permissions_red_flag_view') == 'on',
                'red_flag_edit': request.POST.get('permissions_red_flag_edit') == 'on',
                'can_manage_view': request.POST.get('permissions_can_manage_view') == 'on',
                'can_manage_edit': request.POST.get('permissions_can_manage_edit') == 'on',
                'non_scan_view': request.POST.get('permissions_non_scan_view') == 'on',
                'non_scan_edit': request.POST.get('permissions_non_scan_edit') == 'on',
                'reports_view': request.POST.get('permissions_reports_view') == 'on',
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
        return redirect('millUserList')

    # Prepare context for the template
    context = {
        'user': user,
        'profile': profile,
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'User Management', 'url': '/mill-user-list'},
            {'name': 'Edit User', 'url': f'/mill-user-edit/{pk}'}
        ],
        'active_menu': 'millUser'
    }

    return render(request, 'mill_user_edit.html', context)

# Delete User View
""" @login_required
@role_required(['Admin']) """
def millUserDelete(request, pk):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('millUserList')

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


""" @login_required
@role_required(['Admin']) """
#@permission_required(['reports_view'])
def devices(request):
    return render(request, 'devices.html', {
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Device Management', 'url': '/devices'},
        ],
        'active_menu': 'devices'
    })

""" @login_required
@role_required(['Admin', 'Manager', 'Supervisor'])
@permission_required(['mill_config_view']) """
def dashboard(request):
    """ context = {
    'chart_labels': ['Carding', 'Breaker', 'Unilap'],  
    'chart_data': [15, 10, 65]  
} """
    return render(request, 'dashboard.html', {
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Dashboard', 'url': '/mill-info'},
        ],
        'active_menu': 'dashboard'
    })

def get_machine_models(request):
    machine_type = request.GET.get('type')
    
    machines = Machine.objects.filter(type=machine_type, status=True).values(
        'id', 'code', 'model', 'make_year', 'design', 'manufacturer', 
        'num_inputs', 'num_outputs', 'image', 'status'
    )

    print(machines) 
    return JsonResponse(list(machines), safe=False)

@csrf_exempt  
def add_machine(request):
    if request.method == 'POST':
        machine_type = request.POST.get('machine_type')
        machine_model = request.POST.get('machine_model')
        machine_code = request.POST.get('machine_code')
        manufacturer = request.POST.get('manufacturer')
        num_machines = request.POST.get('num_machines')
        num_starting = request.POST.get('num_starting', 1)
        design = request.POST.get('design', 0)
        make_year = request.POST.get('make_year', 0)
        num_inputs = request.POST.get('num_inputs', 0)
        num_outputs = request.POST.get('num_outputs', 0)
        image = request.POST.get('image')

        user_profile = UserProfile.objects.get(user=request.user)
        admin_mill = user_profile.mill

        if not machine_type or not machine_model or not num_machines:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        try:
            num_machines = int(num_machines)
            num_starting = int(num_starting)
        except ValueError:
            return JsonResponse({'error': 'Invalid number format'}, status=400)

        for i in range(num_machines):
            name = f"{machine_type} {str(num_starting + i).zfill(3)}"
            mill_machine = MillMachine(
                type=machine_type,
                code=machine_code,
                model=machine_model,
                make_year=make_year,
                design=design,
                manufacturer=manufacturer,
                num_inputs=num_inputs,
                num_outputs=num_outputs,
                image=image,
                machine_name=name,
                mill = admin_mill
            )
            mill_machine.save()

        return JsonResponse({'message': 'Machines added successfully!'}, status=201)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def update_machine(request, machine_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_name = data.get('new_name')

            if not new_name:
                return JsonResponse({'error': 'New name is required'}, status=400)
            
            mill_machine = MillMachine.objects.get(id=machine_id)
            mill_machine.machine_name = new_name
            mill_machine.save()
            return JsonResponse({'message': 'Machine name updated successfully!'}, status=200)

        except MillMachine.DoesNotExist:
            return JsonResponse({'error': 'Machine not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def delete_machine(request, machine_id):
    if request.method == 'POST':
        try:
            machine = MillMachine.objects.get(id=machine_id)
            machine.delete()
            return JsonResponse({'message': 'Machine deleted successfully!'}, status=200)
        except MillMachine.DoesNotExist:
            return JsonResponse({'error': 'Machine not found'}, status=404)
    return JsonResponse({'error': 'Invalid request'}, status=400)

# Mill Config View
""" @login_required
@role_required(['Admin', 'Manager', 'Supervisor'])
@permission_required(['mill_config_edit']) """
def millConfig(request):
    user_profile = UserProfile.objects.get(user=request.user)
    mill = user_profile.mill
    
    machines = Machine.objects.filter(status=True).values('code', 'model', 'type')
    mill_machines = MillMachine.objects.filter(mill=mill)
    machine_type = SetupMachine.objects.filter(is_add=True, mill=mill)
    
    return render(request, 'mill_config.html', {
        'machines': machines,
        'machine_type': machine_type,
        'mill_machines': mill_machines,
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Mill Configuration', 'url': '/mill-config'},
        ],
        'active_menu': 'millConfig',
    })


def millSetupMachine(request):
    user_profile = UserProfile.objects.get(user=request.user)
    mill = user_profile.mill
    machines = SetupMachine.objects.filter(mill=mill)
    print(machines)
    return render(request, 'mill_setup_machines.html', {
        'machines': machines,
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Mill Configuration', 'url': '/mill-config'},
        ],
        'active_menu': 'millConfig',
    })


def toggle_machine(request):
    if request.method == 'POST':
        machine_id = request.POST.get('machine_id')
        action = request.POST.get('action')

        try:
            machine = SetupMachine.objects.get(id=machine_id)
            if action == 'add':
                machine.is_add = True
            elif action == 'remove':
                machine.is_add = False
            machine.save()
            return JsonResponse({'success': True})
        except SetupMachine.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Machine not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# Mill Config View
""" @login_required
@role_required(['Admin', 'Manager', 'Supervisor'])
@permission_required(['mill_config_edit']) """
def millInfo(request):
    user_profile = UserProfile.objects.get(user=request.user)
    admin_mill = user_profile.mill   
    
    mill, created = Mill.objects.get_or_create(id=admin_mill.id)
    mill_info, created_info = MillInfo.objects.get_or_create(mill=mill)

    if request.method == 'POST':
        name = request.POST.get('name', '') 
        unit_number = request.POST.get('unit_number', '')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        logo = request.POST.get('logo')  

        mill_info.name = name
        mill_info.unit_number = unit_number
        mill_info.phone = phone
        mill_info.email = email
        mill_info.logo = logo

        mill_info.save()
        return redirect('millInfo')

    return render(request, 'mill_info.html', {
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Mill Information', 'url': '/mill-info'},
        ],
        'active_menu': 'millConfig',
        'mill': mill_info,
    })


# Mill Config View
""" @login_required
@role_required(['Admin', 'Manager', 'Supervisor'])
@permission_required(['mill_config_edit']) """
def millShift(request):
    user_profile = UserProfile.objects.get(user=request.user)
    admin_mill = user_profile.mill  
    shifts = MillShift.objects.filter(mill=admin_mill)
    shifts_data = serialize('json', shifts)

    if request.method == "POST":
        action = request.POST.get('action')  
        shift_id = request.POST.get('shift_id')

        if action == 'delete' and shift_id:  
            try:
                shift = get_object_or_404(MillShift, id=shift_id)
                shift.delete()
            except Exception as e:
                print(f"Error deleting shift: {e}")
            return redirect('millShift')

        shift_number = request.POST.get('shift_number')
        shift_name = request.POST.get('shift_name')
        start_date = request.POST.get('start_date')
        start_time = request.POST.get('start_time')
        end_date = request.POST.get('end_date')
        end_time = request.POST.get('end_time')

        start_datetime = timezone.datetime.strptime(f"{start_date} {start_time}", '%Y-%m-%d %H:%M')
        end_datetime = timezone.datetime.strptime(f"{end_date} {end_time}", '%Y-%m-%d %H:%M')

        if action == 'add': 
            MillShift.objects.create(
                mill=admin_mill,
                shift_number=shift_number,
                shift_name=shift_name,
                start_time=start_datetime,
                end_time=end_datetime
            )
        elif action == 'edit' and shift_id: 
            shift = get_object_or_404(MillShift, id=shift_id)
            shift.shift_number = shift_number
            shift.shift_name = shift_name
            shift.start_time = start_datetime
            shift.end_time = end_datetime
            shift.save()

        return redirect('millShift')

    return render(request, 'mill_shift.html', {
        'shifts': shifts,
        'shifts_data': shifts_data,
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Mill Shift', 'url': '/mill-shift'},
        ],
        'active_menu': 'millConfig',
    })


def millShiftDelete(request):
    if request.method == "POST":
        shift_id = request.POST.get('shift_id')
        shift = get_object_or_404(MillShift, id=shift_id)
        shift.delete()
        return redirect('millShift')  


""" @login_required
@role_required(['Admin', 'Manager', 'Supervisor'])
@permission_required(['mill_config_view']) """
def millLayout(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        admin_mill = user_profile.mill

        if request.method == 'POST':
            data = json.loads(request.body)
            layout_data = data.get('layout_data')

            layout, created = MillLayout.objects.get_or_create(mill=admin_mill)

            form = MillLayoutForm(instance=layout, data={'layout_data': layout_data})

            if form.is_valid():
                form.save()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

        layout = MillLayout.objects.filter(mill=admin_mill).first()
        layout_data = layout.layout_data if layout else {}

        return render(request, 'mill_layout.html', {
            'breadcrumb': [
                {'name': 'Home', 'url': '/'},
                {'name': 'Mill Layout', 'url': '/mill-layout'},
            ],
            'active_menu': 'millLayout',
            'layout_data': json.dumps(layout_data),
        })
    
    except ObjectDoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User profile not found'}, status=404)

def millLineDetails(request):
    user_profile = UserProfile.objects.get(user=request.user)
    admin_mill = user_profile.mill
    if request.method == 'POST':
        line_name = request.POST.get('line_name')
        line_description = request.POST.get('line_description')

        mill_line = MillLine(
            name=line_name,
            description=line_description,
            layout_data={},
            mill=admin_mill
        )
        mill_line.save()

        return redirect('millLineSelectPattern', line_id=mill_line.id)
    
    return render(request, 'line_details.html', {
        'breadcrumb': [
            {'name': 'Mill Line Configuration', 'url': '/mill-line'},
        ],
        'active_menu': 'millLine',
    })


def editMillLine(request, line_id):
    mill_line = get_object_or_404(MillLine, id=line_id)
    
    if request.method == 'POST':
        line_name = request.POST.get('line_name')
        line_description = request.POST.get('line_description')

        mill_line.name = line_name
        mill_line.description = line_description
        mill_line.save()

        return redirect('millLineSelectPattern', line_id=mill_line.id)

    return render(request, 'line_details_edit.html', {
        'mill_line': mill_line,
        'breadcrumb': [
            {'name': 'Mill Line Configuration', 'url': '/mill-line'},
        ],
        'line_id':line_id,
        'active_menu': 'millLine'
    })

def millLineSelectPattern(request, line_id):
    mill_line = get_object_or_404(MillLine, id=line_id)
    
    user_profile = UserProfile.objects.get(user=request.user)
    admin_mill = user_profile.mill

    if mill_line.mill != admin_mill:
        messages.error(request, "You do not have access to this mill line.")
        return redirect('millLine')

    if request.method == 'POST':
        selected_machine_types = request.POST.getlist('machine_types')
        mill_line.machine_types.clear()
        for machine_name in selected_machine_types:
            machine, created = MachineType.objects.get_or_create(type=machine_name)
            mill_line.machine_types.add(machine)

        messages.success(request, "Machine types updated successfully.")
        return redirect('millLineSelectMachine', line_id=mill_line.id)

    # Fetch machine types specific to the user's mill
    machine_types = admin_mill.machine_types.all()

    return render(request, 'line_pattern.html', {
        'mill_line': mill_line,
        'machine_types': machine_types,
        'selected_machine_types': mill_line.machine_types.all(),  # Pass selected machine types
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Mill Report', 'url': '/mill-report'},
        ],
        'active_menu': 'millLine',
        'line_id': line_id
    })


def millLineSelectMachine(request, line_id):
    mill_line = get_object_or_404(MillLine, id=line_id)
    selected_machine_types = mill_line.machine_types.values_list('type', flat=True)
    filtered_machines = MillMachine.objects.filter(
        type__in=selected_machine_types
    ).filter(
        Q(line__isnull=True) | Q(line_id=line_id)
    )

    return render(request, 'line_select_machines.html', {
        'breadcrumb': [
            {'name': 'Mill Line Configuration', 'url': '/mill-line'},
        ],
        'machine_types': MachineType.objects.all(),
        'filtered_machines': filtered_machines,
        'active_menu': 'millLine',
        'line_id': line_id,
    })

@csrf_exempt
def save_loading_unloading_details(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        machine_ids = data.get('machine_ids', [])
        loading_detail_m = data.get('loading_detail_m')
        unloading_detail_m = data.get('unloading_detail_m')
        loading_detail_kg = data.get('loading_detail_kg')
        unloading_detail_kg = data.get('unloading_detail_kg')
        loading_time_mins = data.get('loading_time_mins')
        unloading_time_mins = data.get('unloading_time_mins')
        line_id = data.get('line_id')

        try:
            for machine_id in machine_ids:
                machine = MillMachine.objects.get(id=machine_id)
                machine.loading_details_m = loading_detail_m
                machine.unloading_details_m = unloading_detail_m
                machine.loading_details_kg = loading_detail_kg
                machine.unloading_details_kg = unloading_detail_kg
                machine.loading_time = loading_time_mins
                machine.unloading_time = unloading_time_mins
                machine.line_id = line_id 
                machine.save()

            return JsonResponse({'success': True})
        except MillMachine.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'One or more machines do not exist.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

def millLineConfigLine(request, line_id):
    mill_line = get_object_or_404(MillLine, id=line_id)
    selected_machine_types = mill_line.machine_types.values_list('type', flat=True)
    filtered_machines = MillMachine.objects.filter(
        type__in=selected_machine_types
    ).filter(line_id=line_id)
    filtered_machines_data = list(filtered_machines.values(
        'id', 'machine_name', 'type', 'num_inputs', 'num_outputs', 'image'
    ))
    layout_data = mill_line.layout_data or {} 

    context = {
        'line_id': line_id,
        'filtered_machines_data': filtered_machines_data,
        'active_menu': 'millLine',
        'breadcrumb': [
            {'name': 'Mill Line Configuration', 'url': '/mill-line'},
        ], 
        'layout_data': json.dumps(layout_data)
    }
    return render(request, 'line_config.html', context)

@csrf_exempt
def save_line_layout(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            layout_data = data.get('layout_data')
            line_id = data.get('line_id')
            mill_line = get_object_or_404(MillLine, id=line_id)
            mill_line.layout_data = layout_data
            mill_line.save()
            return JsonResponse({'success': True}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def millLine(request):
    user_profile = UserProfile.objects.get(user=request.user)
    admin_mill = user_profile.mill
    lines = MillLine.objects.filter(mill=admin_mill)
    if request.method == "POST":
        try:
            data = json.loads(request.body) 
            line_id = data.get('line_id')
            stop = data.get('stop')
            start_date = data.get('start_date')
            end_date = data.get('end_date')

            line = MillLine.objects.get(id=line_id)

            if stop:
                line.is_start = False
                line.start_date = None 
                line.end_date = None  
            else:
                line.start_date = start_date
                line.end_date = end_date
                line.is_start = True 
            
            line.save()
            return JsonResponse({'status': 'success'})
        except MillLine.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Line not found'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            line_id = data.get('line_id')
            line = MillLine.objects.get(id=line_id)
            MillMachine.objects.filter(line=line).update(line=None)
            line.delete()

            return JsonResponse({'status': 'success'})
        except MillLine.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Line not found'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
    return render(request, 'mill_line.html', {
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Mill Line Configuration', 'url': '/mill-line'},
        ],
        'active_menu': 'millLine',
        'lines': lines
    })

""" @login_required
@role_required(['Admin', 'Manager', 'Supervisor'])
@permission_required(['reports_view']) """
def millReport(request):
    return render(request, 'mill_report.html', {
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Mill Report', 'url': '/mill-report'},
        ],
        'active_menu': 'millReport'
    })

""" @login_required
@role_required(['Admin', 'Manager', 'Supervisor'])
@permission_required(['reports_view']) """
def millProcess(request):
    machines = MillMachine.objects.all()
    return render(request, 'processes.html', {
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Process Management', 'url': '/mill-report'},
        ],
        'active_menu': 'millProcesses',
        'machines' : machines
    })

def notAuth(request):
    return render(request, 'unauth.html')

def lineAdd(request):
    return render(request, 'line_add.html', {
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Mill Line Configuration', 'url': '/mill-line'},
            {'name': 'Mill Add Line', 'url': '/line-add'},
        ],
        'active_menu': 'millLine'
    })

# Base View (if needed)
def base(request):
    return render(request, 'topbar.html')

def get_machines(request):
    user_profile = UserProfile.objects.get(user=request.user)
    mill = user_profile.mill
    machines = list(MillMachine.objects.filter(mill=mill).values('id', 'machine_name', 'image', 'num_inputs', 'num_outputs'))
    return JsonResponse(machines, safe=False)