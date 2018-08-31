from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_jwt.settings import api_settings

from .models import OAuthQQUser
from .exceptions import QQAPIError
from .utils import OAuthQQ
from .serializers import OAuthQQUserSerializer

from carts.utils import merge_cart_cookie_to_redis


class QQAuthURLView(APIView):
    """
    获取QQ登录的url
    """

    def get(self, request):
        """
        提供用于qq登录的url
        """
        #获取来源地址，登录成功后会转向这个地址
        next = request.query_params.get('next')
        #创建QQ登录对象
        oauth = OAuthQQ(state=next)
        #获取授权地址，包含了应用的appid
        login_url = oauth.get_qq_login_url()
        #向客户端返回授权地址
        return Response({'login_url': login_url})


class QQAuthUserView(APIView):
    """
    QQ登录的用户
    """
    def get(self, request):
        """
        获取qq登录的用户数据
        """
        code = request.query_params.get('code')
        if not code:
            return Response({'message': '缺少code'}, status=status.HTTP_400_BAD_REQUEST)

        oauth = OAuthQQ()

        # 获取用户openid
        try:
            access_token = oauth.get_access_token(code)
            openid = oauth.get_openid(access_token)
        except QQAPIError:
            return Response({'message': 'QQ服务异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 判断用户是否存在
        try:
            qq_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 用户第一次使用QQ登录
            token = oauth.generate_save_user_token(openid)
            return Response({'access_token': token})
        else:
            # 找到用户, 生成token
            user = qq_user.user
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)

            response = Response({
                'token': token,
                'user_id': user.id,
                'username': user.username
            })

            # 登录成功，合并购物车
            response = merge_cart_cookie_to_redis(request,response,user.id)

            return response

    def post(self, request):
        serializer = OAuthQQUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        response = Response({
            'token': user.token,
            'user_id': user.id,
            'username': user.username
        })

        # 登录成功，合并购物车
        response = merge_cart_cookie_to_redis(request, response, user.id)

        return response