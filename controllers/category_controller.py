from models.category import Category
from flask import request, jsonify
from extensions import db

def get_all_categories():
    try:
        results = Category.get_all()
        return jsonify({
            "status": "success",
            "data": [category.data for category in results]
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
        
def create_category():
    try:
        data = request.get_json()
        name = data.get('name')
        keywords = data.get('keywords')

        if not name or not keywords:
            return jsonify({"message": "Name and keywords are required"}), 400

        if Category.query.filter_by(name=name).first():
            return jsonify({"message": "Category already exists"}), 409

        new_category = Category(name=name, keywords=",".join(keywords))
        db.session.add(new_category)
        db.session.commit()

        return jsonify({"status": "success", "data": new_category.data}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

def update_category(category_id):
    category = Category.get_by_id(category_id)
    if not category:
        return jsonify({"status": "error", "message": "Category not found"}), 404

    try:
        data = request.get_json()
        category.name = data.get("name", category.name)

        # Pastikan keywords adalah array sebelum diubah ke string
        if "keywords" in data and isinstance(data["keywords"], list):
            category.keywords = ",".join(data["keywords"])

        db.session.commit()

        return jsonify({
            "status": "success",
            "data": {
                "id": category.id,
                "name": category.name,
                "keywords": category.keywords.split(",") if category.keywords else []
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

