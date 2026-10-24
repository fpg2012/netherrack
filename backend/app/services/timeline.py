"""讨论内的操作记录：写库（record）和渲染成一句人话（event_text）。

payload 的格式沿用 Flarum 迁移数据的样子，这样从旧站导进来的事件和新产生的
事件共用同一套文案：

    discussionRenamed     [旧标题, 新标题]
    discussionTagged      [旧标签 id 列表, 新标签 id 列表]
    discussionStickied    {"sticky": bool}
    discussionLocked      {"locked": bool}
    discussionCollapsed   {"collapsed": bool}
    discussionVisibility  {"is_public": bool}
    discussionBestAnswer  {"post_number": int}
    postCollapsed         {"post_number": int, "collapsed": bool}
    recipientsModified    {"old": {...}, "new": {...}}   Flarum 私有讨论
    recipientLeft         Flarum 私有讨论

早期版本写进库里的 {"old"/"new"}、{"added"/"removed"} 形态仍然能读，见下面
的 _rename_pair / _tag_diff。
"""
from typing import Any

from app.models import DiscussionEvent


def record(session, *, discussion_id: int, actor_id: int | None, kind: str,
           payload: Any) -> None:
    session.add(DiscussionEvent(
        discussion_id=discussion_id, actor_id=actor_id, kind=kind, payload=payload,
    ))


def _flag(payload: object, key: str) -> bool:
    return bool(payload.get(key)) if isinstance(payload, dict) else False


def _number(payload: object) -> object:
    return payload.get("post_number") if isinstance(payload, dict) else None


def _rename_pair(payload: object) -> tuple[str, str]:
    if isinstance(payload, dict):  # 早期版本写的是 {"old": ..., "new": ...}
        return str(payload.get("old") or ""), str(payload.get("new") or "")
    values = list(payload) if isinstance(payload, list) else []
    old, new = (values + ["", ""])[:2]
    return str(old or ""), str(new or "")


def _tag_diff(payload: object) -> tuple[list[int], list[int]]:
    if isinstance(payload, dict):  # 早期版本写的是 {"added": [...], "removed": [...]}
        return list(payload.get("added") or []), list(payload.get("removed") or [])
    values = list(payload) if isinstance(payload, list) else []
    old, new = (values + [[], []])[:2]
    old, new = list(old or []), list(new or [])
    return [t for t in new if t not in old], [t for t in old if t not in new]


def _tag_names(ids: list[int], tag_names: dict[int, str]) -> str:
    return "、".join(tag_names.get(i, str(i)) for i in ids)


def event_text(kind: str, payload: object, who: str, tag_names: dict[int, str]) -> str:
    if kind == "discussionRenamed":
        old, new = _rename_pair(payload)
        return f"{who} 将标题从「{old}」改为「{new}」"
    if kind == "discussionTagged":
        added, removed = _tag_diff(payload)
        parts = []
        if added:
            parts.append("添加标签 " + _tag_names(added, tag_names))
        if removed:
            parts.append("移除标签 " + _tag_names(removed, tag_names))
        return f"{who} " + "，".join(parts) if parts else f"{who} 修改了标签"
    if kind == "discussionStickied":
        return f"{who} {'置顶' if _flag(payload, 'sticky') else '取消置顶'}了该讨论"
    if kind == "discussionLocked":
        return f"{who} {'锁定' if _flag(payload, 'locked') else '解锁'}了该讨论"
    if kind == "discussionCollapsed":
        return f"{who} {'折叠' if _flag(payload, 'collapsed') else '取消折叠'}了该讨论"
    if kind == "discussionVisibility":
        return f"{who} 将该讨论设为{'公开' if _flag(payload, 'is_public') else '私密'}"
    if kind == "discussionBestAnswer":
        return f"{who} 将 #{_number(payload)} 楼设为最佳回复"
    if kind == "postCollapsed":
        if _flag(payload, "collapsed"):
            return f"{who} 折叠了 #{_number(payload)} 楼"
        return f"{who} 取消了 #{_number(payload)} 楼的折叠"
    if kind == "recipientsModified":
        return f"{who} 修改了参与者"
    if kind == "recipientLeft":
        return f"{who} 退出了该讨论"
    return f"{who} {kind}"
