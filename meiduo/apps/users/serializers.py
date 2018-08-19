from rest_framework import serializers
from .models import User
from django_redis import get_redis_connection
import re


class UserCreateSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(
        min_length=5,
        max_length=20,
        error_messages={
            'mix_length':'用户名不少于5个字符',
            'max_length':'用户名不多于20个字符'
        }
    )
    mobile = serializers.CharField()

    password = serializers.CharField(write_only=True,
                                     min_length=8,
                                     max_length=20,
                                     error_messages={
                                         'min_length':'密码长度不少于8个字符',
                                         'max_length':'密码长度不多于20个字符'
                                     })
    # accuracy password
    password2 = serializers.CharField(write_only=True,
                                     min_length=8,
                                     max_length=20,
                                     error_messages={
                                         'min_length': '密码长度不少于8个字符',
                                         'max_length': '密码长度不多于20个字符'
                                     })

    # agreement
    allow = serializers.CharField(write_only=True)
    # massage vaildate
    sms_code = serializers.CharField(write_only=True)

    def validate_username(self, value):
        # verify whether the username is registered by others
        count = User.objects.filter(username=value).count()
        if count>0:
            raise serializers.ValidationError('用户名已存在')
        return value

    def validate_mobile(self,value):
        # if the mobile format is wrong
        if not re.match(r'^1[3-9]\d{9}$',value):
            raise serializers.ValidationError('手机号有误')
        # verify whether the mobile has been used
        count = User.objects.filter(mobile=value).count()
        if count>0:
            raise serializers.ValidationError('该手机号已被注册')
        return value

    def validate_sms_code(self,value):
        if not re.match(r'^\d{6}$',value):
            raise serializers.ValidationError('验证码格式错误')
        return value

    def validat_allow(self,value):
        if not value:
            raise serializers.ValidationError('请同意协议')
        return value

    def validate(self, attrs):
        # verify more than two attributes

        # if password is equal to password2
        password = attrs.get('password')
        password2 = attrs.get('password2')
        if password != password2:
            print(password,password2)
            raise serializers.ValidationError('两次密码输入不一致')

        # verify sms_code
        redis_cli = get_redis_connection('verify_code')
        key = 'sms_code_' + attrs.get('mobile')
        sms_code_redis = redis_cli.get(key)
        sms_code_user = attrs.get('sms_code')
        if not sms_code_redis:
            print('无验证码')
            raise serializers.ValidationError('验证码已过期')
        # force the sms_code out of date
        redis_cli.delete(key)
        if sms_code_user != sms_code_redis.decode():
            print('验证码错误')
            raise serializers.ValidationError('验证码错误')
        return attrs

    def create(self, validated_data):
        user = User()
        user.username = validated_data.get('username')
        user.mobile = validated_data.get('mobile')
        user.set_password(validated_data.get('password'))
        user.save()

        return user