#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2017/11/21
from flask import render_template, abort, redirect, url_for, request, current_app, flash
from . import main
from .. import db
from .forms import PostForm, CommentForm
from app.models import User, Article, Source, Category, Tag, Comment, Follow


@main.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Article.query.order_by(
        Article.created.desc()).paginate(page,
                                         per_page=Article.PER_PAGE,
                                         error_out=False)
    articles = pagination.items
    return render_template('index.html', articles=articles,
                           pagination=pagination, endpoint='.index')


@main.route('/about/')
def about():
    return render_template('about.html')


@main.route('/contact/', methods=['GET', 'POST'])
def contact():
    form = CommentForm(request.form, follow_id=-1)
    if form.validate_on_submit():
        followed_id = int(form.follow_id.data if form.follow_id.data else -1)
        reply_to = form.follow.data
        content = form.content.data
        if reply_to:
            content = form.content.data.replace("@" + reply_to + " ", "")
        comment = Comment(content=content,
                          author_name=form.name.data,
                          author_email=form.email.data,
                          comment_type='contact')
        db.session.add(comment)
        db.session.commit()

        if followed_id != -1:
            followed = Comment.query.get_or_404(followed_id)
            f = Follow(follower=comment, followed=followed)
            comment.comment_type = 'reply'
            # comment.reply_to = followed.author_name
            comment.reply_to = reply_to if reply_to else followed.author_name
            db.session.add(f)
            db.session.add(comment)
            db.session.commit()
        # flash(u'提交评论成功！', 'success')
        return redirect(url_for('.contact', page=-1))
    page = request.args.get('page', 1, type=int)
    _query = Comment.query.filter_by(comment_type='contact')
    counts = _query.count()
    if page == -1:
        page = int((counts - 1) / Comment.PER_PAGE + 1)
    pagination = _query.order_by(Comment.created.asc()).paginate(
        page, per_page=Comment.PER_PAGE,
        error_out=False)
    comments = pagination.items
    return render_template('contact.html', comments=comments, counts=counts, pagination=pagination, form=form,
                           endpoint='.contact')


@main.route('/archives/')
def archives():
    count = Article.query.count()
    page = request.args.get('page', 1, type=int)
    pagination = Article.query.order_by(Article.created.desc()).paginate(
        page, per_page=Article.PER_PAGE,
        error_out=False
    )
    articles = [article for article in pagination.items if article.published]
    # times = [article.timestamp for article in posts ]
    year = list(set([i.year for i in articles]))[::-1]
    data = {}
    year_article = []
    for y in year:
        for p in articles:
            if y == p.year:
                year_article.append(p)
                data[y] = year_article
        year_article = []

    return render_template('archives.html',
                           articles=articles,
                           year=year,
                           data=data,
                           count=count,
                           pagination=pagination, endpoint='.archives')


@main.route('/article/<int:id>/', methods=['GET', 'POST'])
def article(id):
    article = Article.query.get_or_404(id)
    if not article.published:
        abort(403)
    next = next_article(article)
    prev = prev_article(article)
    form = CommentForm(request.form, follow_id=-1)
    if form.validate_on_submit():
        followed_id = int(form.follow_id.data if form.follow_id.data else -1)
        reply_to = form.follow.data
        content = form.content.data
        if reply_to:
            content = form.content.data.replace("@" + reply_to + " ", "")
        comment = Comment(article=article,
                          content=content,
                          author_name=form.name.data,
                          author_email=form.email.data)
        db.session.add(comment)
        db.session.commit()

        if followed_id != -1:
            followed = Comment.query.get_or_404(followed_id)
            f = Follow(follower=comment, followed=followed)
            comment.comment_type = 'reply'
            # comment.reply_to = followed.author_name
            comment.reply_to = reply_to if reply_to else followed.author_name
            db.session.add(f)
            db.session.add(comment)
            db.session.commit()
        # flash(u'提交评论成功！', 'success')
        return redirect(url_for('.article', id=article.id, page=-1))
    # if form.errors:
    # flash(u'发表评论失败', 'danger')

    page = request.args.get('page', 1, type=int)
    counts = article.comments.count()
    if page == -1:
        page = int((counts - 1) / Comment.PER_PAGE + 1)
    pagination = article.comments.order_by(Comment.created.asc()).paginate(
        page, per_page=Comment.PER_PAGE,
        error_out=False)
    comments = pagination.items

    return render_template('article.html', article=article, category_id=article.category_id, next_article=next,
                           prev_article=prev, comments=comments, counts=counts, pagination=pagination, form=form,
                           endpoint='.article', id=article.id)


def next_article(article):
    """
    获取本篇文章的下一篇
    :param article: article
    :return: next article
    """
    article_list = Article.query.order_by(Article.created.desc()).all()
    articles = [article for article in article_list if article.published]
    if articles[0] != article:
        next_post = articles[articles.index(article) - 1]
        return next_post
    return None


def prev_article(article):
    """
    获取本篇文章的上一篇
    :param article: article
    :return: prev article
    """
    article_list = Article.query.order_by(Article.created.desc()).all()
    articles = [article for article in article_list if article.published]
    if articles[-1] != article:
        prev_article = articles[articles.index(article) + 1]
        return prev_article
    return None


@main.route('/user/<username>/')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(400)
    return render_template('user.html', user=user)


@main.route('/category/<int:id>/')
def category(id):
    page = request.args.get('page', 1, type=int)
    pagination = Category.query.get_or_404(id).articles.order_by(
        Article.created.desc()).paginate(
        page, per_page=Article.PER_PAGE,
        error_out=False)
    articles = pagination.items
    return render_template('index.html', articles=articles,
                           pagination=pagination, endpoint='.category',
                           id=id, category_id=id)


@main.route('/search/')
def search():
    page = int(request.args.get('page', 1))
    keyword = request.args.get('keyword', None)
    pagination = None
    articles = None
    if keyword:
        pagination = Article.query.search(keyword).order_by(
            Article.created.desc()).paginate(
            page, per_page=Article.PER_PAGE,
            error_out=False)
        articles = pagination.items

    return render_template('index.html',
                           articles=articles,
                           keyword=keyword,
                           pagination=pagination, endpoint='.index')


@main.route('/tag/<name>/')
def tag(name):
    page = int(request.args.get('page', 1))
    # 若name为非ASCII字符，传入时一般是经过URL编码的
    # 若name为URL编码，则需要解码为Unicode
    # URL编码判断方法：若已为URL编码, 再次编码会在每个码之前出现`%25`
    # _name = to_bytes(name, 'utf-8')
    # if urllib.quote(_name).count('%25') > 0:
    #     name = urllib.unquote(_name)
    tag = Tag.query.filter_by(name=name).first_or_404()
    _query = Article.query.filter(Article.tags.any(id=tag.id)).order_by(
        Article.created.desc())
    pagination = _query.paginate(
        page, per_page=Article.PER_PAGE,
        error_out=False)
    articles = pagination.items
    return render_template('index.html',
                           articles=articles,
                           tag=tag,
                           pagination=pagination, endpoint='.index', select_tag=tag)
