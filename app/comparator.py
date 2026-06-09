import re


def normalize(s):
    if not s:
        return ""

    s = s.lower()

    # 記号削除
    s = s.replace("→", "")
    s = s.replace("＆", "")
    s = s.replace("&", "")

    s = re.sub(r"\s+", "", s)

    # 型番削除
    s = re.sub(r"ps-exglm-[\w-]+", "", s)

    # 余計な記号
    s = re.sub(r"[（）()・/]", "", s)

    return s


def extract_company(name):
    if not name:
        return ""

    name = re.sub(r"御中.*", "", name)
    name = re.sub(r"No\..*", "", name)
    name = re.sub(r"見積番号.*", "", name)
    name = re.sub(r"[：:]\s*\w+", "", name)
    name = re.sub(r"\s+", "", name)

    return name.strip()


def compare_pair(q_text, i_text, pair_no):

    from parser import parse_items, parse_basic

    q_items = parse_items(q_text) or []
    i_items = parse_items(i_text) or []

    q_basic = parse_basic(q_text)
    i_basic = parse_basic(i_text)

    results = []

    # ✅ 合計金額
    results.append({
        "name": "合計金額",
        "status": "OK" if q_basic["total"] == i_basic["total"] else "NG",
        "reason": "" if q_basic["total"] == i_basic["total"] else "不一致",
        "q_qty": "-",
        "i_qty": "-",
        "q_price": "-",
        "i_price": "-",
        "q_amount": q_basic["total"],
        "i_amount": i_basic["total"]
    })

    # ✅ 消費税（数量比較しない）
    results.append({
        "name": "消費税",
        "status": "OK" if q_basic["tax"] == i_basic["tax"] else "NG",
        "reason": "" if q_basic["tax"] == i_basic["tax"] else "不一致",
        "q_qty": "-",
        "i_qty": "-",
        "q_price": "-",
        "i_price": "-",
        "q_amount": q_basic["tax"],
        "i_amount": i_basic["tax"]
    })

    # ✅ 宛先
    q_c = extract_company(q_basic["customer"])
    i_c = extract_company(i_basic["customer"])

    status = "OK" if q_c in i_c or i_c in q_c else "NG"

    results.append({
        "name": "宛先",
        "status": status,
        "reason": "" if status == "OK" else "不一致",
        "q_qty": q_basic["customer"],
        "i_qty": i_basic["customer"],
        "q_price": "-",
        "i_price": "-",
        "q_amount": "-",
        "i_amount": "-"
    })

    # ✅ 明細比較（点数方式）
    used = set()

    for q in q_items:

        qn = normalize(q["name"])

        best_match = None
        best_score = 0

        for idx, i in enumerate(i_items):

            if idx in used:
                continue

            iname = normalize(i["name"])

            score = 0

            # 名前一致が最重要
            if qn in iname or iname in qn:
                score += 5
            
            # 数量一致
            if q["qty"] == i["qty"]:
                score += 3

            # 長さが近い
            #if abs(len(qn) - len(iname)) < 10:
                #score += 1

            # 単価一致
            if q["unit_price"] == i["unit_price"]:
                score += 2

            if score > best_score:
                best_score = score
                best_match = (idx, i)

        if best_match and best_score >= 5:
            idx, i = best_match
            used.add(idx)

            status = "OK"
            reason = ""

            if q["qty"] != i["qty"]:
                status = "NG"
                reason = "数量"
            elif q["unit_price"] != i["unit_price"]:
                status = "NG"
                reason = "単価"
            elif q["amount"] != i["amount"]:
                status = "NG"
                reason = "金額"

            results.append({
                "name": q["name"],
                "status": status,
                "reason": reason,
                "q_qty": q["qty"],
                "i_qty": i["qty"],
                "q_price": q["unit_price"],
                "i_price": i["unit_price"],
                "q_amount": q["amount"],
                "i_amount": i["amount"]
            })

        else:
            results.append({
                "name": q["name"],
                "status": "NG",
                "reason": "請求に存在しない",
                "q_qty": q["qty"],
                "i_qty": "-",
                "q_price": q["unit_price"],
                "i_price": "-",
                "q_amount": q["amount"],
                "i_amount": "-"
            })

    # ① 明細NGがあればNG
    for item in results:
        if item["status"] != "OK":
            status = "NG"
            break

    # ② 合計＋税が一致ならOKに上書き
    total_match = False
    tax_match = False
    tax_found = False

    for item in results:
        if "合計" in item["name"]:
            if item["status"] == "OK":
                total_match = True

        if "消費税" in item["name"]:
            if item["status"] == "OK":
                tax_match = True

    if total_match and (not tax_found or tax_match):
        status = "OK"

    # ③ return
    return {
        "pair": pair_no,
        "status": status,
        "items": results
    }
