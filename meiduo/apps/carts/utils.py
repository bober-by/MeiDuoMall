from utils import turnover
from django_redis import get_redis_connection

def merge_cart_cookie_to_redis(request,response,user_id):
    '''
    登录后将cookie中的数据保存至redis中
    :param request:
    :param response:
    :param user:
    :return:
    '''
    # 从cookie中获取cart
    cookie_cart = request.COOKIES.get('cart')
    if not cookie_cart:
        return response

    cart_dict = turnover.loads(cookie_cart)

    # 写入redis
    redis_cli = get_redis_connection('cart')
    for sku_id,item in cart_dict.items():
        # 将数量保存到hash中
        redis_cli.hset('cart%d'%user_id,sku_id,item.get('count'))
        # 将选中状态保存在set中,选中则添加，未选中则删除
        if item.get('selected'):
            redis_cli.sadd('cart_selected%d'%user_id,sku_id)
        else:
            redis_cli.srem('cart_selected%d'%user_id,sku_id)

    # 删除cookie
    response.delete_cookie('cart')

    return response





