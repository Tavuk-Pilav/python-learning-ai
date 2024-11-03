document.addEventListener('DOMContentLoaded', function() {
    let currentSessionId = null;
    let currentTopic = null;

    const chatSessionsElement = document.getElementById('chat-sessions');
    const chatMessagesElement = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const logoutButton = document.getElementById('logout-button');
    const toggleDarkModeButton = document.getElementById('toggle-dark-mode');
    const newSessionButton = document.getElementById('new-session-button');

    // Oturumları Firestore’dan çek ve sol panele ekle
    const loadChatSessions = async () => {
        try {
            const response = await fetch('/api/get_chat_sessions');
            if (!response.ok) {
                throw new Error(`Sunucu hatası: ${response.status}`);
            }
            const sessions = await response.json();
            chatSessionsElement.innerHTML = ''; // Önceki oturumları temizle
    
            sessions.forEach(session => {
                const sessionButton = document.createElement('button');
                sessionButton.classList.add(
                    'w-full', 'text-left', 'flex', 'items-center', 'justify-between', 
                    'text-gray-700', 'dark:text-gray-200', 'p-3', 'rounded-lg', 
                    'hover:bg-blue-100', 'dark:hover:bg-gray-700', 'transition'
                );
                sessionButton.innerHTML = `<span>${session.session_name}</span><i class="fas fa-chevron-right text-sm"></i>`;
    
                sessionButton.addEventListener('click', () => {
                    currentSessionId = session.session_id;  // Seçilen oturumun ID'sini güncelle
                    loadChatMessages(currentSessionId);  // Seçilen oturumdaki mesajları yükle
                });
    
                chatSessionsElement.appendChild(sessionButton);
            });
        } catch (error) {
            console.error('Oturumlar yüklenirken hata oluştu:', error);
        }
    };
    

    // Firestore’dan belirli bir oturuma ait mesajları çek
    const loadChatMessages = async (sessionId) => {
        try {
            const response = await fetch(`/api/get_chat_messages?session_id=${sessionId}`);
            if (!response.ok) {
                throw new Error(`Sunucu hatası: ${response.status}`);
            }
            const messages = await response.json();
            chatMessagesElement.innerHTML = '';  // Önceki mesajları temizle
    
            messages.forEach(message => {
                appendMessage(message.role, message.formatted_content || message.content);
            });
        } catch (error) {
            console.error('Mesajlar yüklenirken hata oluştu:', error);
        }
    };
    
    // Konu kırılımlarını başlat
    const initializeTopicNavigation = () => {
        document.querySelectorAll('.topic-main, .category-main').forEach(button => {
            button.addEventListener('click', function() {
                const contentElement = this.nextElementSibling;
                if (contentElement) {
                    contentElement.classList.toggle('hidden');
                }
            });
        });

        document.querySelectorAll('.topic').forEach(button => {
            button.addEventListener('click', function() {
                currentTopic = this.dataset.topic;
                sendMessage(`${currentTopic} konusunu öğrenmek istiyorum.`);
                document.getElementById('current-topic').textContent = currentTopic;
            });
        });
    };

    // Yeni sohbet oturumu oluştur
    newSessionButton.addEventListener('click', async () => {
        const sessionName = prompt('Yeni sohbet oturumu adı:');
        if (sessionName) {
            try {
                const response = await fetch('/api/new_chat_session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_name: sessionName })
                });
                
                const data = await response.json();
                currentSessionId = data.session_id;
                chatMessagesElement.innerHTML = ''; // Yeni oturum için önceki mesajları temizle
                loadChatSessions();  // Yeni oturumlar listesini yükle
                console.log('Yeni oturum başlatıldı:', sessionName);
            } catch (error) {
                console.error('Yeni oturum başlatılırken hata oluştu:', error);
            }
        }
    });

    // Çıkışta oturum kaydetme
    logoutButton.addEventListener('click', async () => {
        try {
            const response = await fetch('/logout', { method: 'GET' });
            if (response.ok) {
                window.location.href = '/login';
            } else {
                console.error('Çıkış işlemi başarısız:', response.statusText);
            }
        } catch (error) {
            console.error('Çıkış sırasında hata oluştu:', error);
        }
    });

    // Mesajı UI'ya ekle
    const appendMessage = (role, content) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message markdown-content`;
        messageDiv.innerHTML = content;
        chatMessagesElement.appendChild(messageDiv);
        chatMessagesElement.scrollTop = chatMessagesElement.scrollHeight;
    };

    // Mesaj gönderme işlevi
    const sendMessage = async (message) => {
        if (!message.trim()) return;
        appendMessage('user', message);
        messageInput.value = '';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: currentSessionId,
                    message: message,
                    topic: currentTopic
                })
            });

            const data = await response.json();
            appendMessage('assistant', data.html_response);

            if (typeof Prism !== 'undefined') {
                Prism.highlightAll();
            }
        } catch (error) {
            console.error('Mesaj gönderilirken hata oluştu:', error);
            appendMessage('assistant', 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.');
        }
    };

    // Send button and Enter key event listeners
    sendButton.addEventListener('click', () => {
        sendMessage(messageInput.value);
    });

    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage(messageInput.value);
        }
    });

    // Tema durumunu yükle
    const currentTheme = localStorage.getItem('theme') || 'light';
    if (currentTheme === 'dark') {
        document.body.classList.add('dark');
    }

    toggleDarkModeButton.addEventListener('click', () => {
        document.body.classList.toggle('dark');
        const newTheme = document.body.classList.contains('dark') ? 'dark' : 'light';
        localStorage.setItem('theme', newTheme);
    });

    // İlk yükleme sırasında oturumları, konu kırılımlarını ve konu navigasyonunu başlat
    loadChatSessions();
    initializeTopicNavigation();
});
