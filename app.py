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
    cursor.execute(
        "INSERT INTO products VALUES ('8801045291313', '햇반 210g', 900, 1300) ON CONFLICT (barcode) DO NOTHING"
    )
    conn.commit()
    cursor.close()
    conn.close()


if DATABASE_URL:
    init_db()


@app.route("/")
def index():
    return render_template("index.html")


# 1. 바코드 조회 및 신규 등록 API
@app.route("/api/scan/<barcode>", methods=["GET", "POST"])
def scan_barcode(barcode):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "GET":
        try:
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


# ★ 2. [신규 추가] 역대 최저가 가격 업데이트 API
@app.route("/api/update/<barcode>", methods=["POST"])
def update_price(barcode):
    conn = get_db_connection()
    cursor = conn.cursor()
    data = request.json
    try:
        # 해당 바코드의 hotdeal_price를 새로운 가격으로 업데이트
        cursor.execute(
            "UPDATE products SET hotdeal_price = %s WHERE barcode = %s",
            (data["hotdeal_price"], barcode),
        )
        conn.commit()
        return jsonify(
            {
                "success": True,
                "message": "💥 역대 최저가가 성공적으로 갱신되었습니다!",
            }
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
