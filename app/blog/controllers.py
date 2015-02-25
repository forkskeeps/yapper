"""Blog post controller."""
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from flask import current_app, redirect, url_for, render_template, \
    flash, request, abort, jsonify
from app import db
from flask.ext.login import login_required, current_user
from . import blog_blueprint
from .forms import PostForm
from .models import Post, Tag
from ..user.models import Permission
from app.decorators import permission_required


@blog_blueprint.route('/page/<int:page>')
@blog_blueprint.route('/')
def index(page=1):
    """Show lst of latest blog posts."""
    pagination = Post.query.order_by(
            Post.created_at.desc()
    ).paginate(
        page=page,
        per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items
    return render_template(
        'blog/index.html',
        posts=posts,
        pagination=pagination,
        title='Posts' if page < 2 else 'Posts - Page '+str(page)
    )


@blog_blueprint.route('/<int:pid>', methods=['GET'])
@blog_blueprint.route('/<int:pid>/<string:slug>', methods=['GET'])
def get_post(pid=None, slug=None):
    """Display a blog post with given id."""
    post = Post.query.get_or_404(pid)
    return render_template(
        'blog/index.html',
        posts=[post],
        pagination=None,
        title=post.title
    )


@blog_blueprint.route('/new', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE_POSTS)
def add():
    """Create a new blog post."""
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            description=form.description.data,
            content=form.body.data,
            author=current_user._get_current_object()
        )
        db.session.add(post)
        db.session.commit()
        flash(u'Post added')
        return redirect(url_for('.index'))
    return render_template('blog/add.html', form=form, title='Create New Post')


@blog_blueprint.route('/<int:pid>/edit', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE_POSTS)
def edit_post(pid=None):
    """Edit a blog post with given id."""
    post = Post.query.get_or_404(pid)
    if not (current_user.is_admin() or current_user.id == post.author.id):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.description = form.description.data
        post.content = form.body.data
        db.session.add(post)
        db.session.commit()
        flash(u'Post Updated', 'success')
        return redirect(url_for('.get_post', pid=post.id))
    form.title.data = post.title
    form.description.data = post.description
    form.body.data = post.body
    return render_template(
        'blog/add.html',
        form=form,
        title='Edit Post - '+post.title
    )


@blog_blueprint.route('/<int:pid>', methods=['DELETE', 'POST'])
@login_required
def delete(pid):
    """Delete a blog post with given id."""
    post = Post.query.get_or_404(pid)
    if current_user.is_admin() or post.author.id == current_user.id:
        db.session.delete(post)
        db.session.commit()
        flash(u'Post deleted.', 'success')
        return redirect(url_for('.index'))
    else:
        abort(403)


@blog_blueprint.route('/tag/', methods=['GET', 'POST', 'DELETE', 'PUT'])
@login_required
def add_tag():
    """Tag addition and deletion."""
    if request.method == 'GET':
        tag_name = request.args.get('name', '')
        if tag_name == '':
            return jsonify({
                'type': 'error',
                'message': 'Invalid paramater.'
            }), 400
        tags = Tag.query.filter_by(name=tag_name.lower()).all()
        return jsonify({
            'type': 'success',
            'message': tags
        })
    if request.method == 'POST':
        taglist = request.form.get('name', '')
        if taglist == '':
            return jsonify({
                'type': 'error',
                'message': 'Invalid paramater.'
            }), 400
        taglist = taglist.split(',')
        tags = []
        for tag in taglist:
            tag = tag.lower()
            try:
                ctag = Tag.query.filter_by(name=tag).one()
            except NoResultFound:
                tags.append(Tag(name=tag))
            except MultipleResultsFound:
                pass
        if len(tags) > 0:
            db.session.add_all(tags)
            db.session.commit()
        return jsonify({
            'type': 'success',
            'message': tags
        })
