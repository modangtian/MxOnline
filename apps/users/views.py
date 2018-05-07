from django.contrib.auth.hashers import make_password
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.backends import ModelBackend
from django.urls import reverse

from course.models import Course
from operation.models import UserCourse, UserFavorite, UserMessage
from organization.models import CourseOrg, Teacher
from utils.mixin_utils import LoginRequiredMixin
from .models import UserProfile, EmailVerifyRecord, Banner
from django.db.models import Q
from django.views.generic.base import View
from .forms import LoginForm, RegisterForm, ForgetPwdForm, ModifyPwdForm, UploadImageForm, UserInfoForm
from utils.email_send import send_register_email
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger


'''让用户可以通过邮箱或者用户名都可以登录，用自定义authenticate方法
这里是继承（ModelBackend后台）类来做的验证'''


#邮箱和用户名都可以登录
# 基础ModelBackend类，因为它有authenticate方法
class CustomBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # 不希望用户存在两个，get只能有一个。两个是get失败的一种原因 Q为使用并集查询
            user = UserProfile.objects.get(Q(username=username) | Q(email=username))

            # django的后台中密码加密：所以不能password==password
            # UserProfile继承的AbstractUser中有def check_password(self, raw_password):
            if user.check_password(password):
                return user
        except Exception as e:
            return None


#首页
class IndexView(View):
    def get(self, request):
        #轮播图
        all_banners = Banner.objects.all().order_by('index')
        #课程
        courses = Course.objects.filter(is_banner=False)[:6]#前端的class属性不一样
        #轮播课程
        banner_courses = Course.objects.filter(is_banner=True)[:3]#前端的class属性不一样
        #课程机构
        course_orgs = CourseOrg.objects.all()[:15]
        return render(request, 'index.html', {
            'all_banners': all_banners,
            'courses': courses,
            'banner_courses': banner_courses,
            'course_orgs': course_orgs,
        })




class LoginView(View):
    def get(self, request):
        return render(request, 'user/login.html')

    def post(self,request):
        #实例化
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user_name = request.POST.get('username', None)
            pass_word = request.POST.get('password', None)
            # 成功返回user对象,失败None
            user = authenticate(username=user_name, password=pass_word)
            # 如果不是null说明验证成功
            if user is not None:
                if user.is_active:
                    # 只有注册激活才能登录
                    login(request, user)
                    return render(request, 'index.html')
                else:
                    return render(request, 'user/login.html', {'msg': '用户名或密码错误','login_form': login_form})
            # 只有当用户名或密码不存在时，才返回错误信息到前端
            else:
                return render(request, 'user/login.html', {'msg': '用户名或密码错误', 'login_form': login_form})


        # form.is_valid（）已经判断不合法了，所以这里不需要再返回错误信息到前端了
        else:
            return render(request, 'user/login.html', {'login_form': login_form})

'''
def user_login(request):
    if request.method == 'POST':
        #获取用户名和密码
        user_name = request.POST.get('username', None)
        pass_word = request.POST.get('password', None)
        #成功返回user，失败None
        user = authenticate(username=user_name, password=pass_word)
        #如果不是null说明验证成功
        if user is not None:
            #登录
            login(request, user)
            return render(request, 'index.html')
        else:
            return render(request, 'login.html', {'msg': '用户名或密码错误'})

    elif request.method == 'GET':
        return render(request, 'login.html')
'''


#用户退出
class LogoutView(View):
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(reverse('index'))  #重定向


#用户注册
class RegisterView(View):
    def get(self, request): #如果是get请求，直接返回注册页面给用户
        register_form = RegisterForm()
        return render(request, 'user/register.html', {'register_form':register_form})

    def post(self, request):#如果是post请求，先生成一个表单实例，并获取用户提交的所有信息（request.POST）
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():#is_valid 判断用户提交的数据是否合法
            user_name = request.POST.get('email', None)
            #如果用户已存在，则提示错误信息
            if UserProfile.objects.filter(email= user_name):
                return render(request, 'user/register.html', {'register_form':register_form,'msg':'用户已存在'})
            pass_word = request.POST.get('password', None)
            #实例化一个user_profile对象
            user_profile = UserProfile()#实例化一个user_profile对象，把用户添加到数据库
            user_profile.username = user_name
            user_profile.email = user_name
            user_profile.is_active = False#默认添加用户的激活状态（is_active=1表示True），在这里我们修改默认的状态（改为is_active = False），只有用户去邮箱激活之后才改为True
            #对保存到数据库密码进行加密
            user_profile.password = make_password(pass_word)
            user_profile.save()#对密码加密，然后保存，发送邮箱，username是用户注册的邮箱，‘register’表明是注册
            send_register_email(user_name, 'register')
            return render(request, 'user/login.html')
        else:
            return render(request, 'user/register.html', {'register_form':register_form})


#激活用户
class ActiveUserView(View):
    def get(self, request, active_code):
        #查询邮箱验证记录是否存在
        all_record = EmailVerifyRecord.objects.filter(code=active_code)
        if all_record:
            for record in all_record:
                #获取到对应的邮箱
                email = record.email
                #查找到有相对应的user
                user = UserProfile.objects.filter(email=email)
                user.is_active = True
                user.save()
                # 激活成功后跳转到登陆页面
                return render(request, 'user/login.html')
        # 验证码不对的时候跳转到激活失败页面
        else:
            return render(request, 'user/active_fail.html', {'msg': '您的激活链接无效'})


