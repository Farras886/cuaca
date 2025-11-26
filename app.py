from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import requests
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rahasia_donk'
socketio = SocketIO(app, cors_allowed_origins="*")

API_KEY = "MASUKKAN_API_KEY_OPENWEATHER_DISINI"
CITY = "Pontianak" # Ganti dengan kotamu

def get_weather_forecast():
    # PERUBAHAN 1: Menambahkan '&lang=id' di akhir URL
    # Ini bikin deskripsi cuaca (misal: "light rain") jadi bahasa Indonesia ("hujan ringan")
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric&lang=id"
    response = requests.get(url)
    return response.json()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('cek_jadwal')
def handle_cek_jadwal(data):
    weather_data = get_weather_forecast()
    
    # --- LOGIKA GRAFIK & RATA-RATA ---
    chart_labels = []
    chart_temps = []
    processed_dates = set()
    
    for item in weather_data['list']:
        date_only = item['dt_txt'].split(" ")[0]
        time_only = item['dt_txt'].split(" ")[1]
        
        if date_only not in processed_dates and len(processed_dates) < 5:
            if "12:00" in time_only or len(chart_labels) == len(processed_dates): 
                chart_labels.append(date_only)
                chart_temps.append(item['main']['temp'])
                processed_dates.add(date_only)

    if len(chart_temps) > 0:
        avg_temp = round(sum(chart_temps) / len(chart_temps), 1)
    else:
        avg_temp = 0

    # --- LOGIKA SARAN ---
    user_date = data['tanggal']
    user_time = data['jam']
    target_time_str = f"{user_date} {user_time}:00"
    
    found = False
    saran = ""
    kondisi = ""
    
    for item in weather_data['list']:
        if target_time_str in item['dt_txt']:
            # 'description' otomatis jadi B.Indo karena lang=id (contoh: "hujan ringan", "awan tersebar")
            kondisi = item['weather'][0]['description'] 
            
            # 'main' TETAP bahasa Inggris (Rain, Clouds, Clear). 
            # Kita pakai ini untuk logika IF karena lebih stabil daripada description yang bisa macam-macam.
            main_weather = item['weather'][0]['main']
            temp = item['main']['temp']
            
            # Logika Saran
            if main_weather in ['Rain', 'Thunderstorm', 'Drizzle']:
                saran = f"⚠️ Waduh, bakal {kondisi}. Mending jangan keluar dulu, atau siapin payung/mantel ya!"
            elif main_weather == 'Snow':
                saran = f"❄️ Turun salju ({kondisi}). Pakai baju tebal!"
            elif main_weather == 'Clear':
                if temp > 33:
                    saran = f"☀️ Cuaca cerah tapi panas banget ({temp}°C). Jangan lupa pakai sunscreen!"
                else:
                    saran = f"✅ Asik! Cuaca cerah ({kondisi}). Aman buat keluar rumah."
            elif main_weather == 'Clouds':
                saran = f"☁️ Langit agak mendung/berawan ({kondisi}). Sejuk sih, aman buat jalan."
            else:
                saran = f"ℹ️ Cuaca diprediksi: {kondisi}. Tetap hati-hati ya."
            
            found = True
            break
            
    if not found:
        saran = "Maaf, data prediksi spesifik untuk jam tersebut belum tersedia. Coba cek grafik tren harian di bawah."

    emit('hasil_prediksi', {
        'saran': saran,
        'kondisi': kondisi,
        'grafik_label': chart_labels,
        'grafik_data': chart_temps,
        'rata_rata': avg_temp
    })

if __name__ == '__main__':
    socketio.run(app, debug=True)
