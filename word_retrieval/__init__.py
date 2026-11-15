"""Word 文档单词提取应用包。"""

from pathlib import Path

from flask import Flask

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent


def create_app() -> Flask:
    """创建并配置 Flask 应用。"""
    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="/static",
    )
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB
    app.config["PROJECT_ROOT"] = PROJECT_ROOT
    app.config["INDEX_HTML"] = PROJECT_ROOT / "index.html"
    app.config["LEGACY_WORDS_TXT"] = PROJECT_ROOT / "words.txt"
    app.config["WORDLISTS_DIR"] = PROJECT_ROOT / "wordlists"
    # 旧 scowl 文件保留兼容；黄/红分类已改为 ECDICT
    app.config["SCOWL_WORDS"] = PROJECT_ROOT / "scowl_words.txt"
    app.config["DOWNLOAD_DIR"] = PROJECT_ROOT / ".cache" / "downloads"
    app.config["SESSION_DIR"] = PROJECT_ROOT / ".cache" / "sessions"
    app.config["CACHE_MAX_AGE_SEC"] = 1800  # 30 分钟
    app.config["CACHE_MAX_SESSIONS"] = 50
    app.config["CACHE_MAX_BYTES"] = 500 * 1024 * 1024  # 500 MB
    # 资源上限（SECURITY 1.3）
    app.config["MAX_ARTICLE_CHARS"] = 200_000
    app.config["MAX_SOURCE_TEXT_CHARS"] = 500_000
    app.config["MAX_EXTRACTED_WORDS"] = 5_000
    app.config["MAX_DOCX_ENTRIES"] = 2_000
    app.config["MAX_DOCX_UNCOMPRESSED"] = 64 * 1024 * 1024  # 64 MB
    app.config["MAX_DOCX_RATIO"] = 100
    app.config["MAX_ALGO_EXPAND_WORDS"] = 20_000
    app.config["MAX_EXPAND_SEC"] = 20
    app.config["ECDICT_DB"] = PROJECT_ROOT / "dictionaries" / "ecdict.db"
    # 服务器仍可保留空覆盖文件；网页用户改动写入浏览器，不再写这些共享文件
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

    from word_retrieval.job_cache import cleanup_expired, ensure_cache_dirs

    ensure_cache_dirs(app.config["SESSION_DIR"], app.config["DOWNLOAD_DIR"])
    cleanup_expired(
        app.config["SESSION_DIR"],
        app.config["DOWNLOAD_DIR"],
        max_age_sec=app.config["CACHE_MAX_AGE_SEC"],
    )

    from word_retrieval.routes import bp

    app.register_blueprint(bp)
    return app
