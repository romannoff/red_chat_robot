import gradio as gr
from db_handler.db_handler import Database
from langchain_openai import ChatOpenAI
from config import Config
from rag_chat import RagChat


settings = Config.from_yaml("config.yaml")

# История сообщений
db = Database(db_name=settings.db_name)

chat = RagChat(llm=None, db_name=settings.db_name, vdb_name='src/database/vector_database.sqlite')


def clear_history():
    db.clear_history(current_chat_id.value)


def get_chat_interface(chat_id):
    history = [
        {'role': msg['role'], 'metadata': None, 'content': msg['content'], 'options': None}
        for msg in db.get_history(chat_id)
    ]

    return gr.ChatInterface(
        fn=chat.get_msg,
        type="messages",
        chatbot=gr.Chatbot(value=history, type="messages"),
        # title="Chat Bot🤖",
    )


def process_api_key(api_key):
    global llm, chat
    llm = ChatOpenAI(
        model_name=settings.model_name,
        openai_api_base=settings.url,
        openai_api_key=api_key,
    )
    chat.llm = llm


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


    def on_tab_select():
        current_chat_id.value = (current_chat_id.value + 1) % 2

    tabs.select(
        fn=on_tab_select,
    )


def main():
    demo.queue().launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
