#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2017/11/25

from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, TextAreaField, BooleanField, SelectField, \
    SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField


class PostForm(FlaskForm):
    body = PageDownField("What's on your mind?", validators=[DataRequired()])
    submit = SubmitField('Submit')


class CommentForm(FlaskForm):
    name = StringField(u'昵称', validators=[DataRequired()])
    email = StringField(u'邮箱', validators=[DataRequired(), Length(1, 64),
                                           Email()])
    content = TextAreaField(u'内容', validators=[DataRequired(), Length(1, 1024)])
    follow_id = StringField()
    follow = StringField()
