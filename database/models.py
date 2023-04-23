from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class Book(Base):
    __tablename__ = "books"  # Имя таблицы
    id = Column(Integer, primary_key=True)
    title = Column(String(60), primary_key=True)
    author = Column(String(30), primary_key=True)
    reviews = relationship("Reviews", backref="book", lazy=True)  # Связываем таблицу "reviews" с таблицей "Book"

    def __repr__(self):
        return self.title


class Reviews(Base):
    """Класс с обзорами книг"""

    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    text = Column(String(2000), primary_key=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return f"От {self.reviewer}"
