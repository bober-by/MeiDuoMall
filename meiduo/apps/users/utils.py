from django.contrib.auth.backends import ModelBackend
import re
from .models import User

def jwt_response_payload_handler(token,user=None,request=None):
    '''
    self-defining the data returned
    :param token:
    :param user:
    :param request:
    :return:
    '''
    return {
        'token':token,
        'user_id':user.id,
        'username':user.username
    }

# seld-defining a class to re-write the function ---> authenticate()
class UsernameMobileModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # if client logining by mobile number
            user = User.objects.get(mobile=username)
        except:
            # if client logining by username
            try:
                user = User.objects.get(username=username)
            except:
                return None

        # if it find the user,then checkout the password
        if user.check_password(password):
            return user
        else:
            return None