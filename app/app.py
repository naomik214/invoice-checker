from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

import base64

from parser import extract_text
from comparator import compare_pair

app = FastAPI()

# ✅ テンプレートパス（Docker対応）
templates = Jinja2Templates(directory="templates")


# ====================================
# ✅ BASIC認証（全リクエスト対象）
# ====================================
USERNAME = "keiri1"
PASSWORD = "7y.ueJZ7rP"

@app.middleware("http")
async def basic_auth(request: Request, call_next):

    auth = request.headers.get("Authorization")

    if auth is None:
        return Response(
            status_code=401,
            headers={"WWW-Authenticate": "Basic"}
        )

    try:
        scheme, credentials = auth.split()
        decoded = base64.b64decode(credentials).decode("utf-8")
        username, password = decoded.split(":")
    except:
        return Response(
            status_code=401,
            headers={"WWW-Authenticate": "Basic"}
        )

    if username != USERNAME or password != PASSWORD:
        return Response(
            status_code=401,
            headers={"WWW-Authenticate": "Basic"}
        )

    return await call_next(request)


# ====================================
# ✅ 画面表示
# ====================================
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ====================================
# ✅ 比較処理
# ====================================
@app.post("/compare")
async def compare(
    request: Request,
    q1: UploadFile = File(...),
    i1: UploadFile = File(...),
    q2: UploadFile = File(None),
    i2: UploadFile = File(None),
    q3: UploadFile = File(None),
    i3: UploadFile = File(None),
    q4: UploadFile = File(None),
    i4: UploadFile = File(None),
    q5: UploadFile = File(None),
    i5: UploadFile = File(None),
):

    pairs = [
        (q1, i1),
        (q2, i2),
        (q3, i3),
        (q4, i4),
        (q5, i5),
    ]

    all_results = []

    for idx, (q_file, i_file) in enumerate(pairs):

        if q_file and i_file:
            q_bytes = await q_file.read()
            i_bytes = await i_file.read()

        # ✅ 空ファイル対策
        if not q_bytes or not i_bytes:
            continue

        try:
            # ✅ PDF読み取り
            q_text = extract_text(q_bytes)
            i_text = extract_text(i_bytes)

            # ✅ ペア番号付きで呼ぶ
            result = compare_pair(q_text, i_text, idx + 1)
            all_results.append(result)

        except Exception as e:
            print("PDFエラー:", e)

            # ✅ エラーでも結果を返す（ここ重要）
            all_results.append({
                "pair": idx + 1,
                "status": "NG",
                "items": [],
                "reason": "PDF読込エラー"
            })

            continue
    
    return {"results": all_results}
