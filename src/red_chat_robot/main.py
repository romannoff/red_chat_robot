import gradio as gr
from db_handler.db_handler import Database
from langchain_openai import ChatOpenAI
from config import Config
from rag_chat import RagChat
from simple_chat import SimpleChat


settings = Config.from_yaml("config.yaml")

# История сообщений
db = Database(db_name=settings.db_name)

llm = None
rag_chat = RagChat(llm=llm, db_name=settings.db_name, vdb_name='src/database/vector_database.sqlite')
simple_chat = SimpleChat(llm, settings.db_name)


def clear_history():
    db.clear_history(current_chat_id.value)


def main_chat(msg, history):
    if checkbox.value:
        return rag_chat.get_msg(msg, history)
    else:
        return simple_chat.get_msg(msg, history)


def get_chat_interface(chat_id):
    history = [
        {'role': msg['role'], 'metadata': None, 'content': msg['content'], 'options': None}
        for msg in db.get_history(chat_id)
    ]

    # for r in history:
    #     print(r)

    return gr.ChatInterface(
        fn=main_chat,
        type="messages",
        chatbot=gr.Chatbot(value=history, type="messages"),
        # title="Chat Bot🤖",
    )


current_chat_id = gr.State(value=0)

with gr.Blocks() as demo:
    with gr.Row():
        gr.Markdown("# <center> Чат с LLM 🤖 </center>")
    with gr.Row():

        # Левая часть
        with gr.Column(scale=3):
            api_input = gr.Textbox(label="API Key", type="password")

            with gr.Row():
                with gr.Column():
                    clear_btn = gr.Button("Очистить")
                with gr.Column():
                    submit_btn = gr.Button("Ввод API")

            checkbox = gr.Checkbox(label="Использовать базу знаний", value=True)

        # Центральная часть
        with gr.Column(scale=7, visible=False) as right_bar:
            with gr.Tabs() as tabs:
                with gr.Tab("Чат 1"):
                    get_chat_interface(chat_id=0)
                with gr.Tab("Чат 2"):
                    get_chat_interface(chat_id=1)
            clear_memory_btn = gr.Button("Очистить память")
            gr.Markdown("💡 *Если очищать память агента после смены темы разговора, то качество ответов увеличится*")
            clear_memory_btn.click(fn=clear_history, inputs=None, outputs=None)

        def on_tab_select():
            current_chat_id.value = (current_chat_id.value + 1) % 2

        def click_checkbox(value):
            checkbox.value = value
            return value

        def process_api_key(api_key):
            global llm
            llm = ChatOpenAI(
                model_name=settings.model_name,
                openai_api_base=settings.url,
                openai_api_key=api_key,
            )
            rag_chat.llm = llm
            simple_chat.llm = llm
            gr.Info("API ключ введён!")
            return {api_input: '', right_bar: gr.Column(scale=7, visible=True)}

        tabs.select(
            fn=on_tab_select,
        )
        checkbox.change(
            fn=click_checkbox,
            inputs=[checkbox],
            outputs=[checkbox]
        )
        submit_btn.click(
            fn=process_api_key,
            inputs=api_input,
            outputs=[api_input, right_bar],
        )

        clear_btn.click(
            fn=lambda: "",
            inputs=None,
            outputs=api_input
        )


def main():
    demo.queue().launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
