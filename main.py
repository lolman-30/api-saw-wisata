import pymysql, cursor
from app import app
from config import mysql
from flask import jsonify, Flask, request

app = Flask(__name__)

# Fungsi untuk menghitung nilai SAW
def hitung_saw(cur, rating, harga):
   rating_max = float(cur.execute("SELECT MAX(rating) FROM twisata"))
   rating_min = float(cur.execute("SELECT MIN(rating) FROM twisata"))
   harga_max = int(cur.execute("SELECT MAX(harga) FROM twisata"))
   harga_min = int(cur.execute("SELECT MIN(harga) FROM twisata"))

   # Normalisasi Rating
   if rating_max == rating_min:
      normalisasi_rating = (float(rating) - rating_min) / 1
   else:
      rating_min = max(rating_min, 1) # Batasan minimum rating_min adalah 1
      rating_max = min(rating_max, 5) # Batasan maksimum rating_max adalah 5
      normalisasi_rating = (rating - rating_min) / (rating_max - rating_min)

   # Normalisasi Harga
   if harga_max == harga_min:
      normalisasi_harga = (int(harga) - harga_min) /1
   else:
      harga_min = max(harga_min, 1000) # Batasan minimum harga_min adalah 1000
      harga_max = min(harga_max, 500000) # Batasan maksimum harga_max adalah 500000
      normalisasi_harga = (harga - harga_min) / (harga_max - harga_min)

   preferensi_rating = normalisasi_rating * 0.6
   preferensi_harga = normalisasi_harga * 0.4

   saw = preferensi_rating + preferensi_harga
   return saw

   
@app.route('/wisata', methods=['GET'])
def twisatasGet():
   try:
      conn = mysql.connect()
      cur = conn.cursor(pymysql.cursors.DictCursor)
      cur.execute("SELECT * from twisata;")
      rows = cur.fetchall()
      resp = jsonify(rows)
      resp.status_code = 200
      return resp      
   except Exception as e:
      print(e)
   finally:
      cur.close()
      conn.close()

@app.route("/wisata/allsaw", methods=['GET'])
def allsaw():
   # Koneksi ke database
   conn = mysql.connect()
   cur = conn.cursor(pymysql.cursors.DictCursor)

   # Ambil semua data wisata dari database
   cur.execute("SELECT * FROM twisata;")
   rows = cur.fetchall()
   hasil_saw = []

   for row in rows:
      rating = row["rating"]
      harga = row["harga"]
      kategori = row["kategori"]
      saw = hitung_saw(cur, rating, harga)
      hasil_saw.append({
         "nama_wisata": row["nama"],
         "rating": rating,
         "harga": harga,
         "kategori": kategori,
         "saw": saw
      })
   
   # Urutkan hasil_saw berdasarkan nilai saw (dari yang tertinggi ke terendah)
   hasil_saw = sorted(hasil_saw, key=lambda x: x["saw"], reverse=True)

   # Kembalikan hasilnya dalam format JSON
   return jsonify(hasil_saw)


@app.route("/wisata/<string:nama>")
def twisatasaw(nama):
   # Koneksi ke database
   conn = mysql.connect()
   cur = conn.cursor(pymysql.cursors.DictCursor)
   # Ambil data wisata dari database
   cur.execute("SELECT * FROM twisata WHERE nama = %s", (nama,))
   rows = cur.fetchall()
   hasil_saw = []
   if not rows: # Jika list rows kosong
      return "Wisata tidak ditemukan", 404
   
   for row in rows:
      rating = row["rating"]
      harga = row["harga"]
      kategori = row["kategori"]
      saw = hitung_saw(cur, rating, harga)
      hasil_saw.append({
         "nama_wisata": row["nama"],
         "rating": rating,
         "harga": harga,
         "kategori": kategori,
         "saw": saw
      })

   # Kembalikan hasilnya dalam format JSON
   return jsonify(hasil_saw)

@app.errorhandler(404)
def showMessage(error=None):
   message = {
      'status': 404,
      'message': 'Data not found: ' + request.url,
   }
   respone = jsonify(message)
   respone.status_code = 404
   return respone



if __name__ == "__main__":
   app.run(debug=True, host="0.0.0.0")
