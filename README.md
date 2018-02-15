
# flask-blog
基于Python Flask框架的实现的个人博客系统

## 主要特性

- 内置模型：栏目、标签、文章、评论等
- 数据库：使用SQLAlchemy驱动，主要支持SQLITE和Mysql两种数据库
- 编辑器：集成[editor.md](https://github.com/pandao/editor.md) Markdown编辑器
- 后台管理：使用Flask-Admin管理后台，功能强大，简单易用

## 主要依赖的 Flask 扩展插件

- Flask-SQLAlchemy 数据库模型
- Flask-Admin 后台管理
- Flask-Login 用户登录

## DEMO

[http://blog.adisonhyh.com/](http://blog.adisonhyh.com/)

## 部署

### 本地环境

本地环境通过 pip + virtualenv 方式部署.

**安装依赖:**

使用 `requirements/common.txt` 来安装依赖, 本地环境默认使用SQLite数据库:

```
pip install -r requirements/common.txt
```

**运行程序:**

如果通过 virtualenv 来运行程序, 需要先激活虚拟环境.

**初始化数据库**:

```python
python manage.py db init 
python manage.py db migrate -m "init"
python manage.py db upgrade        
```
**初始化**
```python
python manage.py deploy
```

**运行程序:**

```
python manage.py runserver
```

若需要强制开启 debug 和 reload 的模式, 请加上参数 `-d -r`.

### 线上部署

[CentOS 部署 flask项目](http://blog.adisonhyh.com/article/2/)

## 主题

基于[keep it simple](https://www.styleshout.com/free-templates/keep-it-simple/)修改



