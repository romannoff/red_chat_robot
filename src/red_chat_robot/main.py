import gradio as gr
from db_handler.db_handler import Database
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
from config import Config


settings = Config.from_yaml("config.yaml")

# История сообщений
db = Database(db_name=settings.db_name)


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


def chat(msg, history):
    context = db.get_history(chat_id=current_chat_id.value, size=20)

    user_msg = {"role": "user", "content": msg}
    system_msg = {"role": "system", "context": settings.system}

    context.insert(0, system_msg)
    context.append(user_msg)

    qwery = get_qwery(context)

    answer = llm.invoke(qwery)
    answer = answer.content

    db.insert(chat_id=current_chat_id.value, role='user', msg_text=msg)
    db.insert(chat_id=current_chat_id.value, role='assistant', msg_text=answer)

    return answer


def clear_history():
    db.clear_history(current_chat_id.value)


def get_chat_interface(chat_id):
    history = [
        {'role': msg['role'], 'metadata': None, 'content': msg['content'], 'options': None}
        for msg in db.get_history(chat_id)
    ]

    return gr.ChatInterface(
        fn=chat,
        type="messages",
        chatbot=gr.Chatbot(value=history, type="messages"),
        # title="Chat Bot🤖",
    )


def process_api_key(api_key):
    global llm
    llm = ChatOpenAI(
        model_name=settings.model_name,
        openai_api_base=settings.url,
        openai_api_key=api_key,
    )


current_chat_id = gr.State(value=0)

with gr.Blocks() as demo:
    with gr.Row():
        # Левая часть
        with gr.Column(scale=3):
            iface = gr.Interface(
                fn=process_api_key,
                inputs=gr.Textbox(label="API Key", type="password"),
                outputs=None,
            )
            pass
        # Центральная часть
        with gr.Column(scale=7):
            with gr.Tabs() as tabs:
                with gr.Tab("Чат 1"):
                    get_chat_interface(chat_id=0)
                with gr.Tab("Чат 2"):
                    get_chat_interface(chat_id=1)
            clear_btn = gr.Button("Очистить память")
            clear_btn.click(fn=clear_history, inputs=None, outputs=None)

            # create_btn = gr.Button("добавить")
            # create_btn.click(fn=add_table, inputs=[], outputs=)


    def on_tab_select():
        current_chat_id.value = (current_chat_id.value + 1) % 2

    tabs.select(
        fn=on_tab_select,
    )

# with gr.Blocks() as demo:
#     chatbot = gr.ChatInterface(
#         fn=chat,
#         type="messages",
#         title="Chat Bot🤖",
#     )
#     chatbot.render()
#
#     # Добавляем кнопку очистки памяти
#     with gr.Row():
#         clear_btn = gr.Button("Очистить память")
#
#     # Связываем кнопку с функцией очистки памяти
#     clear_btn.click(fn=clear_history, inputs=None, outputs=gr.Textbox(visible=False))


llm = None


def main():
    demo.queue().launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
