from django_redis import get_redis_connection
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from celery_tasks.sms.tasks import sms_send


import random

# 验证码
class SMSCodeView(APIView):
    def get(self,request,mobile):
        '''
        接收手机号，发送短信验证码
        :param mobile: 手机号
        :return: 是否成功
        '''
        # 获取redis的连接
        redis_cli = get_redis_connection('verify_code')
        # 检查60s之内是否有获取验证操作
        sms_flag = redis_cli.get('sms_flag_'+mobile)
        if sms_flag:
            raise serializers.ValidationError('请稍后再重新获取验证码')
        # 生成短信验证码
        sms_code = str(random.randint(100000,999999))
        # 保存短信验证码与验证记录
        # 保存验证码，设置有效期为300s
        # redis_cli.setex('sms_code_'+mobile,300,sms_code)
        # # 保存发送标记，有效时间为60s
        # redis_cli.setex('sms_flag_'+mobile,60,1)

        # 使用管道，减少与redis服务器的通信次数
        redis_pl = redis_cli.pipeline()
        redis_pl.setex('sms_code_'+mobile,300,sms_code)
        redis_pl.setex('sms_flag_'+mobile,60,1)
        redis_pl.execute()

        # 使用云通讯发送验证码,单位为分钟
        # CCP.sendTemplateSMS(mobile,sms_code,5,1)
        sms_send.delay(mobile,sms_code,5,1)

        print(sms_code)

        return Response({'message':'OK'})

