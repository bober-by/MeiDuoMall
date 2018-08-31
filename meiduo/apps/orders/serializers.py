from .models import OrderInfo,OrderGoods
from rest_framework import serializers
from django_redis import get_redis_connection
from datetime import datetime
from goods.models import SKU
from django.db import transaction

class SaveOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInfo
        fields = ['order_id','address','pay_method']
        read_only_fields = ['order_id']
        # 对现有字段进行验证
        extra_kwargs = {
            'address':{
                # 只写，表示只用于输入
                'write_only':True,
                # 要求必须传入
                'required':True
            },
            'pay_method':{
                # 只写，表示只用于输入
                'write_only': True,
                # 要求必须传入
                'required': True
            }
        }

    def create(self, validated_data):
        user = self.context['request'].user
        with transaction.atomic():
            # 开启事务
            sid = transaction.savepoint()
            # 1.创建OrderInfo对象
            order = OrderInfo()
            order.order_id = datetime.now().strftime('%y%m%d%H%M%S') + '%09d'%user.id
            order.user = user
            order.address = validated_data.get('address')
            order.total_count = 0
            order.total_amount = 0
            order.freight = 10
            order.pay_method = validated_data.get('pay_method')
            if validated_data.get('pay_method') == 1:
                # 货到付款
                order.status = 2
            else:
                # Alipay
                order.status = 1

            order.save()

            # 2.查询redis中所有选中的商品
            redis_cli = get_redis_connection('cart')
            # 获取商品编号及数量
            cart_hash = redis_cli.hgetall('cart%d'%user.id)
            cart_dict = {int(k):int(v) for k,v in cart_hash.items()}
            # 查询选中的商品
            cart_set = redis_cli.smembers('cart_selected%d'%user.id)
            cart_selected = [int(sku_id) for sku_id in cart_set]

            # 3.遍历
            skus = SKU.objects.filter(id__in=cart_selected)
            total_amount = 0
            total_count = 0
            for sku in skus:
                # 3.1判断库存是否足够,库存不够则抛异常
                # 获取购买数量
                count = cart_dict.get(user.id)
                if count > sku.stock:
                    # 回滚
                    transaction.savepoint_rollback(sid)
                    raise serializers.ValidationError('库存不足')

                # 3.2修改商品的库存、销量
                sku.stock-=count
                sku.sales+=count
                sku.save()

                # 3.3修改SPU的总销量
                # 获取当前商品对应的spu
                goods = sku.goods
                goods.sales += count
                goods.save()

                # 3.4创建OrderGoods对象
                order_goods = OrderGoods()
                order_goods.order = order
                order_goods.count = count
                order_goods.sku = sku
                order_goods.price = sku.price
                order_goods.save()

                # 3.5计算总金额、总数量
                total_count += count
                total_amount += count * sku.price

            # 4.修改总金额、总数量
            order.total_amount = total_amount
            order.total_count = total_count
            order.save()
            # 提交事务
            transaction.savepoint_commit(sid)

        # 5.删除redis中选中的商品数据
        pl = redis_cli.pipeline()
        pl.hdel('cart%d'%user.id,*cart_selected)
        pl.srem('cart_slelcted%d'%user.id,*cart_selected)
        pl.execute()

        return order

