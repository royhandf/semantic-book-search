from extensions import db

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, unique=True, index=True)
    publisher = db.Column(db.String(255), index=True)
    published = db.Column(db.Integer)
    description = db.Column(db.Text, index=True)
    isbn = db.Column(db.String(535))
    table_of_contents = db.Column(db.Text, index=True)
    pdf_link = db.Column(db.String(255))
    cover_link = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # relationships
    authors = db.relationship('Author', backref='book', lazy=True, cascade="all,delete")
    editors = db.relationship('Editor', backref='book', lazy=True, cascade="all,delete")

    @property
    def data(self):
        return {
            'id': self.id,
            'title': self.title,
            'publisher': self.publisher,
            'published': self.published,
            'description': self.description,
            'isbn': self.isbn,
            'table_of_contents': self.table_of_contents,
            'pdf_link': self.pdf_link,
            'cover_link': self.cover_link,
            'authors': ', '.join([author.name for author in self.authors]),
            'editors': ', '.join([editor.name for editor in self.editors])
        }

    def save(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_all(cls):
        return cls._fetch_all()

    @classmethod
    def _fetch_all(cls):
        r = cls.query.all() 
        return [book.data for book in r]

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).first()
    