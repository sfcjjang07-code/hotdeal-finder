import os
import psycopg2
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# Render 설정창에 입력한 금고 주소(DATABASE_URL)를 자동으로 가져옵니다.
DATABASE_URL = os.environ.get("DATABASE_URL")


# 클라우드 데이터베이스와 연결하는 함수
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


# 데이터베이스 초기화 (테이블 생성 및 샘플 데이터 삽입)
def init_db():
    conn = get_db_connection()
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
    # 클라우드 DB(PostgreSQL) 문법에 맞게 'ON CONFLICT' 구문 사용
    cursor.execute(
        "INSERT INTO products VALUES ('8801045291313', '햇반 210g', 900, 1300) ON CONFLICT (barcode) DO NOTHING"
    )
    conn.commit()
    cursor.close()
    conn.close()


# 앱이 켜질 때 클라우드에 테이블을 자동으로 만듭니다.
if DATABASE_URL:
    init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scan/<barcode>", methods=["GET", "POST"])
def scan_barcode(barcode):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "GET":
        try:
            # PostgreSQL 표준에 맞게 %s 사용
            cursor.execute(
                "SELECT * FROM products WHERE barcode = %s", (barcode,)
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
            return jsonify(
                {"success": True, "exists": False, "barcode": barcode}
            )
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            cursor.close()
            conn.close()

    elif request.method == "POST":
        data = request.json
        try:
            cursor.execute(
                "INSERT INTO products VALUES (%s, %s, %s, %s)",
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
            cursor.close()
            conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
