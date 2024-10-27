from flask import Flask, render_template, jsonify, request
import google.generativeai as genai
from markdown import markdown
import bleach
from datetime import datetime
import json

app = Flask(__name__)

TOPIC_TREE = {
    "Python": {
        "Temel Konular": [
            "Değişkenler ve Veri Tipleri",
            "Operatörler",
            "Koşullu İfadeler",
            "Döngüler",
            "Fonksiyonlar",
            "Modüller"
        ],
        "İleri Seviye": [
            "Sınıflar ve Nesneler",
            "Hata Yönetimi",
            "Dosya İşlemleri",
            "Dekoratörler",
            "Jeneratörler"
        ]
    },
    "Veri Yapıları": {
        "Temel Veri Yapıları": [
            "Diziler",
            "Bağlı Listeler",
            "Yığınlar",
            "Kuyruklar"
        ],
        "İleri Veri Yapıları": [
            "Ağaçlar",
            "Graflar",
            "Hash Tabloları",
            "Heap"
        ]
    }
}

class ChatSession:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.history = []
        self.current_topic = None
        
    def add_message(self, role, content):
        self.history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
    def get_response(self, message):
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.history[-5:]])
        
        prompt = f"""
        Son konuşmalar:
        {context}
        
        Mevcut konu: {self.current_topic}
        Öğrenci mesajı: {message}
        
        Lütfen:
        1. Markdown formatında yanıt ver
        2. Kod örnekleri için ``` kullan
        3. Önemli noktaları **bold** yap
        4. Öğrencinin seviyesine göre yanıt ver
        5. Konuyu adım adım ilerlet
        6. Her yanıtın sonunda anlama kontrolü için soru sor
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Üzgünüm, bir hata oluştu: {str(e)}"

# Global session dictionary
sessions = {}

@app.route('/')
def home():
    return render_template('index.html', topic_tree=TOPIC_TREE)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    session_id = data.get('session_id')
    message = data.get('message')
    topic = data.get('topic')
    
    if session_id not in sessions:
        sessions[session_id] = ChatSession('Gemini_Api_Key')
    
    session = sessions[session_id]
    session.current_topic = topic
    session.add_message('user', message)
    
    response = session.get_response(message)
    session.add_message('assistant', response)
    
    # Convert markdown to HTML
    html_response = bleach.clean(
        markdown(response, extensions=['fenced_code', 'tables']),
        tags=['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'code', 'pre', 
              'strong', 'em', 'ul', 'ol', 'li', 'table', 'thead', 'tbody',
              'tr', 'th', 'td', 'blockquote', 'br'],
        attributes={'code': ['class'], 'pre': ['class']}
    )
    
    return jsonify({
        'response': response,
        'html_response': html_response
    })

if __name__ == '__main__':
    app.run(debug=True)