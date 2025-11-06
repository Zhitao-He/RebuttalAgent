"""import json
import sys
from pathlib import Path

HUMAN_PATH = "human/RebuttalAgent-50.json"  # 固定的人类数据来源

def load_array(obj):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for k in ("data", "items", "records", "results"):
            v = obj.get(k)
            if isinstance(v, list):
                return v
    raise ValueError("未找到数组数据（期望顶层为数组，或在 data/items/records/results 字段中）")

def get_comment_id(item):
    # 优先 comment.comment_id；兼容顶层 comment_id
    if not isinstance(item, dict):
        return None
    c = item.get("comment")
    if isinstance(c, dict) and "comment_id" in c:
        return c["comment_id"]
    return item.get("comment_id", None)

def build_index(arr):
    index = {}
    for it in arr:
        if not isinstance(it, dict):
            continue
        pid = it.get("paper_id")
        rid = it.get("reviewer_id")
        cid = get_comment_id(it)
        if pid is None or rid is None or cid is None:
            continue
        key = (pid, rid, cid)
        # 仅在第一次遇到该 key 时记录；如需“最后一条”，改为 index[key] = it
        if key not in index:
            index[key] = it
    return index

def main(other_path, out_path):
    # 读取 human（固定路径）
    with open(HUMAN_PATH, "r", encoding="utf-8") as f:
        human_data = json.load(f)
    human_arr = human_data if isinstance(human_data, list) else load_array(human_data)

    # 读取 other 数据并建索引（无多重匹配）
    with open(other_path, "r", encoding="utf-8") as f:
        other_data = json.load(f)
    other_arr = other_data if isinstance(other_data, list) else load_array(other_data)
    idx = build_index(other_arr)

    matched = []
    missing = []

    for i, it in enumerate(human_arr):
        if not isinstance(it, dict):
            missing.append({"index": i, "reason": "not an object"})
            continue
        pid = it.get("paper_id")
        rid = it.get("reviewer_id")
        cid = get_comment_id(it)
        if pid is None or rid is None or cid is None:
            missing.append({
                "index": i,
                "reason": "missing keys",
                "paper_id": pid, "reviewer_id": rid, "comment_id": cid
            })
            continue

        key = (pid, rid, cid)
        hit = idx.get(key)
        if hit is not None:
            matched.append(hit)  # 只追加单条
        else:
            missing.append({
                "index": i,
                "paper_id": pid, "reviewer_id": rid, "comment_id": cid,
                "reason": "not found"
            })

    # 保险起见，按 (paper_id, reviewer_id, comment_id) 去重一次
    seen = set()
    dedup_matched = []
    for it in matched:
        pid = it.get("paper_id")
        rid = it.get("reviewer_id")
        cid = get_comment_id(it)
        key = (pid, rid, cid)
        if key in seen:
            continue
        seen.add(key)
        dedup_matched.append(it)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dedup_matched, f, ensure_ascii=False, indent=2)

    # 简要报告
    print(f"human 条目数: {len(human_arr)}")
    print(f"匹配成功条目: {len(dedup_matched)}")
    print(f"未匹配条目数: {len(missing)}")
    if missing:
        print("未匹配示例（最多前20条）:")
        for m in missing[:20]:
            print(m)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 ag_access.py rebuttal_agent_response/RebuttalAgent-25.json human/RebuttalAgent-25.json")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])"""

import json
import csv
import sys
from pathlib import Path

def load_array(obj):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for k in ("data", "items", "records", "results"):
            v = obj.get(k)
            if isinstance(v, list):
                return v
    raise ValueError("未找到数组数据（期望顶层为数组，或在 data/items/records/results 字段中）")

def get_val(item, path, default=""):
    cur = item
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur if cur is not None else default

def main(src_json, out_csv):
    with open(src_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    arr = data if isinstance(data, list) else load_array(data)

    # 仅导出三列
    headers = ["comment_text", "category", "response"]
    rows = []
    for it in arr:
        if not isinstance(it, dict):
            continue
        rows.append({
            "comment_text": get_val(it, ["comment", "comment_text"], ""),
            "category": get_val(it, ["comment", "category"], ""),
            "response": get_val(it, ["response"], ""),  # 如果 response 在别的位置可告知路径
        })

    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"已导出 {len(rows)} 行到 {out_csv}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 ag_access.py human/RebuttalAgent-75.json human1/RebuttalAgent-75.csv")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])