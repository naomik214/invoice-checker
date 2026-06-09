import pdfplumber
import re
from io import BytesIO


def extract_text(file_bytes):
    text = ""
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return text


def parse_items(text):

    items = []
    lines = text.split("\n")

    buffer = ""

    for line in lines:

        line = line.strip()
        if not line:
            continue

        buffer += " " + line

        # 金額が出たら1明細として確定
        if "¥" in line or "￥" in line:

            prices = re.findall(r"[¥￥]\s*([\d,]+)", buffer)
            if not prices:
                buffer = ""
                continue

            try:
                prices_int = [int(p.replace(",", "")) for p in prices]

                amount = prices_int[-1]
                unit_price = prices_int[-2] if len(prices_int) >= 2 else amount

                nums = re.findall(r"\d+", buffer)
                nums_int = [int(n) for n in nums]

                qty_candidates = [n for n in nums_int if 1 <= n <= 10]
                qty = qty_candidates[-1] if qty_candidates else 1

                name = re.sub(r"[¥￥].*", "", buffer).strip()

                # ゴミ除外
                if "合計" in name or "消費税" in name or "ID数" in name:
                    buffer = ""
                    continue

                if len(name) < 5:
                    buffer = ""
                    continue

                items.append({
                    "name": name,
                    "qty": qty,
                    "unit_price": unit_price,
                    "amount": amount
                })

            except:
                pass

            buffer = ""

    return items


def parse_total(text):

    match = re.search(r"(合計|請求|税込).*?[¥￥]\s*([\d,]+)", text, re.DOTALL)
    if match:
        return int(match.group(2).replace(",", ""))

    amounts = re.findall(r"[¥￥]\s*([\d,]+)", text)
    if amounts:
        return int(amounts[-1].replace(",", ""))

    return 0