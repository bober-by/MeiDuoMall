from .serializers import CartSerializer,CartSKUSerializer,CartDeleteSerializer,CartAllSerializer
from rest_framework.views import APIView
from utils import turnover
from rest_framework.response import Response
from rest_framework import status,serializers
from . import constants
from goods.models import SKU
from django_redis import get_redis_connection

class CartView(APIView):
    def perform_authentication(self, request):
        # 跳过dispatch之前的登录验证
        pass

    '''
    添加购物车
    '''
    def post(self,request):
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        try:
            user = request.user
        except:
            user = None

        response = Response(serializer.validated_data)

        # 如果用户未登录
        if user is None:
            cart = request.COOKIES.get('cart')
            # cookie中是否已经存在cart,存在则修改，不存在则添加
            if cart:
                cart_dict = turnover.loads(cart)
            else:
                cart_dict = {}

            # 判断购物车中是否有此商品
            if sku_id in cart_dict:
                count_cart = cart_dict.get(sku_id).get('count')
                cart_dict[sku_id][count] = count_cart + count
            else:
                cart_dict[sku_id] = {
                    'count':count,
                    'selected':True
                }
            cart_str = turnover.dumps(cart_dict)
            # 存到cookie中
            response.set_cookie('cart',cart_str,max_age=constants.CART_COOKIE_EXPIRES)
        else:
            # 向redis中存储数据
            redis_cli = get_redis_connection('cart')
            redis_cli.hincreby('cart%d'%user.id,sku_id,count)

        return response

    def get(self,request):
        try:
            user = request.user
        except:
            user = None

        if user is None:
            cart = request.COOKIES.get('cart')

            if cart:
                cart_dict = turnover.loads(cart)
            else:
                cart_dict = {}
        else:
            redis_cli = get_redis_connection('cart')
            cart_redis = redis_cli.hgetall('cart%d' % user.id)
            cart_dict = {}
            '''
            {sku_id:count}===>
            {
                sku_id:{
                    count:***
                }
            }
            '''
            for sku_id in cart_redis:
                cart_dict[int(sku_id)] = {
                    'count':int(cart_redis[sku_id])
                }
            cart_select = redis_cli.smembers('cart_selected%d'%user.id)
            cart_select = [int(sku_id) for sku_id in cart_select]
            for sku_id in cart_dict:
                if sku_id in cart_select:
                    cart_dict[sku_id]['selected'] = True
                else:
                    cart_dict[sku_id]['selected'] = False

        skus = SKU.objects.filter(id__in=cart_dict.keys())
        # 为商品添加count和selected属性
        for sku in skus:
            sku_dict = cart_dict.get(sku.id)
            sku.count = sku_dict.get('count')
            sku.selected = sku_dict.get('selected')

        serializer = CartSKUSerializer(skus,many=True)
        return Response(serializer.data)

    def put(self,request):
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        response = Response(serializer.validated_data)

        try:
            user = request.user
        except:
            user = None

        if user is None:
            cart = request.COOKIES.get('cart')
            if cart is not None:
                cart_dict = turnover.loads(cart)
            else:
                raise serializers.ValidationError('购物车为空')
            if sku_id in cart_dict:
                cart_dict[sku_id] = {
                    'count':count,
                    'selected':selected
                }
            cart_str = turnover.dumps(cart_dict)
            response.set_cookie('cart',cart_str,max_age=constants.CART_COOKIE_EXPIRES)

        else:
            redis_cli = get_redis_connection('cart')
            redis_cli.hset('cart%d' % user.id, sku_id, count)
            if selected:
                redis_cli.sadd('cart_selecte%d' % user.id, sku_id)
            else:
                redis_cli.srem('cart_selected%d' % user.id, sku_id)

        return response

    def delete(self,request):
        serializer = CartDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')

        try:
            user = request.user
        except:
            user =None

        response = Response(status=status.HTTP_204_NO_CONTENT)

        if user is None:
            cart = request.COOKIES.get('cart')
            if not cart:
                raise serializers.ValidationError('购物车无数据，不需要删除')
            cart_dict = turnover.loads(cart)
            if sku_id in cart_dict:
                del cart_dict[sku_id]

            cart_str = turnover.dumps(cart_dict)
            response.set_cookie('cart', cart_str, max_age=constants.CART_COOKIE_EXPIRES)

        else:
            redis_cli = get_redis_connection('cart')
            redis_cli.hdel('cart_selecte%d' % user.id, sku_id)

        return response

class CartAllView(APIView):
    def perform_authentication(self, request):
        # 跳过dispatch之前的登录验证
        pass

    def put(self,request):
        serializer = CartAllSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selected = serializer.validated_data.get('selected')

        try:
            user = request.user
        except:
            user = None

        response = Response({'message': 'OK'})
        if user is None:
            cart = request.COOKIES.get('cart')
            if not cart:
                raise serializers.ValidationError('暂无购物车数据')
            cart_dict = turnover.loads(cart)
            for sku_id in cart_dict:
                cart_dict[sku_id]['selected'] = selected
            cart_str = turnover.dumps(cart_dict)
            response.set_cookie('cart', cart_str, max_age=constants.CART_COOKIE_EXPIRES)

        else:
            pass

        return response