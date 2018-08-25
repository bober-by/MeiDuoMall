from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from rest_framework.generics import CreateAPIView
from .serializers import UserCreateSerializer
from .serializers import UserDetailSerializer
from .serializers import EmailSerializer,UserAddressSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import RetrieveAPIView,UpdateAPIView
from rest_framework import status
from rest_framework.mixins import CreateModelMixin,UpdateModelMixin
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from . import serializers
from . import constants

class UsernameCountView(APIView):

    def get(self,request,username):
        # verify whether the username is exist or not
        count = User.objects.filter(username=username).count()

        return Response({
            'username':username,
            'count':count
        })

class MobileCountView(APIView):
    def get(self,request,mobile):
        # verify whether the mobile is exist or not
        count = User.objects.filter(mobile=mobile).count()

        return Response({
            'mobile':mobile,
            'count':count
        })

class UserView(CreateAPIView):

    serializer_class = UserCreateSerializer


class UserDetailView(RetrieveAPIView):
    # verify if user has been logined
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetailSerializer

    # rewrite the 'get_object' function to make the client unable to access by pk
    # we can get user from JWT's payload,and it has been analysised into request
    def get_object(self):
        return self.request.user

class EmailView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmailSerializer

    def get_object(self, *args, **kwargs):
        return self.request.user

class VerifyEmailView(APIView):
    def get(self,request):
        # get token
        token = request.query_params.get('token')
        if not token:
            return Response({'message': '缺少token'}, status=status.HTTP_400_BAD_REQUEST)

        # verify token
        user = User.check_verify_email_token(token)
        if user is None:
            return Response({'message': '链接信息无效'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            user.email_active = True
            user.save()

            return Response({'message': 'OK'})

    pass

class AddressViewSet(CreateModelMixin, UpdateModelMixin, GenericViewSet):
    """
    用户地址新增与修改
    """
    serializer_class = serializers.UserAddressSerializer
    permissions = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    # GET /addresses/
    def list(self, request, *args, **kwargs):
        """
        用户地址列表数据
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data,
        })

    # POST /addresses/
    def create(self, request, *args, **kwargs):
        """
        保存用户地址数据
        """
        # 检查用户地址数据数目不能超过上限
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '保存地址数据已达到上限'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    # delete /addresses/<pk>/
    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    # put /addresses/pk/status/
    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    # put /addresses/pk/title/
    # 需要请求体参数 title
    @action(methods=['put'], detail=True)
    def title(self, request, pk=None):
        """
        修改标题
        """
        address = self.get_object()
        '''更新，instance为要更新的对象实例'''
        serializer = serializers.AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)