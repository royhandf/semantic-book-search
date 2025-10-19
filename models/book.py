from extensions import db

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, unique=True, index=True)
    authors = db.Column(db.Text, nullable=True)
    editors = db.Column(db.Text, nullable=True)
    language = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, index=True)
    table_of_contents = db.Column(db.Text, index=True)
    publisher = db.Column(db.String(255), index=True)
    published = db.Column(db.Integer)
    subject = db.Column(db.Text, nullable=True)
    isbn = db.Column(db.Text, nullable=True)
    pdf_link = db.Column(db.String(255))
    cover_link = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    @property
    def data(self):
        return {
            'id': self.id,
            'title': self.title,
            'authors': self.authors,
            'editors': self.editors,
            'language': self.language,
            'description': self.description,
            'table_of_contents': self.table_of_contents,
            'publisher': self.publisher,
            'published': self.published,
            'subject': self.subject,
            'isbn': self.isbn,
            'pdf_link': self.pdf_link,
            'cover_link': self.cover_link,
        }

    def save(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_all(cls):
        return [book.data for book in cls.query.all()]

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).first()
    