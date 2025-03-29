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
        # prompt = self.get_prompt(msg, history)

        # todo: LLM router

        # добавляем контекст
        texts, sources = self.vectors_db.cosine_similarity_search(msg, top_k=3)
        context = '\n'.join(texts)
        # msg = f 'context:\n{context}\n{msg}'
        print(context)

        # работа с LLM

        user_msg = {"role": "user", "content": msg}
        system_msg = {"role": "system", "content": settings.system}
        context_msg = {"role": "system", "context": context}

        history.insert(0, system_msg)
        history.append(context_msg)
        history.append(user_msg)

        qwery = self.get_qwery(history)

        answer = self.llm.invoke(qwery)
        answer = answer.content

        self.db.insert(chat_id=self.current_chat_id, role='user', msg_text=msg)
        self.db.insert(chat_id=self.current_chat_id, role='assistant', msg_text=answer)

        return answer

    def get_prompt(self, user_query, history):
        # user_msg = {"role": "user", "content": user_query}
        # system_msg = {"role": "system", "content": settings.prompt_generator_system}
        # history.insert(0, system_msg)
        # history.append(user_msg)

        history = [msg['content'] for msg in history]
        history = '\n'.join(history)

        topic_prompt = settings.topic_system + '\n Вопрос: \n' + user_query + '\n' + 'История:\n' + history + '\n' + 'Ответ: '

        self.llm.temperature = 0.0
        answer = self.llm.invoke(topic_prompt)
        print('topic', '_' * 100)
        print(answer.content)

        print('summ', '_' * 100)
        system_prompt = settings.prompt_generator_system + '\n Вопрос пользователя: \n' + user_query + '\n'

        history_msg = system_prompt + '\nИстория диалога:\n', history + '\nПерефразированный вопрос:'
        answer = self.llm.invoke(history_msg)
        print(answer.content)
        print('context', '_' * 100)
        self.llm.temperature = 1.0
        return answer.content

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
