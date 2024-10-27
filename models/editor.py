from extensions import db

class Editor(db.Model):
    __tablename__ = 'editors'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    @property
    def data(self):
        return {
            'id': self.id,
            'book_id': self.book_id,
            'name': self.name
        }

    def save(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_all(cls):
        r = cls.query.all()
        return [editor.data for editor in r]

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get(id)