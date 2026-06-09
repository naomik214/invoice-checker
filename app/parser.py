import pdfplumber
import re
from io import BytesIO


def extract_text(file_bytes):
    text = ""
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return text


# ✅ 明細抽出（安定版）
def parse_items(text):
    import re

    items = []

    lines = text.split("\n")

    # ✅ ★ 行結合（ここ重要）
    merged_lines = []
    i = 0

    while i < len(lines):

        line = lines[i].strip()

        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()

            # ✅ 数字だけの行なら結合
            if re.match(r"^\d+$", next_line):
                line = line + " " + next_line
                i += 1

        merged_lines.append(line)
        i += 1

    lines = merged_lines

    # ✅ 通常処理
    for line in lines:

        if "合計" in line:
            continue
        if "消費税" in line:
            continue
        if "御中" in line:
            continue

    # ↓ 既存処理
    # 明細として処理するロジック

        line = line.strip()
        if not line:
            continue

        # ✅ 金額行のみ
        # ✅ 金額が無くても、数量行は通す
        if "¥" not in line and "￥" not in line:
            if not re.search(r"\d+", line):
                continue       

        # ✅ 金額抽出
        prices = re.findall(r"[¥￥]\s*([\d,]+)", line)
        if not prices:
            continue

        try:
            prices_int = [int(p.replace(",", "")) for p in prices]

            amount = prices_int[-1]
            unit_price = prices_int[-2] if len(prices_int) >= 2 else amount

            # ✅ 数値取得
            nums = re.findall(r"\d+", line)
            if len(nums) < 2:
                continue

            nums_int = [int(n) for n in nums]

            qty_candidates = [n for n in nums_int if 1 <= n <= 10]
            qty = qty_candidates[-1] if qty_candidates else 1

            # ✅ 名前
            name = re.split(r"[¥￥]", line)[0].strip()

            # ✅ ノイズ除外
            if any(k in name for k in [
                "合計", "消費税", "小計", "税込",
                "税", "総計", "ID数"
            ]):
                continue

            if len(name) < 5:
                continue

            items.append({
                "name": name,
                "qty": qty,
                "unit_price": unit_price,
                "amount": amount
            })

        except:
            continue

    # ✅ fallback
    if len(items) == 0:
        for line in lines:
            if "¥" in line or "￥" in line:
                name = re.split(r"[¥￥]", line)[0].strip()

                if len(name) < 5:
                    continue

                items.append({
                    "name": name,
                    "qty": 1,
                    "unit_price": 0,
                    "amount": 0
                })

    # ✅ 重複除去
    unique = {}
    for item in items:
        if item["name"] not in unique:
            unique[item["name"]] = item

    items = list(unique.values())

    # ✅ ソート（安定化）
    items = sorted(items, key=lambda x: x["name"])

    return items

# ✅ 基本情報（合計・税・宛先）
def parse_basic(text):

    # ✅ 合計金額（最後の金額）
    amounts = re.findall(r"[¥￥]\s*([\d,]+)", text)
    total = int(amounts[-1].replace(",", "")) if amounts else 0

    # ✅ 税金（強化版）
    tax_candidates = re.findall(r"[¥￥]\s*([\d,]+)", text)

    tax = 0
    if len(tax_candidates) >= 2:
        tax = int(tax_candidates[-2].replace(",", ""))
        
    # ✅ 宛先
    customer = ""
    for line in text.split("\n"):
        if "御中" in line:
            customer = line.strip()
            break

    return {
        "total": total,
        "tax": tax,
        "customer": customer
    }

def parse_total(text):

    import re

    amounts = re.findall(r"[¥￥]\s*([\d,]+)", text)
    if amounts:
        return int(amounts[-1].replace(",", ""))

    return 0
