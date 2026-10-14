from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOrUsernameBackend(ModelBackend):
    """登录标识符同时支持邮箱与用户名。

    USERNAME_FIELD 被设为 email，SimpleJWT 会以 email=<标识符> 调用 authenticate，
    因此这里把 email / username 两个参数都当作登录标识符：
    普通用户用邮箱登录；管理员沿用原来的用户名登录。
    """

    def authenticate(self, request, email=None, username=None, password=None, **kwargs):
        identifier = (email or username or "").strip()
        if not identifier or password is None:
            return None

        User = get_user_model()
        user = User.objects.filter(email__iexact=identifier).first()
        if user is None:
            user = User.objects.filter(username__iexact=identifier).first()
        if user is None:
            # 与 ModelBackend 行为一致，空跑一次哈希以弱化时序差异
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
