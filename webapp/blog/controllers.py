import datetime
from sqlalchemy import desc, func
from flask import (
    render_template,
    Blueprint,
    flash,
    redirect,
    url_for,
    session,
    current_app,
    abort,
    request,
    get_flashed_messages
)
from flask_login import login_required, current_user
from .models import Reminder, db, Post, Tag, Comment, tags
from .. import cache
from .forms import CommentForm, PostForm, ReminderForm
from ..auth.models import User
from ..auth import has_role

blog_blueprint = Blueprint(
    'blog',
    __name__,
    template_folder='../templates/blog',
    url_prefix="/blog"
)


def make_cache_key(*args, **kwargs):
    path = request.path.replace("/comment", "")
    path = path.replace("/edit", "/post")
    path = path.replace("reminder", "")
    args = str(hash(frozenset(request.args.items())))
    if current_user.is_authenticated:
        roles = str(current_user.roles)
    else:
        roles = ""
    res = path + args + roles + session.get('locale', '')
    return res


@cache.cached(timeout=60, key_prefix='sidebar_data')
def sidebar_data():
    recent = Post.query.order_by(Post.publish_date.desc()).limit(5).all()
    top_tags = db.session.query(
        Tag, func.count(tags.c.post_id).label('total')
    ).join(tags).group_by(Tag).order_by(desc(
        func.count(tags.c.post_id)
    )).limit(5).all()

    return recent, top_tags


@blog_blueprint.route('/', methods=('GET', 'POST'))
@blog_blueprint.route('/<int:page>', methods=('GET', 'POST'))
@cache.cached(timeout=60, key_prefix=make_cache_key)
def home(page=1):

    posts = Post.query.order_by(
        Post.publish_date.desc()
        ).paginate(page, current_app.config['POSTS_PER_PAGE'], False)

    recent, top_tags = sidebar_data()
    
    return render_template(
        'home.html',
        posts=posts,
        recent=recent,
        top_tags=top_tags
    )


@blog_blueprint.route('/reminder', methods=['GET', 'POST'])
def home_add_reminder():

    form = ReminderForm()
    if form.validate_on_submit():
        new_rem = Reminder()
        new_rem.text = form.text.data
        new_rem.email = form.email.data
        new_rem.date = datetime.datetime.now()

        db.session.add(new_rem)
        db.session.commit()
        flash('Reminder added', 'info')
        print(make_cache_key())
        cache.delete(make_cache_key())
        return redirect(url_for('blog.home'))
    return render_template('reminder.html', form=form)


@blog_blueprint.route('/new', methods=['GET', 'POST'])
@login_required
@has_role('poster')
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        new_post = Post(form.title.data)
        new_post.user_id = current_user.id
        new_post.text = form.text.data
        new_post.youtube_id = form.youtube_id.data

        new_post.tags = []
        for new_tag_title in form.tags.data:
            new_tag = Tag.query.filter_by(title=new_tag_title).first()
            if not(new_tag):
                new_tag = Tag(new_tag_title)
            new_post.tags.append(new_tag)

        db.session.add(new_post)
        db.session.commit()
        flash('Post added', 'info')
        return redirect(url_for('.post', post_id=new_post.id))
    return render_template('new.html', form=form)


@blog_blueprint.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)
    # We want that the current user can edit is own posts
    if current_user.id == post.user.id:
        form = PostForm()
        if form.validate_on_submit():
            post.title = form.title.data
            post.text = form.text.data
            post.publish_date = datetime.datetime.now()
            post.youtube_id = form.youtube_id.data
            
            post.tags = []
            for new_tag_title in form.tags.data:
                new_tag = Tag.query.filter_by(title=new_tag_title).first()
                if not(new_tag):
                    new_tag = Tag(new_tag_title)
                post.tags.append(new_tag)

            db.session.merge(post)
            db.session.commit()
            cache.delete(make_cache_key())
            return redirect(url_for('.post', post_id=post.id))
        form.title.data = post.title
        form.text.data = post.text
        form.youtube_id.data = post.youtube_id
        list_tags = []
        for tag in post.tags:
            list_tags.append(tag.title)
        form.tags.data = list_tags
        return render_template('edit.html', form=form, post=post)
    abort(403)


@blog_blueprint.route('/post/<int:post_id>/comment', methods=['GET', 'POST'])
def post_add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        new_comment = Comment()
        new_comment.name = form.name.data
        new_comment.text = form.text.data
        new_comment.post_id = post_id

        db.session.add(new_comment)
        db.session.commit()
        flash('Comment added', 'info')
        cache.delete(make_cache_key())
        return redirect(url_for('blog.post', post_id=post_id))
    return render_template('comment.html', form=form, post=post)


@blog_blueprint.route('/post/<int:post_id>', methods=('GET', 'POST'))
@cache.cached(timeout=60, key_prefix=make_cache_key)
def post(post_id):
    post = Post.query.get_or_404(post_id)
    tags = post.tags
    comments = post.comments.order_by(Comment.date.desc()).all()
    recent, top_tags = sidebar_data()
    
    return render_template(
        'post.html',
        post=post,
        tags=tags,
        comments=comments,
        recent=recent,
        top_tags=top_tags
    )


@blog_blueprint.route('/posts_by_tag/<string:tag_name>')
@blog_blueprint.route('/posts_by_tag/<string:tag_name>/')
@blog_blueprint.route('/posts_by_tag/<string:tag_name>/<int:page>')
@cache.cached(timeout=60, key_prefix=make_cache_key)
def posts_by_tag(tag_name, page=1):
    tag = Tag.query.filter_by(title=tag_name).first_or_404()
    posts = tag.posts.order_by(
        Post.publish_date.desc()
        ).paginate(page, current_app.config['POSTS_PER_PAGE'], True)
    # posts = tag.posts.order_by(Post.publish_date.desc()).all()
    recent, top_tags = sidebar_data()

    return render_template(
        'tag.html',
        tag=tag,
        posts=posts,
        recent=recent,
        top_tags=top_tags
    )


@blog_blueprint.route('/posts_by_user/<string:username>')
@blog_blueprint.route('/posts_by_user/<string:username>/')
@blog_blueprint.route('/posts_by_user/<string:username>/<int:page>')
@cache.cached(timeout=60, key_prefix=make_cache_key)
def posts_by_user(username, page=1):
    user = User.query.filter_by(username=username).first_or_404()
    posts = user.posts.order_by(
        Post.publish_date.desc()
        ).paginate(page, current_app.config['POSTS_PER_PAGE'], True)
    recent, top_tags = sidebar_data()

    return render_template(
        'user.html',
        user=user,
        posts=posts,
        recent=recent,
        top_tags=top_tags
    )
