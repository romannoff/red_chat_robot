from db_handler.db_handler import Database
from langchain.schema import HumanMessage, AIMessage
from config import Config
from base_chat import BaseChat


settings = Config.from_yaml("config.yaml")


class SimpleChat(BaseChat):
    def __init__(self, llm, db_name):
        super().__init__(llm)
        self.db = Database(db_name=db_name)

        self.current_chat_id = 0

    # История сообщений
    db = Database(db_name=settings.db_name)

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

    def get_msg(self, msg, history):
        context = self.db.get_history(chat_id=self.current_chat_id, size=20)

        user_msg = {"role": "user", "content": msg}
        system_msg = {"role": "system", "context": settings.system}

        context.insert(0, system_msg)
        context.append(user_msg)

        qwery = self.get_qwery(context)

        answer = self.llm.invoke(qwery)
        answer = answer.content

        self.db.insert(chat_id=self.current_chat_id, role='user', msg_text=msg)
        self.db.insert(chat_id=self.current_chat_id, role='assistant', msg_text=answer)

        return answer
