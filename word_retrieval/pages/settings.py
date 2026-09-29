"""设置页面：对照表/词典改动写入本浏览器（方案 A）。"""

from __future__ import annotations

import html
import json

from flask import url_for

from word_retrieval.pages import ICP_FOOTER_CSS, icp_footer_html


def render_settings_page(
    *,
    baseline_wordlists: list[str],
) -> str:
    home = url_for("main.index")
    parse_api = url_for("main.api_parse_wordlist")
    static_js = url_for("static", filename="user_data.js")
    baseline_json = json.dumps(baseline_wordlists, ensure_ascii=False)
    footer = icp_footer_html()

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>设置</title>
  <style>
    :root {{
      --bg-top: #e8f0f4;
      --bg-bottom: #f7f3ec;
      --ink: #1c2a32;
      --muted: #5a6b75;
      --accent: #0f6a5c;
      --accent-hover: #0b5449;
      --line: #c5d2da;
      --surface: rgba(255, 255, 255, 0.72);
      --danger: #c62828;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; min-height: 100vh;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 12% 18%, rgba(15, 106, 92, 0.12), transparent 42%),
        linear-gradient(165deg, var(--bg-top), var(--bg-bottom));
      padding: 2rem 1rem 3rem;
    }}
    main {{ width: min(760px, 100%); margin: 0 auto; }}
    h1 {{ margin: 0 0 0.4rem; }}
    h2 {{ margin: 0 0 0.7rem; font-size: 1.05rem; }}
    .meta {{ color: var(--muted); margin: 0 0 1rem; line-height: 1.5; }}
    a {{ color: var(--accent); font-weight: 600; text-decoration: none; }}
    .panel {{
      background: var(--surface); border: 1px solid var(--line);
      padding: 1.1rem 1.2rem; margin-bottom: 1rem;
    }}
    label {{ display: block; font-weight: 600; margin: 0.5rem 0 0.35rem; }}
    input[type="text"], input[type="file"], select, textarea {{
      width: 100%; padding: 0.7rem; border: 1px solid var(--line);
      font: inherit; background: #fff;
    }}
    input[type="file"] {{ border-style: dashed; }}
    textarea {{ min-height: 110px; resize: vertical; }}
    .hint {{ color: var(--muted); font-size: 0.88rem; margin: 0.35rem 0 0.7rem; line-height: 1.45; }}
    .req {{
      background: rgba(28, 77, 110, 0.06); border: 1px solid var(--line);
      padding: 0.75rem 0.9rem; margin: 0.5rem 0 0.9rem; font-size: 0.88rem;
      color: var(--muted); line-height: 1.5;
    }}
    .req strong {{ color: var(--ink); }}
    .row {{ display: flex; flex-wrap: wrap; gap: 0.6rem; margin-top: 0.7rem; align-items: center; }}
    .check {{
      display: flex; align-items: center; gap: 0.45rem; font-weight: 600; margin: 0.6rem 0;
    }}
    .check input {{ width: auto; }}
    button, .btn {{
      appearance: none; border: 0; background: var(--accent); color: #fff;
      font: inherit; font-weight: 600; padding: 0.7rem 1rem; cursor: pointer;
    }}
    button:hover {{ background: var(--accent-hover); }}
    button.danger {{ background: var(--danger); }}
    button.secondary {{ background: #1c4d6e; }}
    button.secondary:hover {{ background: #163d57; }}
    .ok {{ color: var(--accent); }}
    .error {{ color: var(--danger); }}
    #statusLine {{ min-height: 1.4em; }}
{ICP_FOOTER_CSS}
  </style>
</head>
<body>
  <main>
    <h1>设置</h1>
    <p class="meta">
      服务器保留基准 <strong>ECDICT</strong> 与默认对照表；
      你在本页的增删、自建对照表只保存在<strong>当前浏览器</strong>（localStorage）。
      换设备或清除站点数据会丢失，可用下方导出备份。
    </p>
    <p class="meta"><a href="{home}">← 返回首页</a></p>
    <p class="meta" id="summary"></p>
    <p id="statusLine" class="meta"></p>

    <section class="panel">
      <h2>编辑大词典覆盖（本机）</h2>
      <p class="hint">
        基础词表为服务器 ECDICT。「添加」写入本机增补；「排除」写入本机排除表。
      </p>
      <label for="dict_add">添加单词（每行一个）</label>
      <textarea id="dict_add" placeholder="apple&#10;banana"></textarea>
      <label for="dict_remove">排除单词（每行一个）</label>
      <textarea id="dict_remove" placeholder="obsoleteword"></textarea>
      <div class="row"><button type="button" id="btnDict">更新本机词典覆盖</button></div>
    </section>

    <section class="panel">
      <h2>编辑对照表（本机差分）</h2>
      <p class="hint">对服务器基准表的修改记为差分；自建表直接改本机全文。</p>
      <label for="wordlist">选择对照表</label>
      <select id="wordlist"></select>
      <label for="list_add">添加单词（每行一个）</label>
      <textarea id="list_add"></textarea>
      <label for="list_remove">删除单词（每行一个）</label>
      <textarea id="list_remove"></textarea>
      <div class="row"><button type="button" id="btnWordlist">更新本机对照表</button></div>
    </section>

    <section class="panel">
      <h2>新建空对照表（本机）</h2>
      <label for="new_list">名称</label>
      <input id="new_list" type="text" placeholder="例如 cet4 或 考研词汇" />
      <p class="hint">只保存在本浏览器，不会写入服务器 wordlists/。</p>
      <div class="row"><button type="button" id="btnCreate">创建空对照表</button></div>
    </section>

    <section class="panel">
      <h2>上传 .txt 创建对照表（本机）</h2>
      <div class="req">
        <strong>文件格式与排版要求：</strong><br />
        1. 扩展名必须为 <strong>.txt</strong>；编码推荐 <strong>UTF-8</strong>（也支持带 BOM 的 UTF-8、GBK）。<br />
        2. <strong>一行一个英语单词</strong>；允许空行。<br />
        3. 字母词、撇号缩写或序数缩写；大小不超过 <strong>5 MB</strong>。<br />
        4. 服务器仅负责校验（及可选派生词扩展），词表仍写入本浏览器。
      </div>
      <label for="upload_name">对照表名称</label>
      <input id="upload_name" type="text" placeholder="例如 my_vocab" />
      <label for="wordlist_file">选择 .txt 文件</label>
      <input id="wordlist_file" type="file" accept=".txt,text/plain" />
      <label class="check">
        <input type="checkbox" id="add_inflections" value="1" />
        添加派生词（屈折变化，由服务器用 lemminflect 扩展）
      </label>
      <div class="row"><button type="button" id="btnUpload">上传并保存到本机</button></div>
    </section>

    <section class="panel">
      <h2>删除本机自建对照表</h2>
      <label for="del_list">选择对照表</label>
      <select id="del_list"></select>
      <p class="hint">只能删除本机自建表；服务器基准表（如 words.txt）不可删，但可用上方差分剔除单词。</p>
      <div class="row"><button class="danger" type="button" id="btnDelete">删除本机对照表</button></div>
    </section>

    <section class="panel">
      <h2>备份与清除</h2>
      <p class="hint">导出 JSON 便于换浏览器恢复；清除后将回到仅使用服务器基准数据。</p>
      <div class="row">
        <button class="secondary" type="button" id="btnExport">导出本机数据</button>
        <button class="secondary" type="button" id="btnImport">导入本机数据</button>
        <input id="import_file" type="file" accept="application/json,.json" hidden />
        <button class="danger" type="button" id="btnClear">清除本机全部改动</button>
      </div>
    </section>
  </main>
  {footer}
  <script type="application/json" id="baseline-wordlists">{html.escape(baseline_json)}</script>
  <script src="{static_js}"></script>
  <script>
    const PARSE_API = {json.dumps(parse_api)};
    const baselineEl = document.getElementById("baseline-wordlists");
    const BASELINE = JSON.parse(baselineEl.textContent || "[]");
    const statusLine = document.getElementById("statusLine");
    const summary = document.getElementById("summary");

    function setStatus(msg, isError) {{
      statusLine.textContent = msg || "";
      statusLine.className = isError ? "error" : "ok";
    }}

    function parseLines(text) {{
      return UserDataStore.normalizeWords(
        String(text || "").replace(/,/g, "\\n").split(/\\r?\\n/)
      );
    }}

    function refresh() {{
      summary.textContent = UserDataStore.summaryText();
      UserDataStore.mergeWordlistOptions(
        document.getElementById("wordlist"),
        BASELINE
      );
      const data = UserDataStore.load();
      const del = document.getElementById("del_list");
      del.innerHTML = "";
      const customs = Object.keys(data.custom_lists).sort();
      if (!customs.length) {{
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "（暂无本机自建表）";
        del.appendChild(opt);
      }} else {{
        customs.forEach((name) => {{
          const opt = document.createElement("option");
          opt.value = name;
          opt.textContent = name;
          del.appendChild(opt);
        }});
      }}
    }}

    function ensureName(raw) {{
      let name = String(raw || "").trim();
      if (!name) throw new Error("请填写对照表名称。");
      if (name.toLowerCase().endsWith(".txt")) name = name.slice(0, -4);
      if (!/^[A-Za-z0-9_\\-\\u4e00-\\u9fff]{{1,64}}$/.test(name)) {{
        throw new Error("对照表名称仅允许中英文、数字、下划线和短横线，最长 64。");
      }}
      return name + ".txt";
    }}

    document.getElementById("btnDict").addEventListener("click", () => {{
      try {{
        const data = UserDataStore.load();
        const add = new Set(parseLines(document.getElementById("dict_add").value));
        const remove = new Set(parseLines(document.getElementById("dict_remove").value));
        const extra = new Set(data.dict_extra);
        const exclude = new Set(data.dict_exclude);
        let added = 0, excluded = 0;
        add.forEach((w) => {{
          if (!extra.has(w)) added += 1;
          extra.add(w);
          exclude.delete(w);
        }});
        remove.forEach((w) => {{
          extra.delete(w);
          if (!exclude.has(w)) excluded += 1;
          exclude.add(w);
        }});
        data.dict_extra = Array.from(extra).sort();
        data.dict_exclude = Array.from(exclude).sort();
        UserDataStore.save(data);
        document.getElementById("dict_add").value = "";
        document.getElementById("dict_remove").value = "";
        setStatus(`本机词典覆盖已更新：增补 ${{added}}，排除 ${{excluded}}。`);
        refresh();
      }} catch (err) {{
        setStatus(String(err.message || err), true);
      }}
    }});

    document.getElementById("btnWordlist").addEventListener("click", () => {{
      try {{
        const data = UserDataStore.load();
        const name = UserDataStore.safeListName(
          document.getElementById("wordlist").value
        );
        if (!name) throw new Error("请选择对照表。");
        const add = parseLines(document.getElementById("list_add").value);
        const remove = parseLines(document.getElementById("list_remove").value);
        let added = 0, removed = 0;
        if (Object.prototype.hasOwnProperty.call(data.custom_lists, name)) {{
          const set = new Set(data.custom_lists[name]);
          add.forEach((w) => {{ if (!set.has(w)) {{ set.add(w); added += 1; }} }});
          remove.forEach((w) => {{ if (set.delete(w)) removed += 1; }});
          data.custom_lists[name] = Array.from(set).sort();
        }} else {{
          if (!data.patches[name]) data.patches[name] = {{ add: [], remove: [] }};
          const addSet = new Set(data.patches[name].add);
          const remSet = new Set(data.patches[name].remove);
          add.forEach((w) => {{
            if (!addSet.has(w)) added += 1;
            addSet.add(w);
            remSet.delete(w);
          }});
          remove.forEach((w) => {{
            const fromAdd = addSet.delete(w);
            if (!fromAdd && !remSet.has(w)) removed += 1;
            else if (fromAdd) removed += 1;
            remSet.add(w);
          }});
          data.patches[name] = {{
            add: Array.from(addSet).sort(),
            remove: Array.from(remSet).sort(),
          }};
        }}
        UserDataStore.save(data);
        UserDataStore.setSelected(name);
        document.getElementById("list_add").value = "";
        document.getElementById("list_remove").value = "";
        setStatus(`本机对照表 ${{name}} 已更新：新增 ${{added}}，删除 ${{removed}}。`);
        refresh();
      }} catch (err) {{
        setStatus(String(err.message || err), true);
      }}
    }});

    document.getElementById("btnCreate").addEventListener("click", () => {{
      try {{
        const key = ensureName(document.getElementById("new_list").value);
        const data = UserDataStore.load();
        if (BASELINE.includes(key) || data.custom_lists[key]) {{
          throw new Error("对照表已存在：" + key);
        }}
        data.custom_lists[key] = [];
        UserDataStore.save(data);
        UserDataStore.setSelected(key);
        document.getElementById("new_list").value = "";
        setStatus("已在本机创建空对照表：" + key);
        refresh();
      }} catch (err) {{
        setStatus(String(err.message || err), true);
      }}
    }});

    document.getElementById("btnUpload").addEventListener("click", async () => {{
      try {{
        const key = ensureName(document.getElementById("upload_name").value);
        const fileInput = document.getElementById("wordlist_file");
        if (!fileInput.files || !fileInput.files[0]) {{
          throw new Error("请选择 .txt 文件。");
        }}
        const data = UserDataStore.load();
        if (BASELINE.includes(key) || data.custom_lists[key]) {{
          throw new Error("对照表已存在：" + key);
        }}
        const fd = new FormData();
        fd.append("wordlist_file", fileInput.files[0]);
        if (document.getElementById("add_inflections").checked) {{
          fd.append("add_inflections", "1");
        }}
        setStatus("正在校验…");
        const resp = await fetch(PARSE_API, {{ method: "POST", body: fd }});
        const body = await resp.json();
        if (!body.ok) throw new Error(body.error || "上传失败");
        data.custom_lists[key] = body.words || [];
        UserDataStore.save(data);
        UserDataStore.setSelected(key);
        document.getElementById("upload_name").value = "";
        fileInput.value = "";
        const msg = body.with_inflections
          ? `已保存到本机 ${{key}}：原词 ${{body.base_count}}，含派生共 ${{body.total_count}}。`
          : `已保存到本机 ${{key}}：导入 ${{body.base_count}} 个单词。`;
        setStatus(msg);
        refresh();
      }} catch (err) {{
        setStatus(String(err.message || err), true);
      }}
    }});

    document.getElementById("btnDelete").addEventListener("click", () => {{
      try {{
        const name = document.getElementById("del_list").value;
        if (!name) throw new Error("没有可删除的本机自建表。");
        if (!confirm("确定删除本机对照表 " + name + "？")) return;
        const data = UserDataStore.load();
        if (!data.custom_lists[name]) {{
          throw new Error("只能删除本机自建对照表。");
        }}
        delete data.custom_lists[name];
        UserDataStore.save(data);
        setStatus("已删除本机对照表：" + name);
        refresh();
      }} catch (err) {{
        setStatus(String(err.message || err), true);
      }}
    }});

    document.getElementById("btnExport").addEventListener("click", () => {{
      const blob = new Blob([UserDataStore.dump()], {{ type: "application/json" }});
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "word-retrieval-user-data.json";
      a.click();
      URL.revokeObjectURL(a.href);
      setStatus("已导出本机数据。");
    }});

    document.getElementById("btnImport").addEventListener("click", () => {{
      document.getElementById("import_file").click();
    }});

    document.getElementById("import_file").addEventListener("change", async (ev) => {{
      try {{
        const file = ev.target.files && ev.target.files[0];
        if (!file) return;
        const text = await file.text();
        const parsed = JSON.parse(text);
        UserDataStore.replaceAll(parsed);
        setStatus("已导入本机数据。");
        refresh();
      }} catch (err) {{
        setStatus("导入失败：" + (err.message || err), true);
      }} finally {{
        ev.target.value = "";
      }}
    }});

    document.getElementById("btnClear").addEventListener("click", () => {{
      if (!confirm("确定清除本浏览器中全部对照表差分、自建表与词典覆盖？")) return;
      UserDataStore.clear();
      setStatus("已清除本机全部改动。");
      refresh();
    }});

    refresh();
  </script>
</body>
</html>
"""
