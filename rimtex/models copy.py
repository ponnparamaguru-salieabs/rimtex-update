from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20)
    permissions = models.JSONField(default=dict)  

    def get_permission(self, perm):
        return self.permissions.get(perm, False)

    def __str__(self):
        return self.user.username

class Machine(models.Model):
    TYPE_CHOICES = [
        ('Carding', 'Carding Machine'),
        ('Breaker', 'Breaker Machine'),
        ('Unilap', 'Unilap Machine'),
        ('Comber', 'Comber Machine'),
        ('Finisher', 'Finisher Machine'),
        ('Roving', 'Roving Machine'),
    ]

    type = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    make_year = models.IntegerField()
    design = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100)
    num_inputs = models.IntegerField()
    num_outputs = models.IntegerField()
    image = models.ImageField(upload_to='machine_images/', blank=True, null=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.model}"
    
class MachineType(models.Model):
    MACHINE_TYPES = [
        ('Carding', 'Carding'),
        ('Breaker', 'Breaker'),
        ('Unilap', 'Unilap'),
        ('Comber', 'Comber'),
        ('Finisher', 'Finisher'),
        ('Roving', 'Roving'),
    ]

    type = models.CharField(max_length=10, choices=MACHINE_TYPES, unique=True)

    def __str__(self):
        return self.type

class MillLine(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True)
    start_date = models.DateTimeField(null=True)  
    end_date = models.DateTimeField(null=True)
    layout_data = models.JSONField(null=True, blank=True)
    machine_types = models.ManyToManyField(MachineType, blank=True)
    is_start = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class MillMachine(models.Model):
    TYPE_CHOICES = [
        ('Carding', 'Carding Machine'),
        ('Breaker', 'Breaker Machine'),
        ('Unilap', 'Unilap Machine'),
        ('Comber', 'Comber Machine'),
        ('Finisher', 'Finisher Machine'),
        ('Roving', 'Roving Machine'),
    ]

    type = models.CharField(max_length=100, choices=TYPE_CHOICES)
    code = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    make_year = models.IntegerField()
    design = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100, null=True)
    num_inputs = models.IntegerField()
    num_outputs = models.IntegerField()
    image = models.ImageField(upload_to='machine_images/', blank=True, null=True)
    machine_name = models.CharField(max_length=100)

    line = models.ForeignKey(MillLine, on_delete=models.SET_NULL, null=True, blank=True, default=None)  
    is_assigned = models.BooleanField(default=False) 

    loading_time = models.IntegerField(null=True)  
    unloading_time = models.IntegerField(null=True)  
    loading_details_m = models.DecimalField(max_digits=10, decimal_places=2, null=True)  
    unloading_details_m = models.DecimalField(max_digits=10, decimal_places=2, null=True)  
    loading_details_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True)  
    unloading_details_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True) 

    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.machine_name} ({self.type})"


class MillInfo(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    unit_number = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)

    def __str__(self):
        return self.name if self.name else "Mill"

class MillShift(models.Model):
    shift_number = models.CharField(max_length=10)
    shift_name = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return f"{self.shift_name} ({self.shift_number})"
    
class MillLayout(models.Model):
    layout_data = models.JSONField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

class SetupMachine(models.Model):
    name = models.CharField(max_length=100)
    is_add = models.BooleanField(default=False)

    def __str__(self):
        return self.name