// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    const sessionId = Date.now().toString();
    let currentTopic = null;
  
    // Topic navigation handlers
    const initializeTopicNavigation = () => {
      document.querySelectorAll('.topic-main, .category-main').forEach(button => {
        button.addEventListener('click', function() {
          const contentElement = this.nextElementSibling;
          contentElement?.classList.toggle('hidden');
        });
      });
  
      document.querySelectorAll('.topic').forEach(button => {
        button.addEventListener('click', function() {
          currentTopic = this.dataset.topic;
          const topicElement = document.getElementById('current-topic');
          if (topicElement) {
            topicElement.textContent = currentTopic;
          }
          sendMessage(`${currentTopic} konusunu öğrenmek istiyorum. Başlayalım.`);
        });
      });
    };
  
    // Chat functionality
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');
  
    const appendMessage = (role, content) => {
      if (!chatMessages) return;
  
      const messageDiv = document.createElement('div');
      messageDiv.className = `message ${role}-message markdown-content`;
      messageDiv.innerHTML = content;
      chatMessages.appendChild(messageDiv);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    };
  
    const sendMessage = async (message) => {
      const trimmedMessage = message.trim();
      if (!trimmedMessage) return;
  
      appendMessage('user', trimmedMessage);
      if (messageInput) {
        messageInput.value = '';
      }
  
      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            session_id: sessionId,
            message: trimmedMessage,
            topic: currentTopic
          })
        });
  
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
  
        const data = await response.json();
        appendMessage('assistant', data.html_response);
  
        // Update syntax highlighting
        if (typeof Prism !== 'undefined') {
          Prism.highlightAll();
        }
      } catch (error) {
        console.error('Error:', error);
        appendMessage('assistant', 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.');
      }
    };
  
    // Event listeners
    if (sendButton) {
      sendButton.addEventListener('click', () => {
        if (messageInput) {
          sendMessage(messageInput.value);
        }
      });
    }
  
    if (messageInput) {
      messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          sendMessage(messageInput.value);
        }
      });
    }
  
    // Initialize topic navigation
    initializeTopicNavigation();
  });