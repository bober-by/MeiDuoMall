from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from django_redis import get_redis_connection
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from carts.serializers import CartSKUSerializer
from .serializers import SaveOrderSerializer
from goods.models import SKU

class OrderSettlementView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self,request):
        # 查询redis中选中的商品
        redis_cli = get_redis_connection('cart')
        # 获取商品的编号与数量{b'1': b'1', b'15': b'1'}
        cart_dict = redis_cli.hgetall('cart%d'%request.user.id)
        # 转换为int
        cart_dict2 = {int(k):int(v) for k,v in cart_dict.items()}

        # 获取选中的商品
        cart_selected = redis_cli.smembers('cart_selected%d'%request.user.id)

        # 查询商品对象
        skus = SKU.objects.filter(pk__in=cart_selected)
        for sku in skus:
            sku.count = cart_dict2.get(sku.id)
            sku.selected = True

        serializer = CartSKUSerializer(skus,many=True)

        result = {
            'freight':10,
            'skus':serializer.data
        }

        return Response(result)


class OrderSaveView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SaveOrderSerializer
