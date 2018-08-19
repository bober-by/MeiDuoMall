from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from rest_framework.generics import CreateAPIView
from .serializers import UserCreateSerializer

class UsernameCountView(APIView):

    def get(self,request,username):
        # 检查用户名是否存在
        count = User.objects.filter(username=username).count()

        return Response({
            'username':username,
            'count':count
        })

class MobileCountView(APIView):
    def get(self,request,mobile):
        # 检查电话是否存在
        count = User.objects.filter(mobile=mobile).count()

        return Response({
            'mobile':mobile,
            'count':count
        })

class UserView(CreateAPIView):
    print('haha')

    serializer_class = UserCreateSerializer