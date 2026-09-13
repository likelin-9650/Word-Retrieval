"""Word 文档单词提取应用包。"""

from pathlib import Path

from flask import Flask

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent


def create_app() -> Flask:
    """创建并配置 Flask 应用。"""
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB
    app.config["PROJECT_ROOT"] = PROJECT_ROOT
    app.config["INDEX_HTML"] = PROJECT_ROOT / "index.html"
    app.config["LEGACY_WORDS_TXT"] = PROJECT_ROOT / "words.txt"
    app.config["WORDLISTS_DIR"] = PROJECT_ROOT / "wordlists"
    # 旧 scowl 文件保留兼容；黄/红分类已改为 ECDICT
    app.config["SCOWL_WORDS"] = PROJECT_ROOT / "scowl_words.txt"
    app.config["DOWNLOAD_DIR"] = PROJECT_ROOT / ".cache" / "downloads"
    app.config["ECDICT_DB"] = PROJECT_ROOT / "dictionaries" / "ecdict.db"
    app.config["DICT_EXTRA"] = PROJECT_ROOT / "dictionaries" / "dict_extra.txt"
    app.config["DICT_EXCLUDE"] = PROJECT_ROOT / "dictionaries" / "dict_exclude.txt"
    # 此处可以改造接入百度翻译 API：
    # 若网页要改用/回退到百度翻译，可恢复类似配置：（如需该类代码请联系作者）
    #   app.config["BAIDU_SECRETS"] = PROJECT_ROOT / "baidu_translate_secrets.json"

    from word_retrieval.lexicon import ensure_dict_override_files, ensure_wordlists_dir

    ensure_wordlists_dir(
        app.config["WORDLISTS_DIR"],
        legacy_words=app.config["LEGACY_WORDS_TXT"],
    )
    ensure_dict_override_files(app.config["DICT_EXTRA"], app.config["DICT_EXCLUDE"])

    from word_retrieval.routes import bp

    app.register_blueprint(bp)
    return app
