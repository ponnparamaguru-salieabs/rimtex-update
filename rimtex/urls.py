from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

urlpatterns = [
    # path('', views.base, name='home'),
    path('', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('notauth/', views.notAuth, name='notAuth'),
    path('machine-list/', views.machineList, name='machineList'),
    path('machine-add/', views.machineAdd, name='machineAdd'),
    path('machine-edit/<int:id>/', views.machineEdit, name='machineEdit'),
    path('machine-delete/<int:id>/', views.machineDelete, name='machineDelete'),
    path('user-list/', views.userList, name='userList'),
    path('user-add/', views.userAdd, name='userAdd'),
    path('user-edit/<int:user_id>/', views.userEdit, name='userEdit'),
    path('user-delete/<int:pk>/', views.userDelete, name='userDelete'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('mill-user-list/', views.millUserList, name='millUserList'),
    path('mill-user-add/', views.millUserAdd, name='millUserAdd'),
    path('mill-user-edit/<int:pk>/', views.millUserEdit, name='millUserEdit'),
    path('mill-user-delete/<int:pk>/', views.millUserDelete, name='millUserDelete'),

    path('api/machine-models/', views.get_machine_models, name='get_machine_models'),
    path('api/add-machine/', views.add_machine, name='add_machine'),
    path('api/delete-machine/<int:machine_id>/', views.delete_machine, name='delete_machine'),
    path('api/update-machine/<int:machine_id>/', views.update_machine, name='delete_machine'),


    path('mill-info/', views.millInfo, name='millInfo'),
    path('mill-setup/', views.millSetupMachine, name='millSetupMachine'),
    path('toggle-machine/', views.toggle_machine, name='toggle_machine'),

    path('mill-config/', views.millConfig, name='millConfig'),
    path('mill-shift/', views.millShift, name='millShift'),
    path('mill-shift-delete/', views.millShiftDelete, name='millShiftDelete'),
    path('mill-layout/', views.millLayout, name='millLayout'),
    path('mill-line/', views.millLine, name='millLine'),

    path('mill-line-details/', views.millLineDetails, name='millLineDetails'),
    path('mill-line-select-pattern/<int:line_id>', views.millLineSelectPattern, name='millLineSelectPattern'),
    path('mill-line-select-machine/<int:line_id>', views.millLineSelectMachine, name='millLineSelectMachine'),
    path('mill-line-config-line/<int:line_id>', views.millLineConfigLine, name='millLineConfigLine'),
    path('mill-line/edit/<int:line_id>/', views.editMillLine, name='editMillLine'),

    path('save_line_layout/', views.save_line_layout, name='save_line_layout'),
    path('save_loading_unloading_details/', views.save_loading_unloading_details, name='save_loading_unloading_details'),

    path('mill-report/', views.millReport, name='millReport'),
    path('mill-process/', views.millProcess, name='millProcess'),
    path('devices/', views.devices, name='devices'),
    path('file-upload/', views.file_upload, name='file_upload'),

    path('mill-layout/api/machine/', views.get_machines, name='get_machines'),
    path('line-add/api/machine/', views.get_machines, name='get_machines'),

    path('line-add', views.lineAdd, name='lineAdd'),
    # path('drawflow/', views.drawflow_view, name='drawflow'),
    # path('not-authorized/', views.not_authorized, name='not_authorized'),
]