#找回密码
class ForgetView(View):
    def get(self,request):
        forget_form = ForgetPwdForm()
        return render(request, 'user/forgetpwd.html', {'forget_form': forget_form})

    def post(self,request):
        forget_form = ForgetPwdForm(request.POST)
        if forget_form.is_valid():
            email = request.POST.get('email', None)
            send_register_email(email, 'forget')
            return render(request, 'user/send_success.html')

        else:
            return render(request, 'user/forgetpwd.html', {'forget_form': forget_form})


#重置密码(get方式)后台逻辑
class ResetView(View):
    def get(self, request, active_code):
        all_record = EmailVerifyRecord.objects.filter(code=active_code)
        if all_record:
            for recode in all_record:
                email = recode.email
                return render(request, 'user/password_reset.html', {'email': email})

        else:
            return render(request, 'user/active_fail.html')
        return render(request, 'user/login.html')


class ModifyPwdView(View):
    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        if modify_form.is_valid():
            pwd1 = request.POST.get('password1', '')
            pwd2 = request.POST.get('password2', '')
            email = request.POST.get('email', '')
            if pwd1 != pwd2:
                return render(request, 'user/password_reset.html', {'email': email, 'msg': '密码输入不一致'})

            user = UserProfile.objects.get(email=email)
            user.password = make_password(pwd2)
            user.save()

            return render(request, 'user/login.html')
        else:
            email = request.POST.get('email', '')
            return render(request, 'user/password_reset.html', {'email': email, 'modify_form': modify_form})


#用户个人信息
class UserinfoView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'user_center/usercenter-info.html', {

        })


#用户更改头像
class UploadImageView(LoginRequiredMixin, View):
    def post(self, request):
        # 上传的文件都在request.FILES里面获取，所以这里要多传一个这个参数
        image_form = UploadImageForm(request.POST, request.FILES)
        if image_form.is_valid():
            image = image_form.cleaned_data['image']
            request.user.image = image
            request.user.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse('{"status":"fail"}', content_type='application/json')


#在个人中心修改密码
class UpdatePwdView(View):
    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        if modify_form.is_valid():
            pwd1 = request.POST.get('password1', '')
            pwd2 = request.POST.get('password2', '')
            if pwd1 != pwd2:
                return HttpResponse('{"status":"fail", "msg":"密码不一致"}', content_type='application/json')
            user = request.user
            user.password = make_password(pwd2)
            user.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse(json.dumps(modify_form.errors), content_type='application/json')


#发送邮箱修改验证码
class SendEmailCodeView(LoginRequiredMixin, View):
    def get(self, request):
        email = request.GET.get('email', '')
        if UserProfile.objects.filter(email='email'):
            return HttpResponse('{"email": "邮箱已存在"}', content_type='application/json')
        send_register_email(email, 'update_email')
        return HttpResponse('{"status":"success"}', content_type='application/json')


#修改邮箱
class UpdateEmailView(LoginRequiredMixin, View):
    def post(self, request):
        email = request.POST.get('email', '')
        code = request.POST.get('code', '')
        existed_records = EmailVerifyRecord(email=email, code=code, send_type='update_email')
        if existed_records:
            user = request.user
            user.email = email
            user.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse('{"email":"验证码无效}', content_type='application/json')


#用户个人信息
class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'user_center/usercenter-info.html')

    def post(self, request):
        user_info_form = UserInfoForm(request.POST, instance=request.user)
        if user_info_form.is_valid():
            user_info_form.save()
            return HttpResponse('{"status": "success"}', content_type='application/json')
        else:
            return HttpResponse(json.dumps(user_info_form.errors), content_type='application/json')


#我的课程
class MyCourseView(LoginRequiredMixin,View):
    def get(self, request):
        user_courses = UserCourse.objects.filter(user=request.user)
        return render(request, 'course/usercenter-mycourse.html', {
            'user_courses': user_courses,
        })


#我收藏的课程机构
class MyFavOrgView(LoginRequiredMixin, View):
    def get(self, request):
        org_list = []
        fav_orgs = UserFavorite.objects.filter(user=request.user, fav_type=2)
        #通过fav_orgs的id找到机构对象
        for fav_org in fav_orgs:
            org_id = fav_org.fav_id
            #获取机构
            org = CourseOrg.objects.get(id=org_id)
            org_list.append(org)
        return render(request, 'user_center/user-fav-org.html', {
            'org_list': org_list,
        })


#我收藏的老师
class MyFavTeacherView(LoginRequiredMixin, View):
    def get(self, request):
        fav_teachers = UserFavorite.objects.filter(user=request.user, fav_type=3)
        teacher_list = []
        for fav_teacher in fav_teachers:
            teacher_id = fav_teacher.fav_id
            teacher = Teacher.objects.get(id=teacher_id)
            teacher_list.append(teacher)
        return render(request, 'user_center/usercenter-fav-teacher.html', {
            'teacher_list': teacher_list,
        })


#我收藏的课程
class MyFavCourseView(LoginRequiredMixin, View):
    def get(self, request):
        fav_courses = UserFavorite.objects.filter(user=request.user, fav_type=1)
        course_list = []
        for fav_course in fav_courses:
            course_id = fav_course.id
            course = Course.objects.get(id=course_id)
            course_list.append(course)
        return render(request, 'user_center/usercenter-fav-course.html', {
            'course_list': course_list,
        })


#我的消息
class MyMessageView(LoginRequiredMixin, View):
    def get(self, request):
        all_messages = UserMessage.objects.filter(user=request.user.id)
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(all_messages, 4, request=request)
        messages = p.page(page)
        return render(request, 'user_center/usercenter-message.html', {
            'messages': messages,
        })


#全局404处理函数
def pag_not_found(requset):
    response = render_to_response('404.html', {})
    response.status_code = 404
    return response


#全局500处理函数
def pag_error(request):
    response = render_to_response('500.html', {})
    response.status_code = 500
    return response