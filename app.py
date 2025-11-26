from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import requests
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rahasia_donk'
socketio = SocketIO(app, cors_allowed_origins="*")

API_KEY = "MASUKKAN_API_KEY_OPENWEATHER_DISINI"
CITY = "Pontianak" # Sesuaikan kota

def get_weather_forecast():
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric&lang=id"
    response = requests.get(url)
    return response.json()

@app.route('/')
def index():
    return render_template('index.html')

# --- LOGIC WEBSOCKET ---
@socketio.on('cek_jadwal')
def handle_cek_jadwal(data):
    # Data dari client: {'tanggal': '2025-11-27', 'jam': '15:00'}
    user_date = data['tanggal']
    user_time = data['jam'] # Format HH:00
    
    target_time_str = f"{user_date} {user_time}:00"
    
    weather_data = get_weather_forecast()
    
    found = False
    saran = ""
    kondisi = ""
    
    # Loop data forecast (list per 3 jam)
    for item in weather_data['list']:
        # Item['dt_txt'] formatnya "2025-11-27 15:00:00"
        # Kita cek apakah waktu yang diminta user mendekati prediksi ini
        if target_time_str in item['dt_txt']:
            kondisi = item['weather'][0]['description']
            main_weather = item['weather'][0]['main']
            temp = item['main']['temp']
            
            # LOGIKA SARAN (Requirement Tugasmu)
            if main_weather in ['Rain', 'Thunderstorm', 'Drizzle']:
                saran = f"⚠️ Cuaca buruk ({kondisi}). Sebaiknya jangan keluar dulu, atau siapkan payung/mantel tebal!"
            elif main_weather == 'Snow':
                saran = "❄️ Salju turun. Pakai baju hangat!"
            elif temp > 35:
                saran = "☀️ Panas terik! Jangan lupa sunscreen."
            else:
                saran = f"✅ Cuaca aman ({kondisi}). Silakan beraktivitas!"
            
            found = True
            break
    
    if not found:
        saran = "Maaf, data prediksi untuk jam tersebut tidak tersedia (OpenWeather gratis hanya support 5 hari ke depan per 3 jam)."

    # Kirim balik ke client via WebSocket
    emit('hasil_prediksi', {'saran': saran, 'kondisi': kondisi})

if __name__ == '__main__':
    socketio.run(app, debug=True)