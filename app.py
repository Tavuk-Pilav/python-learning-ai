import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import google.generativeai as genai
from markdown import markdown
import bleach
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
import firebase_admin
from firebase_admin import credentials, auth
from dotenv import load_dotenv
from firebase_admin import firestore

load_dotenv()
app = Flask(__name__)
app.secret_key = 'GüvenliBirGizliAnahtar'  # Bunu güvenli bir şekilde ayarlayın

# Ortam değişkenlerini yükleyin
API_KEY = os.getenv('API_KEY')
SERVICE_ACCOUNT_KEY_JSON = os.getenv('SERVICE_ACCOUNT_KEY')  # JSON içeriği
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Geçici dosya yolu
service_account_path = "/tmp/service_account.json"

# JSON içeriğini geçici dosyaya yaz
if SERVICE_ACCOUNT_KEY_JSON:
    with open(service_account_path, "w") as f:
        f.write(SERVICE_ACCOUNT_KEY_JSON)

# Firebase Admin SDK'yı başlatma
cred = credentials.Certificate(service_account_path)
firebase_admin.initialize_app(cred)

# Google Generative AI yapılandırması
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Firestore istemcisini başlat
db = firestore.client()

# Diğer kodlarınız burada devam ediyor...

TOPIC_TREE = {
    "Python": {
        "Değişkenler ve Veri Tipleri": [
            "Değişken tanımlama ve kullanımı",
            "Temel veri tipleri (int, float, str, bool)",
            "Tip dönüşümleri ve veri tipi kontrolü"
        ],
        "Operatörler": [
            "Aritmetik operatörler",
            "Karşılaştırma operatörleri",
            "Mantıksal ve bit düzeyinde operatörler"
        ],
        "Koşullu İfadeler": [
            "if, elif, else kullanımı",
            "Karşılaştırma ve mantıksal işlemlerle koşullar oluşturma"
        ],
        "Döngüler": [
            "for ve while döngüleri",
            "break ve continue ifadeleri",
            "Liste ve sözlük gibi veri yapılarını döngülerle işleme"
        ],
        "Fonksiyonlar": [
            "Fonksiyon tanımlama ve çağırma",
            "Parametreler ve dönüş değerleri",
            "Lambda fonksiyonları"
        ],
        "Modüller": [
            "Hazır modülleri kullanma (math, random, datetime vb.)",
            "Kendi modüllerinizi oluşturma",
            "Python’da paket yönetimi"
        ]
    },
    "Nesne Yönelimli Programlama (OOP)": {
        "Sınıflar ve Nesneler": [
            "Nesne yönelimli programlama temelleri",
            "Sınıf ve nesne oluşturma",
            "Yapıcı (constructor) ve yıkıcı (destructor) metodlar"
        ],
        "Hata Yönetimi": [
            "try, except, finally kullanımı",
            "Özel hata sınıfları tanımlama",
            "Hata mesajlarını yakalama ve yönetme"
        ],
        "Dosya İşlemleri": [
            "Dosya açma, okuma, yazma ve kapama",
            "Dosya ve klasör işlemleri (os modülü ile)",
            "JSON ve CSV gibi veri formatları ile çalışma"
        ],
        "Dekoratörler": [
            "Fonksiyonlara özellik ekleme",
            "@decorator işaretleyicisi ile dekoratör oluşturma",
            "Sınıf ve metotlarda dekoratör kullanımı"
        ],
        "Jeneratörler": [
            "Generatör fonksiyonları ve yield kullanımı",
            "Generatörlerle bellekte verimli veri işlemleri",
            "List comprehensions ve generator expressions"
        ]
    },
    "Veri Yapıları": {
        "Diziler": [
            "Dizilerin tanımı ve temel özellikleri",
            "Python’da liste işlemleri",
            "Liste metodları (append, pop, insert, vb.)"
        ],
        "Bağlı Listeler": [
            "Tekli ve çift bağlı liste yapısı",
            "Bağlı listelerde veri ekleme, silme, arama işlemleri",
            "Bağlı liste örnek uygulamaları"
        ],
        "Yığınlar (Stacks)": [
            "LIFO prensibi ile çalışan yığın veri yapısı",
            "push, pop, peek işlemleri",
            "Yığın uygulamaları (geri al butonu, parantez dengeleme vb.)"
        ],
        "Kuyruklar (Queues)": [
            "FIFO prensibi ile çalışan kuyruk veri yapısı",
            "enqueue ve dequeue işlemleri",
            "Kuyruk türleri (dairesel kuyruk, çift uçlu kuyruk)"
        ]
    },
    "Gelişmiş Veri Yapıları ve Algoritmalar": {
        "Ağaçlar": [
            "İkili ağaçlar (Binary Trees)",
            "Ağacın öncelikli, ardışık ve postorder dolaşımları",
            "AVL ve B-Tree gibi dengeli ağaç yapıları"
        ],
        "Graf Yapıları": [
            "Graf veri yapısının tanımı ve türleri",
            "Breadth-First Search (BFS) ve Depth-First Search (DFS) algoritmaları",
            "Ağırlıklı graf ve kısa yol algoritmaları (Dijkstra, Bellman-Ford vb.)"
        ],
        "Hash Tabloları": [
            "Hash fonksiyonu ve çarpışma çözümleri",
            "Hash tablolar ile veri ekleme ve silme işlemleri",
            "Hashing’in veri erişimi üzerindeki etkisi"
        ],
        "Heap Yapıları": [
            "Min ve Max Heap yapıları",
            "Heap sıralama algoritması (Heap Sort)",
            "Öncelik kuyruğu uygulamaları"
        ]
    }
}


