from flask import Flask, render_template, jsonify, request
import google.generativeai as genai
from markdown import markdown
import bleach
from datetime import datetime
import json
import os
from typing import Dict, List, Optional

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

class TopicContext:
    """Her konu için öğrenme yolunu ve içeriği tanımlar."""
    
    def __init__(self, topic_name: str):
        self.topic_name = topic_name
        self.context = self._get_topic_context()
    
    def _get_topic_context(self) -> Dict:
        """Konuya özel içerik ve öğrenme yolunu döndürür."""
        contexts = {
            "Değişkenler ve Veri Tipleri": {
                "steps": [
                    "Değişken kavramı ve önemi",
                    "Python'da temel veri tipleri",
                    "Değişken tanımlama kuralları",
                    "Type conversion işlemleri",
                    "Complex veri tipleri"
                ],
                "prerequisites": [],
                "examples": {
                    "beginner": [
                        "yaş = 25",
                        "isim = 'Ahmet'",
                        "boy = 1.78"
                    ],
                    "intermediate": [
                        "x, y = 10, 20",
                        "liste = [1, 'abc', True]",
                        "sayilar = list(range(10))"
                    ],
                    "advanced": [
                        "from dataclasses import dataclass\n@dataclass\nclass Point:\n    x: float\n    y: float",
                        "complex_num = 3 + 4j",
                        "from typing import List, Dict\ndef process(items: List[Dict]) -> None: ..."
                    ]
                }
            },
            "Operatörler": {
                "steps": [
                    "Aritmetik operatörler",
                    "Karşılaştırma operatörleri",
                    "Mantıksal operatörler",
                    "Bitwise operatörler",
                    "Özel operatörler"
                ],
                "prerequisites": ["Değişkenler ve Veri Tipleri"],
                "examples": {
                    "beginner": [
                        "toplam = 5 + 3",
                        "sonuc = 10 > 5",
                        "kontrol = True and False"
                    ],
                    "intermediate": [
                        "x = 5; x += 3",
                        "sayilar = [1, 2, 3]; 2 in sayilar",
                        "bitwise_and = 5 & 3"
                    ],
                    "advanced": [
                        "matrix @ vector  # Matrix multiplication",
                        "object.__add__(self, other)",
                        "async with context_manager:"
                    ]
                }
            }
            # Diğer konular için benzer yapılar...
        }
        return contexts.get(self.topic_name, {})
    
    def get_step_content(self, step_number: int, level: str) -> Dict:
        """Belirli bir adım için içerik ve örnekleri döndürür."""
        steps = self.context.get("steps", [])
        examples = self.context.get("examples", {}).get(level, [])
        
        if 0 <= step_number < len(steps):
            return {
                "step_name": steps[step_number],
                "examples": examples[step_number] if step_number < len(examples) else None
            }
        return {}

