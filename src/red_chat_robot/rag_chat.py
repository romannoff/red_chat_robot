from base_chat import BaseChat
from db_handler.db_handler import Database
from db_handler.vectors_db_handler import VectorsDataBase
from langchain.schema import HumanMessage, AIMessage
from config import Config


settings = Config.from_yaml("config.yaml")


class RagChat(BaseChat):
    def __init__(self, llm, db_name, vdb_name):
        super().__init__(llm)
        self.db = Database(db_name=db_name)

        # Векторная база данных 'src/database/vector_database.sqlite'
        self.vectors_db = VectorsDataBase(vdb_name)

        self.current_chat_id = 0

    def get_msg(self, msg: str, history: list) -> str:
        history = self.db.get_history(chat_id=self.current_chat_id, size=5)

        # todo: LLM составляет запрос
        # todo: LLM router

        # добавляем контекст
        texts, sources = self.vectors_db.cosine_similarity_search(msg, top_k=2)
        context = '\n'.join(texts)
        msg = f'context:\n{context}\n{msg}'
        # print(msg)

        # работа с LLM

        user_msg = {"role": "user", "content": msg}
        system_msg = {"role": "system", "context": settings.system}

        history.insert(0, system_msg)
        history.append(user_msg)

        qwery = self.get_qwery(history)

        answer = self.llm.invoke(qwery)
        answer = answer.content

        self.db.insert(chat_id=self.current_chat_id, role='user', msg_text=msg)
        self.db.insert(chat_id=self.current_chat_id, role='assistant', msg_text=answer)

        return answer

    @staticmethod
    def get_qwery(messages_list):
        """
        Составление запроса из истории чата.
        :param messages_list: Список сообщений из базы данных.
        :return: Промпт для LLM
        """
        langchain_messages = []
        for msg in reversed(messages_list):
            if msg["role"] == "user":
                langchain_messages.insert(0, HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.insert(0, AIMessage(content=msg["content"]))

        return langchain_messages
