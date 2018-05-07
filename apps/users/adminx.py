import xadmin
from .models import EmailVerifyRecord, Banner
from xadmin import views


# 创建xadmin的最基本管理器配置，并与view绑定
#1使用xadmin的主题功能
class BaseSetting(object):
    #开启主题功能
    enable_themes = True
    use_bootswatch = True


#2全局配置，全局修改，固定写法
class GlobalSettings(object):
    #修改title
    site_title = '杨先森后台管理页面'
    #修改footer
    site_footer = '杨先森的公司'
    #收起菜单
    menu_style = 'accordion'

#xadmin中这里是继承object，不再是继承admin
class EmailVerifyRecordAdmin(object):
    list_display = ['code', 'email', 'send_type', 'send_time']
    search_fields = ['code', 'email', 'send_type']
    list_filter = ['code', 'email', 'send_type', 'send_time']


class BannerAdmin(object):
    list_display = ['title', 'image', 'url', 'index', 'add_time']
    search_fields = ['title', 'image', 'url', 'index']
    list_filter = ['title', 'image', 'url', 'index', 'add_time']

xadmin.site.register(EmailVerifyRecord, EmailVerifyRecordAdmin)
xadmin.site.register(Banner, BannerAdmin)
xadmin.site.register(views.BaseAdminView, BaseSetting)# 将基本配置管理与view绑定
# 将title和footer信息进行注册
xadmin.site.register(views.CommAdminView, GlobalSettings)