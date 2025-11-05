import datetime as dt

from flask import abort, current_app, jsonify, request
from flask_restful import Resource, fields, marshal_with
from flask_jwt_extended import jwt_required, get_jwt_identity
from webapp.blog.models import db, Post, Tag, Comment
from webapp.auth.models import User
from .parsers import (
    post_get_parser,
    post_post_parser,
    post_put_parser,
    comment_post_parser
)
from .fields import HTMLField
from sqlalchemy.orm import sessionmaker


nested_tag_fields = {
    'id': fields.Integer(),
    'title': fields.String()
}

post_fields = {
    'id': fields.Integer(),
    'author': fields.String(attribute=lambda x: x.user.username),
    'title': fields.String(),
    'text': HTMLField(),
    'tags': fields.List(fields.Nested(nested_tag_fields)),
    'publish_date': fields.DateTime(dt_format='iso8601')
}

comment_fields = {
    'user': fields.String(attribute=lambda x: x.User.username),
    'post_title': fields.String(attribute=lambda x: x.Post.title),
    'comment_id': fields.Integer(attribute=lambda x: x.Comment.id),
    'comment_author': fields.String(attribute=lambda x: x.Comment.name),
    'comment_text': HTMLField(attribute=lambda x: x.Comment.text),
    'comment_publish_date': fields.DateTime(attribute=lambda x: x.Comment.date, dt_format='iso8601')
}


def add_tags_to_post(post, tags_list):
    post.tags = []
    for item in tags_list:
        tag = Tag.query.filter_by(title=item).first()

        # Add the tag if it exists. If not, make a new tag
        if tag:
            post.tags.append(tag)
        else:
            new_tag = Tag(item)
            post.tags.append(new_tag)


class PostApi(Resource):
    @marshal_with(post_fields)
    @jwt_required()
    def get(self, post_id=None):
        if post_id:
            post = Post.query.get(post_id)
            if not post:
                abort(404)
            return post
        else:
            args = post_get_parser.parse_args()
            page = args['page'] or 1

            if args['user']:
                user = User.query.filter_by(username=args['user']).first()
                if not user:
                    abort(404)

                posts = user.posts.order_by(
                    Post.publish_date.desc()
                ).paginate(page, current_app.config['POSTS_PER_PAGE'])
            else:
                posts = Post.query.order_by(
                    Post.publish_date.desc()
                ).paginate(page, current_app.config['POSTS_PER_PAGE'])
            return posts.items

    @jwt_required()
    def post(self):
        print(request.data)
        args = post_post_parser.parse_args(strict=True)
        new_post = Post(args['title'])
        new_post.user_id = get_jwt_identity()
        new_post.text = args['text']

        if args['tags']:
            add_tags_to_post(new_post, args['tags'])

        db.session.add(new_post)
        db.session.commit()
        return {'id': new_post.id}, 201

    @jwt_required()
    def put(self, post_id=None):
        if not post_id:
            abort(400)
        post = Post.query.get(post_id)
        if not post:
            abort(404)
        args = post_put_parser.parse_args(strict=True)
        if get_jwt_identity() != post.user_id:
            abort(403)
        if args['title']:
            post.title = args['title']
        if args['text']:
            post.text = args['text']
        if args['tags']:
            add_tags_to_post(post, args['tags'])

        db.session.merge(post)
        db.session.commit()
        return {'id': post.id}, 201

    @jwt_required()
    def delete(self, post_id=None):
        if not post_id:
            abort(400)
        post = Post.query.get(post_id)
        if not post:
            abort(404)
        if get_jwt_identity() != post.user_id:
            abort(401)

        comments = Comment.query.filter_by(post_id=post_id).all()
        for comment in comments:
            db.session.delete(comment)    

        db.session.delete(post)
        db.session.commit()
        return "", 204


class CommentsApi(Resource):
    @marshal_with(comment_fields)
    @jwt_required()
    def get(self, post_id=None):
        args = post_get_parser.parse_args()
        page = args['page'] or 1        

        if post_id:
            temp_query = db.session.query(Comment, Post, User).join(Post, Post.id==Comment.post_id).join(User, User.id==Post.user_id)
            new_temp_query = temp_query.filter(Comment.post_id==post_id)
            comments = new_temp_query.paginate(page, current_app.config['POSTS_PER_PAGE'])

            return comments.items
        else:
            if args['user']:
                user = User.query.filter_by(username=args['user']).first()
                if not user:
                    abort(404)

                temp_query = db.session.query(Comment, Post, User).join(Post, Post.id==Comment.post_id).join(User, User.id==Post.user_id)
                new_temp_query = temp_query.filter_by(username=args['user'])
                comments = new_temp_query.paginate(page, current_app.config['POSTS_PER_PAGE'])
            else:
                temp_query = db.session.query(Comment, Post, User).join(Post, Post.id==Comment.post_id).join(User, User.id==Post.user_id)
                comments = temp_query.paginate(page, current_app.config['POSTS_PER_PAGE'])

            return comments.items

    @jwt_required()
    def post(self, post_id=None):
        print(request.data)
        args = comment_post_parser.parse_args(strict=True)

        if post_id:
            post = Post.query.get(post_id)
            if not post:
                abort(404)

            new_comment = Comment()
            new_comment.name = args['name']
            new_comment.text = args['text']
            new_comment.post_id = post_id

            db.session.add(new_comment)
            db.session.commit()
            
            return {'id': new_comment.id}, 201
        else:
            abort(400)