def create_chat_session(user_id, first_message):
    """Her yeni sohbet için Firestore'da yeni bir sohbet oturumu oluşturur ve oturum kimliğini döndürür."""
    # İlk üç kelimeyi alarak session_name oluşturuyoruz
    session_name = " ".join(first_message.split()[:3]) + "..."
    session_id = f"{user_id}_{int(datetime.now().timestamp())}"
    session_data = {
        'session_name': session_name,
        'created_at': datetime.now()
    }
    db.collection('users').document(user_id).collection('chat_sessions').document(session_id).set(session_data)
    return session_id




def add_message_to_session(user_id, session_id, content, role):
    """Firestore'da belirli bir oturuma mesaj ekler."""
    message_id = f"{int(datetime.now().timestamp() * 1000)}"  # Benzersiz message ID
    message_ref = db.collection('users').document(user_id).collection('chat_sessions').document(session_id).collection('messages').document(message_id)
    message_data = {
        'content': content,
        'role': role,
        'timestamp': datetime.now()
    }
    message_ref.set(message_data)


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
                    "Tip dönüşümleri",
                    "Karmaşık veri tipleri"
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
                        "from dataclasses import dataclass\n@dataclass\nclass Nokta:\n    x: float\n    y: float",
                        "karmaşık_sayi = 3 + 4j",
                        "from typing import List, Dict\ndef isleme(items: List[Dict]) -> None: ..."
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
                        "matris @ vektor  # Matris çarpımı",
                        "nesne.__add__(self, diğer)",
                        "async with baglam_yonetici:"
                    ]
                }
            }
            # Diğer konular...
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
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.history: List[Dict] = []
        self.current_topic: Optional[str] = None
        self.student_level = "beginner"
        self.current_step = 0
        self.understanding_scores: Dict[str, List[float]] = {}

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

    def generate_prompt(self, message: str, topic_context: TopicContext) -> str:
    """Öğretmen yanıtı için gelişmiş prompt oluşturur."""
    current_step_content = topic_context.get_step_content(self.current_step, self.student_level)
    recent_history = "\n".join([
        f"{msg['role']}: {msg['content']}"
        for msg in self.history[-3:]
    ])
    
    return f"""Sen deneyimli ve arkadaş canlısı bir Türk Python eğitmenisin. '{self.current_topic}' konusunu öğretiyorsun. Her zaman Türkçe karakterleri doğru kullanırsın ve yazım kurallarına dikkat edersin.

ROLE:
- Öğrencinin seviyesine göre uygun dil ve terminoloji kullan
- Karmaşık konuları günlük hayattan örneklerle basitleştir
- Öğrencinin başarılarını vurgula ve motive et
- Hataları öğrenme fırsatı olarak gör

ÖĞRENME BAĞLAMI:
📊 Öğrenci Profili:
- Seviye: {self.student_level}
- Mevcut Konu: {current_step_content.get('step_name', 'Giriş')}
- İlerleme: {self.current_step + 1}/{len(topic_context.context.get('steps', []))}

💬 SON ETKİLEŞİMLER:
{recent_history}

📝 YENİ MESAJ: {message}

YANITLAMA STRATEJİSİ:
1. AÇIKLAMA:
   - Konuyu önce büyük resimde anlat
   - Teknik terimleri günlük dilde karşılıklarıyla açıkla
   - Zor kavramları adım adım parçalara böl

2. ÖRNEKLENDIRME:
   - Her kavram için en az bir gerçek hayat örneği ver
   - Başlangıç seviyesinden ileri seviyeye doğru örnekler sun
   - Farklı kullanım senaryoları göster

3. UYGULAMA:
   - Öğrenciyi aktif öğrenmeye teşvik et
   - "Şimdi sen dene" yaklaşımıyla küçük görevler ver
   - Çözümleri adım adım açıkla

4. PEKİŞTİRME:
   - Öğrenilenleri özetle
   - Kritik noktaları vurgula
   - Bir sonraki adım için merak uyandır

FORMAT KURALLARI:
- Önemli kavramları **kalın** yaz
- Kod örneklerini ```python ile göster
- Adımları ve önemli noktaları maddeler halinde listele
- Sorularını ve alıştırmaları '>' ile belirt
- Başarıları ve motivasyonu '🌟' ile vurgula
- İpuçlarını '💡' ile göster
- Uyarıları '⚠️' ile belirt

TON VE DİL:
- Samimi ama profesyonel ol
- "Biz" dilini kullan ("Birlikte öğrenelim", "Şimdi şunu deneyelim" gibi)
- Öğrencinin seviyesine uygun teknik terimler kullan
- Pozitif ve motive edici bir dil kullan
- Hataları öğrenme fırsatı olarak göster
- Başarıları kutla ve teşvik et

{current_step_content.get('examples', '')}

ÖNEMLİ NOTLAR:
- Her açıklamadan sonra mutlaka anlama kontrolü yap
- Öğrencinin sorularını derinlemesine yanıtla
- Her yeni kavramı önceki öğrenilenlerle ilişkilendir
- Öğrencinin kendi çözümlerini bulmasını teşvik et
"""

    def evaluate_understanding(self, message: str) -> float:
        """Öğrencinin anlama düzeyini değerlendirir."""
        # Basit bir değerlendirme metriği
        understanding_indicators = {
            "positive": ["anladım", "tamam", "evet", "mantıklı", "doğru"],
            "negative": ["anlamadım", "tekrar", "karışık", "zor", "anlaşılmadı"],
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

        recent_scores = self.understanding_scores[self.current_topic][-3:]  # Son 3 skor
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

# Global oturum sözlüğü
sessions: Dict[str, EnhancedTutorSession] = {}

# Flask rotaları
@app.route('/login')
def login():
    return render_template('login.html', API_KEY=API_KEY)


@app.route('/api/chat', methods=['POST'])
def chat():
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Yetkisiz erişim'}), 401

    data = request.json
    message = data.get('message')
    topic = data.get('topic')
    user_id = session['user']
    
    # Oturum zaten yoksa ilk mesajı kullanarak bir oturum adı oluştur
    session_id = data.get('session_id') or create_chat_session(user_id, message)

    if session_id not in sessions:
        sessions[session_id] = EnhancedTutorSession(GEMINI_API_KEY)

    session_obj = sessions[session_id]
    session_obj.current_topic = topic
    session_obj.add_message('user', message)

    # Mesajı Firestore'a kaydet
    add_message_to_session(user_id, session_id, message, "user")

    response = session_obj.get_response(message)
    session_obj.add_message('assistant', response)

    # Asistan yanıtını Firestore'a kaydet
    add_message_to_session(user_id, session_id, response, "assistant")

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
        'student_level': session_obj.student_level,
        'current_step': session_obj.current_step,
        'topic': session_obj.current_topic,
        'understanding_score': session_obj.understanding_scores.get(session_obj.current_topic, [0])[-1]
    })



