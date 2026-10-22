"""解析 mysqldump（Flarum 的备份格式）。

只处理我们需要的表：users / tags / discussions / posts / discussion_tag /
fof_upload_files。解析逻辑与只读版一致，独立成模块方便写单元测试。
"""
import gzip
import re

_ESC = {"0": "\0", "'": "'", '"': '"', "b": "\b", "n": "\n",
        "r": "\r", "t": "\t", "Z": "\x1a", "\\": "\\"}


def _parse_string(s: str, i: int) -> tuple[str, int]:
    quote = s[i]
    i += 1
    out: list[str] = []
    while i < len(s):
        c = s[i]
        if c == "\\":
            out.append(_ESC.get(s[i + 1], s[i + 1]))
            i += 2
        elif c == quote:
            if i + 1 < len(s) and s[i + 1] == quote:
                out.append(quote)
                i += 2
            else:
                return "".join(out), i + 1
        else:
            out.append(c)
            i += 1
    raise ValueError("未闭合的字符串")


def _parse_tuple(s: str, i: int) -> tuple[list, int]:
    i += 1
    row: list = []
    while True:
        while s[i] in " \t\r\n":
            i += 1
        if s[i] in "'\"":
            value, i = _parse_string(s, i)
        elif s[i:i + 4].upper() == "NULL":
            value, i = None, i + 4
        elif s[i:i + 2].lower() == "0x":
            j = i + 2
            while j < len(s) and s[j] in "0123456789abcdefABCDEF":
                j += 1
            value, i = f"<blob:{j - i - 2}>", j
        else:
            j = i
            while s[j] not in ",)":
                j += 1
            value, i = s[i:j].strip(), j
        row.append(value)
        while s[i] in " \t\r\n":
            i += 1
        if s[i] == ",":
            i += 1
            continue
        if s[i] == ")":
            return row, i + 1
        raise ValueError(f"意外字符 {s[i]!r}")


def parse(path: str, tables: set[str]) -> dict[str, tuple[list[str], list[list]]]:
    result: dict[str, tuple[list[str], list[list]]] = {}
    columns: dict[str, list[str]] = {}
    current: str | None = None
    in_create = False
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not in_create and line.startswith("CREATE TABLE `"):
                current = re.match(r"CREATE TABLE `([^`]+)`", line).group(1)
                columns[current] = []
                result[current] = (columns[current], [])
                in_create = True
                continue
            if in_create:
                match = re.match(r"\s+`([^`]+)`", line)
                if match:
                    columns[current].append(match.group(1))
                elif line.startswith(")"):
                    in_create = False
                continue
            if line.startswith("INSERT INTO `"):
                name = re.match(r"INSERT INTO `([^`]+)`", line).group(1)
                if name not in tables:
                    continue
                i = line.index("VALUES") + len("VALUES")
                rows = result[name][1]
                while i < len(line):
                    while i < len(line) and line[i] in " \t\r\n,":
                        i += 1
                    if i >= len(line) or line[i] == ";":
                        break
                    row, i = _parse_tuple(line, i)
                    rows.append(row)
    return {name: value for name, value in result.items() if name in tables}
