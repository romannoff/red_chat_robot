from abc import abstractmethod


class BaseChat:
    def __init__(self, llm):
        self.llm = llm

    @abstractmethod
    def get_msg(self, msg: str, history: list) -> str: ...
