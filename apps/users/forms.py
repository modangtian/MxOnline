from captcha.fields import CaptchaField
from django import forms


#登录表单验证
from users.models import UserProfile


class LoginForm(forms.Form):
    #用户名和密码不能为空
    username = forms.CharField(required=True)
    password = forms.CharField(required=True, min_length=5)


#注册表单验证
class RegisterForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True, min_length=5)
    #验证码，字段里面可以自定义错误提示信息
    captcha = CaptchaField(error_messages={'invalid': '验证码错误'})


#找回密码
class ForgetPwdForm(forms.Form):
    email = forms.CharField(required=True)
    captcha = CaptchaField(error_messages={'invalid': '验证码错误'})
#在这又犯了一个错误，将CaptchaField写成了CharField


#修改密码
class ModifyPwdForm(forms.Form):
    password1 = forms.CharField(required=True, min_length=5)
    password2 = forms.CharField(required=True, min_length=5)


#用户更改头像
class UploadImageForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['image']


#个人中心资料修改
class UserInfoForm(forms.ModelForm):
    class Meta:
        media = UserProfile
        fields = ['nick_name', 'gender', 'birthday', 'address', 'mobile']