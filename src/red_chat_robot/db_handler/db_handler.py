from typing import List, Dict, Optional
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import text

Base = declarative_base()


class MsgHistory(Base):
    __tablename__ = 'history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer)
    msg_type = Column(String)
    msg_text = Column(String)


class Database:
    def __init__(self, db_name: str = "example.db"):
        """
        Args:
            db_name: путь к базе данных
        """
        self.db_name = db_name
        self.engine = create_engine(
            f'sqlite:///{db_name}',
            pool_size=2,
            max_overflow=8,
            poolclass=QueuePool
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create_table(self) -> None:
        Base.metadata.create_all(self.engine)

    def insert(self, chat_id: int, role: str, msg_text: str) -> None:
        """
        Добавление в память сообщения
        :param chat_id:     id чата
        :param role:        Роль (user или assistant)
        :param msg_text:    Текст сообщения
        :return:            None
        """
        with self.Session() as session:
            new_msg = MsgHistory(chat_id=chat_id, msg_type=role, msg_text=msg_text)
            session.add(new_msg)
            session.commit()

    def get_history(self, chat_id: int, size: Optional[int] = None) -> Optional[List[Dict]]:
        """
        Получить историю.
        :param chat_id: id чата
        :param size:    Количество возвращаемых сообщений.
        :return:        List {'role': msg_type, 'content': msg_text} or None if empty
        """
        with self.Session() as session:
            query = session.query(MsgHistory).filter(MsgHistory.chat_id == chat_id)

            if size and size > 0:
                query = query.order_by(MsgHistory.id.desc()).limit(size)
            else:
                query = query.order_by(MsgHistory.id.desc())

            history = query.all()
            if not history:
                return []

            return [dict(role=msg.msg_type, content=msg.msg_text) for msg in reversed(history)]

    def clear_history(self, chat_id):
        """
        Очистка истории
        :param chat_id: id чата
        :return:        None
        """
        with self.Session() as session:
            session.query(MsgHistory).filter(MsgHistory.chat_id == chat_id).delete()
            session.commit()


if __name__ == '__main__':
    db = Database()
    db.insert(1, '22', 'freerrvfer')
    db.insert(2, '33', 'freerrvfer')
    db.insert(1, '22', 'freerrvfer')
    db.insert(2, '33', 'freerrvfer')

    print(db.get_history(1))

    db.clear_history(2)
    print(db.get_history(2))
    print(db.get_history(1))