class EnhancedTutorSession:
    """Gelişmiş öğretmen asistanı oturumu."""
    
    def __init__(self, api_key: str):
        genai.configure(api_key="gemini-api-key")
        self.model = genai.GenerativeModel('gemini-pro')
        self.history: List[Dict] = []
        self.current_topic: Optional[str] = None
        self.student_level = "beginner"
        self.current_step = 0
        self.understanding_scores: Dict[str, float] = {}
        
    def analyze_student_level(self, message: str) -> None:
        """Öğrenci mesajını analiz ederek seviyesini belirler."""
        # Seviye belirleme kriterleri
        level_indicators = {
            "advanced": [
                "metaclass", "decorator", "generator", "async",
                "threading", "multiprocessing", "optimization",
                "memory management", "design pattern"
            ],
            "intermediate": [
                "class", "inheritance", "exception", "file handling",
                "list comprehension", "lambda", "recursion",
                "module", "package"
            ]
        }
        
        message_lower = message.lower()
        
        # Gelişmiş kalıpları kontrol et
        if any(indicator in message_lower for indicator in level_indicators["advanced"]):
            self.student_level = "advanced"
        # Orta seviye kalıpları kontrol et
        elif any(indicator in message_lower for indicator in level_indicators["intermediate"]):
            self.student_level = "intermediate"
        
        # Cümle yapısı ve kelime kullanımı analizi
        words = message_lower.split()
        technical_terms = sum(1 for word in words if len(word) > 7)  # Uzun teknik terimler
        if technical_terms / len(words) > 0.3:  # %30'dan fazla teknik terim
            self.student_level = max(self.student_level, "intermediate")
    
    def generate_prompt(self, message: str, topic_context: TopicContext) -> str:
        """Öğretmen yanıtı için prompt oluşturur."""
        current_step_content = topic_context.get_step_content(self.current_step, self.student_level)
        
        # Son 3 mesajı al
        recent_history = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in self.history[-3:]
        ])
        
        return f"""
        Sen profesyonel ve arkadaşça bir Python eğitmenisin. '{self.current_topic}' konusunu öğretiyorsun.
        
        ÖĞRENME BAĞLAMI:
        - Öğrenci Seviyesi: {self.student_level}
        - Mevcut Adım: {current_step_content.get('step_name', 'Giriş')}
        - Konu İlerlemesi: {self.current_step + 1}/{len(topic_context.context.get('steps', []))}
        
        SON KONUŞMALAR:
        {recent_history}
        
        YENİ MESAJ: {message}
        
        YANITLAMA PRENSİPLERİ:
        1. Samimi ve destekleyici ol
        2. Konuyu gerçek dünya örnekleriyle açıkla
        3. Her yeni kavramı kod örnekleriyle destekle
        4. Öğrencinin seviyesine uygun detayda açıklama yap
        5. Her açıklamadan sonra anlama kontrolü için soru sor
        6. Başarıları takdir et ve motive et
        7. Hataları nazikçe düzelt
        
        YANITLAMA FORMATI:
        - Ana kavramları **bold** yap
        - Kod örneklerini ``` içinde göster
        - Önemli noktaları maddeler halinde listele
        - Sorularını '>' işaretiyle belirt
        
        {current_step_content.get('examples', '')}
        """
    
    def evaluate_understanding(self, message: str) -> float:
        """Öğrencinin anlama düzeyini değerlendirir."""
        # Basit bir değerlendirme metriği
        understanding_indicators = {
            "positive": ["anladım", "tamam", "evet", "mantıklı", "doğru"],
            "negative": ["anlamadım", "tekrar", "confused", "zor", "karışık"],
            "questioning": ["neden", "nasıl", "niçin", "?"]
        }
        
        message_lower = message.lower()
        
        # Pozitif ve negatif göstergeleri say
        positive_count = sum(1 for word in understanding_indicators["positive"] if word in message_lower)
        negative_count = sum(1 for word in understanding_indicators["negative"] if word in message_lower)
        question_count = sum(1 for word in understanding_indicators["questioning"] if word in message_lower)
        
        # Anlama skorunu hesapla (-1 ile 1 arasında)
        base_score = (positive_count - negative_count) / (positive_count + negative_count + 1)
        question_penalty = -0.2 * (question_count / (len(message_lower.split()) + 1))
        
        return max(-1, min(1, base_score + question_penalty))
    
    def add_message(self, role: str, content: str) -> None:
        """Mesaj geçmişine yeni mesaj ekler."""
        self.history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'topic': self.current_topic,
            'step': self.current_step,
            'level': self.student_level
        })
        
        # Öğrenci mesajlarını analiz et
        if role == 'user':
            self.analyze_student_level(content)
            understanding_score = self.evaluate_understanding(content)
            
            if self.current_topic:
                if self.current_topic not in self.understanding_scores:
                    self.understanding_scores[self.current_topic] = []
                self.understanding_scores[self.current_topic].append(understanding_score)
    
    def should_advance_step(self) -> bool:
        """Bir sonraki adıma geçilip geçilmeyeceğini belirler."""
        if not self.current_topic in self.understanding_scores:
            return False
            
        recent_scores = self.understanding_scores[self.current_topic][-3:] # Son 3 skor
        if len(recent_scores) < 3:
            return False
        # Ortalama skor 0.6'dan büyükse ilerle
        return sum(recent_scores) / len(recent_scores) > 0.6  
    
    def get_response(self, message: str) -> str:
        """Öğretmen yanıtını oluşturur."""
        if not self.current_topic:
            return "Lütfen önce bir konu seçin."
            
        topic_context = TopicContext(self.current_topic)
        prompt = self.generate_prompt(message, topic_context)
        
        try:
            response = self.model.generate_content(prompt)
            
            # Yanıt başarılıysa ve anlama yeterliyse adımı ilerlet
            if self.should_advance_step():
                self.current_step += 1
                self.understanding_scores[self.current_topic] = []  
            
            return response.text
        except Exception as e:
            return f"Üzgünüm, bir hata oluştu: {str(e)}"

# Flask routes
@app.route('/')
def home():
    """Ana sayfa."""
    return render_template('index.html', topic_tree=TOPIC_TREE)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat API endpoint."""
    data = request.json
    session_id = data.get('session_id')
    message = data.get('message')
    topic = data.get('topic')
    
    if session_id not in sessions:
        sessions[session_id] = EnhancedTutorSession(os.getenv('gemini-api-key'))
    
    session = sessions[session_id]
    session.current_topic = topic
    session.add_message('user', message)
    
    response = session.get_response(message)
    session.add_message('assistant', response)
    
    # Markdown'ı HTML'e çevir ve temizle
    html_response = bleach.clean(
        markdown(response, extensions=['fenced_code', 'tables']),
        tags=['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'code', 'pre', 
              'strong', 'em', 'ul', 'ol', 'li', 'table', 'thead', 'tbody',
              'tr', 'th', 'td', 'blockquote', 'br'],
        attributes={'code': ['class'], 'pre': ['class']}
    )
    
    return jsonify({
        'response': response,
        'html_response': html_response,
        'student_level': session.student_level,
        'current_step': session.current_step,
        'topic': session.current_topic,
        'understanding_score': session.understanding_scores.get(session.current_topic, [0])[-1]
    })

# Global session dictionary
sessions: Dict[str, EnhancedTutorSession] = {}

if __name__ == '__main__':
    app.run(debug=True)