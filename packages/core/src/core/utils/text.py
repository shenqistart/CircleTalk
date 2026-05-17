"""文本处理工具模块，封装通用文本操作，如分词等。"""

import re
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources is deprecated.*")
    import jieba

_FTS_STOPWORDS = {
    "的",
    "了",
    "和",
    "与",
    "及",
    "或",
    "在",
    "是",
    "就",
    "都",
    "而",
    "及其",
    "以及",
    "一个",
    "一些",
    "这个",
    "那个",
}


def _dedup_keep_order(tokens: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        deduped.append(token)
    return deduped


def tokenize_for_fts(text: str) -> str:
    """
    使用 jieba 对文本进行分词，并进行清洗，为全文搜索（FTS）做准备。

    返回一个用空格分隔的、只包含有效词语的字符串。
    """
    if not text:
        return ""
    cleaned_text = re.sub("[^\\u4e00-\\u9fa5a-zA-Z0-9]", " ", text)
    seg_result = jieba.cut_for_search(cleaned_text)
    seg_list: list[str] = [str(token).strip() for token in seg_result if str(token).strip()]
    filtered_tokens: list[str] = [token for token in seg_list if len(token) > 1 and token not in _FTS_STOPWORDS]
    filtered_tokens = _dedup_keep_order(filtered_tokens)
    return " ".join(filtered_tokens)
