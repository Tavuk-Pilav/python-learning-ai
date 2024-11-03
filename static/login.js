// Firebase yapılandırma bilgileri
const firebaseConfig = {
    apiKey: API_KEY, // Flask template'den alınır
    authDomain: "btk-hackathon-53297.firebaseapp.com",
    projectId: "btk-hackathon-53297",
    storageBucket: "btk-hackathon-53297.appspot.com",
    messagingSenderId: "206057800740",
    appId: "1:206057800740:web:cea14c44c0ae472fd4c4b1",
    measurementId: "G-8J424EFKEV"
  };
  
  // Firebase'i başlatma
  firebase.initializeApp(firebaseConfig);
  const auth = firebase.auth();
  
  // Kayıt Ol Fonksiyonu
  function signUp() {
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
  
    auth.createUserWithEmailAndPassword(email, password)
      .then((userCredential) => {
        // Kayıt başarılı
        const user = userCredential.user;
        alert('Kayıt başarılı!');
        // Giriş paneline geçiş
        container.classList.remove("right-panel-active");
      })
      .catch((error) => {
        const errorMessage = error.message;
        alert('Kayıt başarısız: ' + errorMessage);
      });
  }
  
  // Giriş Fonksiyonu
  function signIn() {
    const email = document.getElementById('signin-email').value;
    const password = document.getElementById('signin-password').value;
  
    auth.signInWithEmailAndPassword(email, password)
      .then((userCredential) => {
        // Giriş başarılı
        const user = userCredential.user;
        return user.getIdToken().then((idToken) => {
          // ID token'ı backend'e gönder
          return fetch('/sessionLogin', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ idToken: idToken })
          });
        });
      })
      .then((response) => {
        if (response.ok) {
          // Başarılıysa ana sayfaya yönlendir
          window.location.href = '/';
        } else {
          return response.json().then((data) => {
            alert('Giriş başarısız: ' + data.message);
          });
        }
      })
      .catch((error) => {
        const errorMessage = error.message;
        alert('Giriş başarısız: ' + errorMessage);
      });
  }
  
  // Butonlara event listener ekleme
  const signUpButton = document.getElementById('signUp');
  const signInButton = document.getElementById('signIn');
  const container = document.getElementById('container');
  
  signUpButton.addEventListener('click', () => {
    container.classList.add("right-panel-active");
  });
  
  signInButton.addEventListener('click', () => {
    container.classList.remove("right-panel-active");
  });
  