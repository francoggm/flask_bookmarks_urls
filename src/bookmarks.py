from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from flasgger import swag_from
import validators

from .database import Bookmark, User, db

bookmarks = Blueprint('bookmarks', __name__, url_prefix='/api/v1/bookmarks')

@bookmarks.route('/', methods=['POST', 'GET'])
@jwt_required()
def handle_bookmarks():
    current_user = get_jwt_identity()

    if request.method == 'POST':
        data = request.get_json()
        body = data.get('body', '')
        url = data.get('url', '')

        if not validators.url(url):
            return jsonify({
                "error": "Enter valid url"
            }), 400
        
        if Bookmark.query.filter_by(url = url).first():
            return jsonify({
                "error": "URL already exists"
            }), 409
        
        bookmark = Bookmark(url = url, body = body, user_id = current_user)

        db.session.add(bookmark)
        db.session.commit()

        return jsonify({
            "id": bookmark.id,
            "url": bookmark.url,
            "short_url": bookmark.short_url,
            "visit": bookmark.visits,
            "body": bookmark.body,
            "created_at": bookmark.created_at,
            "updated_at": bookmark.updated_at,
        })

    else:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)

        bookmarks = Bookmark.query.filter_by(user_id=current_user).paginate(page=page, per_page=per_page)

        output = [
            {
                "id": bookmark.id,
                "url": bookmark.url,
                "short_url": bookmark.short_url,
                "visit": bookmark.visits,
                "body": bookmark.body,
                "created_at": bookmark.created_at,
                "updated_at": bookmark.updated_at,
            } for bookmark in bookmarks.items
        ]

        meta = {
            "page": bookmarks.page,
            "pages": bookmarks.pages,
            "total_count": bookmarks.total,
            "prev": bookmarks.prev_num,
            "next_page": bookmarks.next_num,
            "has_page": bookmarks.has_next,
            "has_prev": bookmarks.has_prev
        }

        return jsonify({"bookmarks": output, "meta": meta}), 200

@bookmarks.get("/<int:id>")
@jwt_required()
def get_bookmark(id):
    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id = current_user, id = id).first()
    if not bookmark:
        return jsonify({"error": "Item not found"}), 404
    
    return jsonify(
        {
            "bookmark": 
                {
                    "id": bookmark.id,
                    "url": bookmark.url,
                    "short_url": bookmark.short_url,
                    "visit": bookmark.visits,
                    "body": bookmark.body,
                    "created_at": bookmark.created_at,
                    "updated_at": bookmark.updated_at,
                }
        }
    ), 200

@bookmarks.put("/<int:id>")
@bookmarks.patch("/<int:id>")
@jwt_required()
def update_bookmark(id):
    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id = current_user, id = id).first()
    if not bookmark:
        return jsonify({"error": "Item not found"}), 404
    
    data = request.get_json()
    body = data.get('body', '')
    url = data.get('url', '')

    if not validators.url(url):
        return jsonify({
            "error": "Enter valid url"
        }), 400
    
    if url:
        bookmark.url = url
    if body:
        bookmark.body = body

    db.session.commit()

    return jsonify(
        {
            "bookmark": 
                {
                    "id": bookmark.id,
                    "url": bookmark.url,
                    "short_url": bookmark.short_url,
                    "visit": bookmark.visits,
                    "body": bookmark.body,
                    "created_at": bookmark.created_at,
                    "updated_at": bookmark.updated_at,
                }
        }
    ), 200

@bookmarks.delete("/<int:id>")
@jwt_required()
def delete_bookmark(id):
    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id = current_user, id = id).first()
    if not bookmark:
        return jsonify({"error": "Item not found"}), 404
    
    db.session.delete(bookmark)
    db.session.commit()

    return jsonify({}), 200

@bookmarks.get('/stats')
@jwt_required()
@swag_from('./docs/bookmarks/stats.yml')
def get_stats():
    current_user = get_jwt_identity()
    items = Bookmark.query.filter_by(user_id=current_user).all()

    output = [
        {
            "visists": item.visits,
            "url": item.url,
            "id": item.id,
            "short_url": item.short_url
        } for item in items
    ]

    return jsonify({"bookmarks": output}), 200



