from rest_framework import serializers
from goods.models import SKU

class CartSerializer(serializers.Serializer):
    sku_id = serializers.IntegerField(min_value=1)
    count = serializers.IntegerField(min_value=1)
    selected = serializers.BooleanField(default=True)

    def validate_sku_id(self,value):
        try:
            sku = SKU.objects.get(pk=value)
        except:
            raise serializers.ValidationError('商品编号不存在')
        return value

class CartSKUSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField()
    selected = serializers.BooleanField()

    class Meta:
        model = SKU
        fields = ['id','count','name','default_image_url','price','selected']


class CartDeleteSerializer(serializers.Serializer):
    sku_id = serializers.IntegerField(min_value=1)

    def validate_sku_id(self,value):
        try:
            sku = SKU.objects.get(pk=value)
        except:
            raise serializers.ValidationError('商品不存在')

        return value


class CartAllSerializer(serializers.Serializer):
    selected = serializers.BooleanField()