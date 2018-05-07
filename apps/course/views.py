from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import View
from course.models import Course, CourseResource, Video
from pure_pagination import PageNotAnInteger, Paginator, EmptyPage
from django.contrib.auth import authenticate
from operation.models import UserFavorite, CourseComments, UserCourse
from utils.mixin_utils import LoginRequiredMixin


class CourseListView(View):
    def get(self, request):
        all_courses = Course.objects.all().order_by('-add_time')

        #热门课程
        hot_courses = Course.objects.all().order_by('-click_nums')[:3]

        #搜索功能
        search_keywords = request.GET.get('keywords', '')
        if search_keywords:
            all_courses = all_courses.filter(Q(name__icontains=search_keywords)|Q(desc__icontains=search_keywords)|Q(detail__icontains=search_keywords))
            #icontains是包含的意思（不区分大小写）
            #Q可以实现多个字段，之间是or的关系


        #排序
        sort = request.GET.get('sort', '')
        if sort:
            if sort == 'students':
                all_courses = Course.objects.all().order_by('-students')
            if sort == 'hot':
                all_courses = Course.objects.all().order_by('-click_nums')

        #分页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(all_courses, 2, request=request)
        courses = p.page(page)
        return render(request, 'course/course-list.html', {
            'all_courses': courses,
            'hot_courses': hot_courses,
            'sort': sort,
        })


#课程详情页
class CourseDetailView(View):
    def get(self, request, course_id):
        course = Course.objects.get(id=course_id)
        course.click_nums += 1
        course.save()

        #判断收藏
        has_fav_course = False
        has_fav_org = False
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course.id, fav_type=1):
                has_fav_course = True
            if UserFavorite.objects.filter(user=request.user, fav_id=course.course_org.id, fav_type=2):
                has_fav_org = True

        #根据课程标签在数据库查找课程
        tag = course.tag
        if tag:
            relate_course = Course.objects.filter(tag=tag)[:3]
        else:
            relate_course = []
        return render(request, 'course/course-detail.html',{
            'course': course,
            'relate_course': relate_course,
            'has_fav_course': has_fav_course,
            'has_fav_org': has_fav_org,
        })


#课程章节信息
class CourseInfoView(LoginRequiredMixin, View):
    def get(self, request, course_id):
        course = Course.objects.get(id=int(course_id))

        #点击数
        course.students += 1
        course.save()

        #查询用户是否学习了该教程
        user_courses = UserCourse.objects.filter(user=request.user, course=course)
        if not user_courses:
            user_course = UserCourse(user=request.user, course=course)
            user_course.save()

        #相关课程推荐
        #找到学习这门课的所有用户
        user_courses = UserCourse.objects.filter(course=course)
        #找到学习这门课的所有用户id
        user_ids = [user_course.user_id for user_course in user_courses]
        #通过所有用户的id,找到所有用户学习过的课程
        all_user_courses = UserCourse.objects.filter(user_id__in=user_ids)
        #取出所有课程id
        course_ids = [all_user_course.course_id for all_user_course in all_user_courses]
        #通过所有课程的id,找到所有的课程，按点击量取五个
        relate_courses = Course.objects.filter(id__in=course_ids).order_by('-click_nums')[:5]

        #课程资源
        all_resources = CourseResource.objects.filter(course=course)
        return render(request, 'course/course-video.html', {
            'course': course,
            'all_resources': all_resources,
            'relate_courses': relate_courses,
        })


#课程评论
class CommentsView(LoginRequiredMixin, View):
    def get(self, request, course_id):
        course = Course.objects.get(id=int(course_id))
        all_resources = CourseResource(course=course)
        all_comments = CourseComments.objects.all()

        # 相关课程推荐
        # 找到学习这门课程的所有用户
        user_courses = UserCourse.objects.filter(course=course)
        # 找到学习这门课的所有用户id
        user_ids = [user_course.course_id for user_course in user_courses]
        # 通过所有用户的id找到所有用户学习过的课程
        all_user_courses = UserCourse.objects.filter(user_id__in=user_ids)
        # 获得所有课程的id
        course_ids = [all_user_course.course_id for all_user_course in all_user_courses]
        # 通过所有课程的id，找到所有的课程，按点击量取五个
        relate_courses = Course.objects.filter(id__in=course_ids).order_by('-click_nums')[:5]
        return render(request, 'course/course-comment.html', {
            'course': course,
            'all_resources': all_resources,
            'all_comments': all_comments,
            'relate_courses': relate_courses,
        })


#添加评论
class AddCommentsView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            # 未登录时返回json提示未登录，跳转到登录页面是在ajax中做的
            return HttpResponse('{"status":"fail", "msg":"用户未登录"}', content_type='application/json')

        course_id = request.POST.get("course_id", 0)
        comments = request.POST.get("comments", "")
        if int(course_id) > 0 and comments:
            # 实例化一个course_comments对象
            course_comments = CourseComments()
            # 获取评论的是哪门课程
            course = Course.objects.get(id=int(course_id))
            # 分别把评论的课程、评论的内容和评论的用户保存到数据库
            course_comments.course = course
            course_comments.comments = comments
            course_comments.user = request.user
            course_comments.save()
            return HttpResponse('{"status":"success", "msg":"评论成功"}', content_type='application/json')
        else:
            return HttpResponse('{"status":"fail", "msg":"评论失败"}', content_type='application/json')


#课程章节视频播放页面
class VideoPlayView(LoginRequiredMixin, View):
    def get(self, request, video_id):
        video = Video.objects.get(id=int(video_id))
        #通过外键找到章节再找到视频对应的课程
        course = video.lesson.course
        course.students +=1
        course.save()

        #查询用户是否学习过该教程
        user_courses = UserCourse.objects.filter(user=request.user, course=course)
        if not user_courses:
            user_course = UserCourse(user=request.user, course=course)
            user_course.save()

        #相关课程推荐
        #找到学习这门课程的所有用户
        user_courses = UserCourse.objects.filter(course=course)
        #找到学习这门课的所有用户id
        user_ids = [user_course.course_id for user_course in user_courses]
        #通过所有用户的id找到所有用户学习过的课程
        all_user_courses = UserCourse.objects.filter(user_id__in=user_ids)
        #获得所有课程的id
        course_ids = [all_user_course.course_id for all_user_course in all_user_courses]
        #通过所有课程的id，找到所有的课程，按点击量取五个
        relate_courses = Course.objects.filter(id__in=course_ids).order_by('-click_nums')[:5]

        #课程资源
        all_resources = CourseResource.objects.filter(course=course)

        return render(request, 'course/course-play.html', {
            'video': video,
            'course': course,
            'relate_courses': relate_courses,
            'all_resources': all_resources,
        })