@app.route('/')
def home():
    if 'user' in session:
        return render_template('index.html', topic_tree=TOPIC_TREE)
    else:
        return redirect(url_for('login'))

@app.route('/sessionLogin', methods=['POST'])
def session_login():
    id_token = request.json.get('idToken')
    try:
        # Token'ı doğrula
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        # Oturumu başlat
        session['user'] = uid
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 401

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/api/get_chat_sessions', methods=['GET'])
def get_chat_sessions():
    user_id = session.get('user')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Yetkisiz erişim'}), 401

    chat_sessions = []
    sessions_ref = db.collection('users').document(user_id).collection('chat_sessions').order_by("created_at")
    for session_doc in sessions_ref.stream():
        session_data = session_doc.to_dict()
        session_data['session_id'] = session_doc.id
        chat_sessions.append(session_data)

    return jsonify(chat_sessions)


@app.route('/api/get_chat_messages', methods=['GET'])
def get_chat_messages():
    try:
        user_id = session.get('user')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Yetkisiz erişim'}), 401

        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({'status': 'error', 'message': 'Geçersiz oturum ID'}), 400

        messages = []
        messages_ref = db.collection('users').document(user_id).collection('chat_sessions').document(session_id).collection('messages')
        docs = messages_ref.order_by('timestamp').stream()

        for doc in docs:
            message = doc.to_dict()

            # Her mesajı HTML'e dönüştür ve temizle
            formatted_content = bleach.clean(
                markdown(message['content'], extensions=['fenced_code', 'tables']),
                tags=['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'code', 'pre',
                      'strong', 'em', 'ul', 'ol', 'li', 'table', 'thead', 'tbody',
                      'tr', 'th', 'td', 'blockquote', 'br'],
                attributes={'code': ['class'], 'pre': ['class']}
            )
            message['formatted_content'] = formatted_content
            messages.append(message)

        return jsonify(messages)

    except Exception as e:
        print(f"get_chat_messages hata: {e}")  # Sunucu konsolunda hatayı görmek için
        return jsonify({'status': 'error', 'message': 'Sunucu hatası'}), 500


@app.route('/api/new_chat_session', methods=['POST'])
def new_chat_session():
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Yetkisiz erişim'}), 401

    data = request.json
    session_name = data.get('session_name', 'Yeni Chat Oturumu')
    user_id = session['user']
    session_id = create_chat_session(user_id, session_name)
    return jsonify({'session_id': session_id, 'session_name': session_name})



if __name__ == '__main__':
    app.run(debug=True)
