import sqlite3
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


# 데이터베이스 초기화 함수
def init_db():
    conn = sqlite3.connect("hotdeal.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            barcode TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            hotdeal_price INTEGER NOT NULL,
            normal_price INTEGER
        )
    """
    )
    # 테스트용 샘플 데이터 (농심 햇반 바코드)
    cursor.execute(
        "INSERT OR IGNORE INTO products VALUES ('8801045291313', '햇반 210g', 900, 1300)"
    )
    conn.commit()
    conn.close()


# ★ 중요: 클라우드(Gunicorn) 환경에서도 무조건 데이터베이스가 먼저 생성되도록 위치 변경!
init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scan/<barcode>", methods=["GET", "POST"])
def scan_barcode(barcode):
    conn = sqlite3.connect("hotdeal.db")
    cursor = conn.cursor()

    if request.method == "GET":
        try:
            cursor.execute(
                "SELECT * FROM products WHERE barcode = ?", (barcode,)
            )
            product = cursor.fetchone()
            if product:
                return jsonify(
                    {
                        "success": True,
                        "exists": True,
                        "name": product[1],
                        "hotdeal_price": product[2],
                        "normal_price": product[3],
                    }
                )
            # 등록되지 않은 상품이면 안전하게 정보 전송
            return jsonify(
                {"success": True, "exists": False, "barcode": barcode}
            )
        except Exception as e:
            # 혹시나 또 에러가 나면 500을 뱉기 전에 에러 원인을 폰으로 전송
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            conn.close()

    elif request.method == "POST":
        data = request.json
        try:
            cursor.execute(
                "INSERT INTO products VALUES (?, ?, ?, ?)",
                (
                    barcode,
                    data["name"],
                    data["hotdeal_price"],
                    data["normal_price"],
                ),
            )
            conn.commit()
            return jsonify(
                {"success": True, "message": "성공적으로 등록되었습니다!"}
            )
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            conn.close()


if __name__ == "__main__":
    # 로컬 컴퓨터 테스트용
    app.run(host="0.0.0.0", port=5000, debug=True)
