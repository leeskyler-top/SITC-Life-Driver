from flask import Flask
from flask_cors import CORS
from Controller.UserController import user_controller
from Controller.DriverController import driver_controller
from Controller.AuthController import auth_controller
from Controller.TemplateController import template_controller
from Controller.SemesterController import semester_controller
from Handler.Handler import handle_global_exceptions
from flask_jwt_extended import (
    JWTManager,
)
import warnings
from urllib3.exceptions import InsecureRequestWarning

from LoadEnviroment.LoadEnv import jwt_secret_key, server_env
from SQLService.Operation import create_database_and_table
from waitress import serve

# 忽略 InsecureRequestWarning 警告
warnings.simplefilter('ignore', InsecureRequestWarning)

# 初始化数据库
create_database_and_table()

# 初始化 Flask 应用
app = Flask(__name__)
CORS(app)

# 注册 Controller
app.register_blueprint(user_controller, url_prefix='/api/v1/user')
app.register_blueprint(auth_controller, url_prefix='/api/v1/auth')
app.register_blueprint(driver_controller, url_prefix='/api/v1/driver')
app.register_blueprint(template_controller, url_prefix='/api/v1/template')
app.register_blueprint(semester_controller, url_prefix='/api/v1/semester')

handle_global_exceptions(app)

# 配置 JWT 密钥
app.config["JWT_SECRET_KEY"] = jwt_secret_key  # 更换为一个更强的密钥
jwt = JWTManager(app)

if __name__ == '__main__':
    if server_env == "production":
        serve(app, host='0.0.0.0', port=8080)
    elif server_env == "development":
        app.run(host='0.0.0.0', port=8080)
    else:
        print("Server environment not supported")
        exit(1)
