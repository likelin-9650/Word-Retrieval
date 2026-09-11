"""启动 Word 单词提取服务。"""

from word_retrieval import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
