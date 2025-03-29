import numpy as np
from typing import List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine

Base = declarative_base()


class VectorChunk(Base):
    """
    SQLAlchemy модель для хранения векторных чанков
    """
    __tablename__ = 'vectors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String, nullable=False)
    embedding = Column(LargeBinary, nullable=False)
    filename = Column(String, nullable=False)


class VectorsDataBase:
    """
    Класс для работы с векторной базой данных с использованием SQLAlchemy
    """

    def __init__(
            self,
            db_path: str = 'vector_database.sqlite',
            model_name: str = 'intfloat/multilingual-e5-large-instruct'
    ):
        """
        Инициализация базы данных

        :param db_path: Путь к базе данных SQLite
        :param model_name: Название модели эмбеддингов
        """
        # Создание движка SQLAlchemy
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)

        # Создание таблиц, если их нет
        Base.metadata.create_all(self.engine)

        # Создание фабрики сессий
        self.Session = sessionmaker(bind=self.engine)

        # Загрузка модели эмбеддингов
        self.embedding_model = SentenceTransformer(model_name)

    @staticmethod
    def _convert_embedding_to_array(embedding_bytes: bytes) -> np.ndarray:
        """
        Преобразование байтов в numpy-массив

        :param embedding_bytes: Бинарное представление эмбеддинга
        :return: Numpy-массив эмбеддингов
        """
        return np.frombuffer(embedding_bytes, dtype=np.float32)

    def cosine_similarity_search(
            self,
            query: str,
            top_k: int = 5,
            similarity_threshold: float = 0.5
    ) -> (list, list):
        """
        Поиск наиболее похожих чанков с использованием косинусного расстояния

        :param query: Текстовый запрос
        :param top_k: Максимальное количество возвращаемых результатов
        :param similarity_threshold: Порог схожести
        :return: Список найденных чанков
        """
        print(1)

        query_embedding = self.embedding_model.encode(f"query: {query}")

        with self.Session() as session:
            # Получение всех записей
            records = session.query(VectorChunk).all()

            texts = []
            embeddings = []
            filenames = []

            for record in records:
                # Преобразование blob обратно в numpy-массив
                embedding_array = np.frombuffer(record.embedding, dtype=np.float32)

                texts.append(record.text)
                embeddings.append(embedding_array)
                filenames.append(record.filename)

            cosine_similarity = [cosine(embedding, query_embedding) for embedding in embeddings]

            sort_texts = [
                (find_text, filename) for find_text, _, filename in sorted(
                    zip(texts, cosine_similarity, filenames),
                    key=lambda x: x[1]
                )[:top_k]]
        return [find_text for find_text, _ in sort_texts], [filename for _, filename in sort_texts]
