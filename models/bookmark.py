from extensions import db

class Bookmark(db.Model):
    __tablename__ = 'bookmarks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship('User', backref='bookmarks', lazy=True)
    book = db.relationship('Book', backref='bookmarked_by', lazy=True)
    
    def save(self):
        db.session.add(self)
        db.session.commit()

    @property
    def data(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'book_id': self.book_id,
            'book_title': self.book.title if self.book else None,
            'created_at': self.created_at
        }

    @classmethod
    def get_all(cls):
        bookmarks = cls.query.all()
        return [bookmark.data for bookmark in bookmarks]

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get(id)
    
    @classmethod
    def get_by_user_id(cls, user_id):
        bookmarks = cls.query.filter_by(user_id=user_id).all()
        return [bookmark.data for bookmark in bookmarks]
