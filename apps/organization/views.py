from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.views.generic import View

from course.models import Course
from organization.models import CourseOrg, CityDict, Teacher

from django.http import HttpResponse
from organization.forms import UserAskForm
from operation.models import UserFavorite
from django.contrib.auth import authenticate
from django.db.models import Q


#课程机构
class OrgView(View):
    '''课程机构'''
    def get(self, request):
        # 所有课程机构
        all_orgs = CourseOrg.objects.all()

        # 所有城市
        all_citys = CityDict.objects.all()
        # 刷选城市
        city_id = request.GET.get('city', '')
        if city_id:
            all_orgs = all_orgs.filter(city_id=int(city_id))

        #机构类别刷选(先刷选再统计数量)
        category = request.GET.get('ct', '')
        if category:
            all_orgs = all_orgs.filter(category=category)

        #热门机构排名
        hot_orgs = all_orgs.order_by('-click_nums')[:3]

        search_keywords = request.GET.get('keywords', '')
        if search_keywords:
            all_orgs = all_orgs.filter(
                Q(name__icontains=search_keywords) | Q(desc__icontains=search_keywords))
            # icontains是包含的意思（不区分大小写）
            # Q可以实现多个字段，之间是or的关系

        #学习人数和课程人数刷选
        sort = request.GET.get('sort', '')
        if sort:
            if sort =='students':
                all_orgs = all_orgs.order_by('-students')
            elif sort =='courses':
                all_orgs = all_orgs.order_by('-course_nums')

        # 有多少家机构
        org_nums = all_orgs.count()
        # 对课程机构进行分页
        # 尝试获取前台get请求传递过来的page参数
        # 如果是不合法的配置参数默认返回第一页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        # 这里指从allorg中取五个出来，每页显示5个
        p = Paginator(all_orgs, 5, request=request)
        orgs = p.page(page)

        return render(request, "org/org-list.html", {
            "all_orgs": orgs,
            "all_citys": all_citys,
            "org_nums": org_nums,
            'city_id': city_id,
            'category': category,
            'sort': sort,
            'hot_orgs': hot_orgs
        })


#用户添加咨询
class AddUserAskView(View):
    def post(self, request):
        userask_form = UserAskForm(request.POST)
        if userask_form.is_valid():
            user_ask = userask_form.save(commit=True)
            # 如果保存成功,返回json字符串,后面content type是告诉浏览器返回的数据类型
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            # 如果保存失败，返回json字符串,并将form的报错信息通过msg传递到前端
            return HttpResponse('{"status":"fail", "msg":"添加出错"}', content_type='application/json')
'''这里要用到Ajax提交，不会对页面整体刷新，应该给前端返回一个Json数据
HttpResponse可以指定传递到前端的数据类型'''


#机构首页
class OrgHomeView(View):
    def get(self, request, org_id):
        current_page = 'home'
        # 根据id找到课程机构
        course_org = CourseOrg.objects.get(id=int(org_id))

        #点击数
        course_org.click_nums += 1
        course_org.save()

        # 判断收藏状态
        has_fav = False
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True

        # 反向查询到课程机构的所有课程和老师
        all_courses = course_org.course_set.all()[:4]
        all_teacher = course_org.teacher_set.all()[:2]
        return render(request, 'org/org-detail-homepage.html',
                      {'course_org': course_org,
                       'all_courses': all_courses,
                       'all_teacher': all_teacher,
                       'current_page': current_page,
                       'has_fav': has_fav,
                       })


#机构课程列表页
class OrgCourseView(View):
    def get(self, request, org_id):
        current_page = 'course'
        course_org = CourseOrg.objects.get(id=int(org_id))
        # 通过课程机构找到课程。内建的变量，找到指向这个字段的外键引用
        all_courses = course_org.course_set.all()
        # 判断收藏状态
        has_fav = False
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True

        return render(request, 'org/org-detail-course.html', {
            'course_org': course_org,
            'all_courses': all_courses,
            'current_page': current_page,
            'has_fav': has_fav,
        })


#机构介绍页
class OrgDescView(View):
    def get(self, request, org_id):
        current_page = 'desc'
        course_org = CourseOrg.objects.get(id=int(org_id))
        # 判断收藏状态
        has_fav = False
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        return render(request, 'org/org-detail-desc.html', {
            'current_page': current_page,
            'course_org': course_org,
            'has_fav': has_fav,
        })


