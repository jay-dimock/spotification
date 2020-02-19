from django.db import models
from datetime import datetime, date
import re
import bcrypt
from dateutil.relativedelta import relativedelta #helps with counting years between dates. pip install python-dateutil

class UserManager(models.Manager):
    def email_message(self, postData):
        if not postData['email']:
            return "Email is required"
        else:
            EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
            if not EMAIL_REGEX.match(postData['email']):
                return 'Email format is not valid'
        return ''

    def basic_password_message(self, postData):
        if not postData['password']:
            return "Password is required"
        if len(postData['password'].strip()) < 8:
            return 'Password must be at least 8 characters'
        return ''

    def password_match_message(self, postData):
        p = self.basic_password_message(postData)
        if p: return p
        
        if postData['password'].strip() != postData['confirm-password'].strip():
            return 'Passwords do not match'      

    def name_validator(self, postData):
        errors = {}
        if len(postData['first-name'].strip()) < 2:
            errors['first-name'] = 'First Name must be at least 2 characters'
        if len(postData['last-name'].strip()) < 2:
            errors['last-name'] = 'Last Name must be at least 2 characters'
        return errors

    def edit_user_validator(self, postData, user_id):
        errors = self.name_validator(postData)
        e = self.email_message(postData)
        if e: 
            errors['email'] = e
            return errors

        users = User.objects.exclude(id=user_id).filter(email=postData['email'].strip())
        if len(users) > 0:
            errors['email'] = "This email is already registered"
        return errors

    def registration_validator(self, postData):
        errors = self.name_validator(postData)

        p = password_match_message(postData)
        if p: errors['password'] = p
        e = self.email_message(postData)
        if e: errors['email'] = e

        if not e:
            users = User.objects.filter(email=postData['email'].strip())
            if len(users) > 0:
                errors['email'] = "This email is already registered"

        if not postData['birthday']:
            errors['birthday'] = 'Birthday must not be blank'
        else:
            try:
                birthday = datetime.strptime(postData['birthday'], '%Y-%m-%d').date()
                age = relativedelta (date.today(), birthday).years
                if age < 13:
                    errors['birthday'] = 'You must be at least 13 years old to register'
            except:
                errors['birthday'] = "Birthday is not a valid date"

        return errors


    def login_validator(self, postData):
        errors = {}

        e = self.email_message(postData)
        if e: errors['email'] = e
        p = self.basic_password_message(postData)
        if p: errors['password'] = p
        
        if not e:
            users = User.objects.filter(email=postData['email'].strip())
            if users.count() == 0:
                errors['email'] = "This email address is not yet registered"
            else:
                encodedpw = postData['password'].strip().encode()
                pwmatch = bcrypt.checkpw(encodedpw, users[0].password.encode())
                if not pwmatch:
                    errors['password'] = 'Password is incorrect'
        return errors


class User(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=75)
    spotify_id = models.IntegerField(default=0)
    token = models.CharField(max_length=255, null=True)
    refresh_token = models.CharField(max_length=255, null=True)
    birthday = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = UserManager()

    def full_name(self):
        return self.first_name + " " + self.last_name