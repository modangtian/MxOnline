#操作数据库
import pymysql
pymysql.install_as_MySQLdb()

#将应用名修改成中文
default_app_config = 'users.apps.UsersConfig'