#机构教师
class OrgTeacherView(View):
    def get(self, request, org_id):
        current_page = 'teacher'
        course_org = CourseOrg.objects.get(id=int(org_id))
        all_teacher = course_org.teacher_set.all()
        # 判断收藏状态
        has_fav = False
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        return render(request, 'org/org-detail-teachers.html', {
            'current_page': current_page,
            'course_org': course_org,
            'all_teacher': all_teacher,
            'has_fav': has_fav,
        })


#用户收藏和取消收藏
class AddFavView(View):
    def post(self, request):
        fav_id = request.POST.get('fav_id', 0)#防止后面int(fav_id)时出错
        fav_type = request.POST.get('fav_type', 0)#防止int(fav_type)出错

        if not request.user.is_authenticated:
            #未登录返回json提示登录，跳转到登录页面是在ajax中做的
            return HttpResponse('{"status":"fail", "msg": "用户未登陆"}', content_type='application/json')
        exist_record = UserFavorite.objects.filter(user=request.user, fav_id=int(fav_id), fav_type=int(fav_type))
        if exist_record:
            # 如果记录已经存在，表示用户取消收藏
            exist_record.delete()
            if int(type) == 1:
                course = Course.objects.get(id=int(id))
                course.fav_nums -= 1
                if course.fav_nums < 0:
                    course.fav_nums = 0
                course.save()

            if int(type) == 2:
                org = CourseOrg.objects.get(id=int(id))
                org.fav_nums -= 1
                if org.fav_nums < 0:
                    org.fav_nums = 0
                org.save()

            if int(type) == 3:
                teacher = Teacher.objects.get(id=int(id))
                teacher.fav_nums -= 1
                if teacher.fav_nums < 0:
                    teacher.fav_nums = 0
                teacher.save()
            return HttpResponse('{"status":"fail", "msg": "已取消收藏"}', content_type='application/json')
        else:
            user_fav = UserFavorite()
            if int(fav_id) > 0 and int(fav_type) > 0:
                user_fav.user = request.user
                user_fav.fav_id = int(fav_id)
                user_fav.fav_type = int(fav_type)
                user_fav.save()

                if int(type) == 1:
                    course = Course.objects.get(id=int(id))
                    course.fav_nums += 1
                    course.save()

                if int(type) == 2:
                    org = CourseOrg.objects.get(id=int(id))
                    org.fav_nums += 1
                    org.save()

                if int(type) == 3:
                    teacher = Teacher.objects.get(id=int(id))
                    teacher.fav_nums += 1
                    teacher.save()
                return HttpResponse('{"status":"success", "msg": "已收藏"}', content_type='application/json')
            else:
                return HttpResponse('{"status":"fail", "msg": "收藏失败"}', content_type='application/json')


# 讲师列表
class TeacherListView(View):
    def get(self, request):
        all_teachers = Teacher.objects.all()
        # 总共有多少老师使用count进行统计
        teacher_nums = all_teachers.count()

        #人气老师
        sort = request.GET.get('sort', '')
        if sort == 'hot':
            all_teachers = all_teachers.order_by('-click_nums')

        #讲师排行榜
        sorted_teacher = all_teachers[:3]

        #搜索
        search_keywords = request.GET.get('keywords', '')
        if search_keywords:
            # 在name字段进行操作,做like语句的操作。i代表不区分大小写
            # or操作使用Q
            all_teachers = all_teachers.filter(name__icontains=search_keywords)

        # 进行分页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(all_teachers, 1, request=request)
        teachers = p.page(page)

        return render(request, "teacher/teachers-list.html", {
            "all_teachers": teachers,
            "teacher_nums": teacher_nums,
            'sort': sort,
            'sorted_teacher': sorted_teacher,
        })


#讲师详情
class TeacherDetailView(View):
    def get(self, request, teacher_id):
        teacher = Teacher.objects.get(id=int(teacher_id))

        #点击数
        teacher.click_nums +=1
        teacher.save()

        all_course = Course.objects.filter(teacher=teacher)
        #讲师排行榜
        sorted_teacher = Teacher.objects.all().order_by('-click_nums')[:3]

        #收藏
        has_teacher_faved = False
        if UserFavorite(user=request.user, fav_type=3, fav_id=teacher.id):
            has_teacher_faved = True

        has_org_faved = False
        if UserFavorite(user=request.user, fav_type=2, fav_id=teacher.org.id):
            has_org_faved = True
        return render(request, 'teacher/teacher-detail.html', {
            'teacher': teacher,
            'all_course': all_course,
            'sorted_teacher': sorted_teacher,
            'has_org_faved': has_org_faved,
            'has_teacher_faved': has_teacher_faved,
        })
