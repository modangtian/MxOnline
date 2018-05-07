import re
from django import forms
from operation.models import UserAsk


class UserAskForm(forms.ModelForm):
    class Meta:
        model =UserAsk
        fields = ['name', 'mobile', 'course_name']

    def clean_mobile(self):  # 函数必须以clean_开头
        """
        通过正则表达式验证手机号码是否合法
        """
        mobile = self.cleaned_data['mobile']
        mobile_regex = r'^1[34578]\d{9}$'
        p = re.compile(mobile_regex)
        if p.match(mobile):
            return mobile
        else:
            raise forms.ValidationError('手机号码非法', code='invalid mobile')