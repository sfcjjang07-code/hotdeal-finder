import sqlite3
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scan/<barcode>", methods=["GET", "POST"])
def scan_barcode(barcode):
    conn = sqlite3.connect("hotdeal.db")
    cursor = conn.cursor()

    if request.method == "GET":
        cursor.execute("SELECT * FROM products WHERE barcode = ?", (barcode,))
        product = cursor.fetchone()
        conn.close()
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
        return jsonify({"success": True, "exists": False, "barcode": barcode})

    elif request.method == "POST":
        data = request.json
        try:
            cursor.execute(
                "INSERT INTO products VALUES (?, ?, ?, ?)",
                (barcode, data["name"], data["hotdeal_price"], data["normal_price"]),
            )
            conn.commit()
            return jsonify({"success": True, "message": "성공적으로 등록되었습니다!"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})
        finally:
            conn.close()


if __name__ == "__main__":
      init_db()
      app.run(host="0.0.0.0", port=5000, debug=True, ssl_context="adhoc")