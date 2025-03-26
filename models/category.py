from extensions import db

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    keywords = db.Column(db.Text, nullable=False) 
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).first() 

    @classmethod
    def get_all(cls):
        return cls.query.all()

    @property
    def data(self):
        return {
            'id': self.id,
            'name': self.name,
            'keywords': self.keywords.split(',') if self.keywords else []  
        }
