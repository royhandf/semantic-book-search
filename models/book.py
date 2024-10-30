from extensions import db
import asyncio

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, unique=True)
    publisher = db.Column(db.String(255))
    published = db.Column(db.Integer)
    description = db.Column(db.Text)
    isbn = db.Column(db.String(535))
    table_of_contents = db.Column(db.Text)
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
    async def get_all(cls):
        # Menggunakan asyncio.to_thread untuk menjalankan fungsi sinkron
        return await asyncio.to_thread(cls._fetch_all)

    @classmethod
    def _fetch_all(cls):
        # Mengambil semua buku dari database
        r = cls.query.all()  # Mengambil semua entri buku
        return [book.data for book in r]

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get(id)
    
    @classmethod
    def get_description_contents_by_id(cls, id):
        book = cls.query.get(id)
        if book:
            return {
                'description': book.description if book.description else '',
                'table_of_contents': book.table_of_contents.split('\n') if book.table_of_contents else []
            }
        return None
