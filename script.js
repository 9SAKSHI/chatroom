const socket = io();
let username;

// Handle username input and join chat
document.getElementById('join-chat').addEventListener('click', () => {
  username = document.getElementById('username-input').value;
  if (username) {
    document.getElementById('username-container').style.display = 'none';
    document.getElementById('chatroom').style.display = 'flex';
    socket.emit('join', username);
  }
});

// Handle incoming messages
socket.on('message', (message) => {
  const chatBox = document.getElementById('chat-box');
  chatBox.innerHTML += `<div>${message}</div>`;
  chatBox.scrollTop = chatBox.scrollHeight; // Scroll to the bottom
});

// Handle chat form submission
document.getElementById('chat-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const messageInput = document.getElementById('message-input');
  const message = messageInput.value;
  if (message) {
    socket.emit('chatMessage', { username, message });
    messageInput.value = '';
  }
});

// Voice Recording Implementation
let recorder;
let audioChunks = [];
let mediaStream;

const audioPreview = document.getElementById('audio-preview');
const sendAudioButton = document.getElementById('send-audio');
const cancelAudioButton = document.getElementById('cancel-audio');
const recordButton = document.getElementById('push-to-talk');

// Start recording
recordButton.addEventListener('click', () => {
  if (recorder && recorder.state === 'recording') {
    stopRecording(); // If already recording, stop the recording
  } else {
    startRecording(); // Otherwise, start the recording
  }
});

// Initialize the recording process
function startRecording() {
  console.log('Requesting microphone access...');
  navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
      console.log('Microphone access granted.');
      mediaStream = stream;
      recorder = new MediaRecorder(stream);
      
      recorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
        console.log('Audio data available:', event.data);
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        audioChunks = []; // Clear audioChunks for the next recording
        const audioUrl = URL.createObjectURL(audioBlob);
        audioPreview.src = audioUrl; // Set the audio source for playback
        audioPreview.style.display = 'block';
        sendAudioButton.style.display = 'inline';
        cancelAudioButton.style.display = 'inline';

        // Send the audio on click of send button
        sendAudioButton.addEventListener('click', () => {
          socket.emit('voiceMessage', { username, audioBlob });
          resetAudioPreview();
        });
      };

      recorder.onerror = (error) => {
        console.error('Recorder error:', error);
        alert('An error occurred during the recording process.');
        resetAudioPreview();
      };

      recorder.start();
      console.log('Recording started');
    })
    .catch(error => {
      console.error('Error accessing microphone:', error);
      alert('Please enable microphone permissions.');
    });
}

// Stop the recording process
function stopRecording() {
  if (recorder && recorder.state === 'recording') {
    recorder.stop();
    console.log('Recording stopped');
    mediaStream.getTracks().forEach(track => track.stop()); // Stop the stream
  } else {
    console.log('Recording not in progress.');
  }
}

// Reset audio preview and hide the buttons
function resetAudioPreview() {
  audioPreview.style.display = 'none';
  sendAudioButton.style.display = 'none';
  cancelAudioButton.style.display = 'none';
}

// Handle canceling audio
cancelAudioButton.addEventListener('click', () => {
  resetAudioPreview();
});

// Image Upload Implementation
document.getElementById('image-input').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) {
    // Read the file and send to the server
    const reader = new FileReader();
    reader.onload = () => {
      socket.emit('imageMessage', { username, imageData: reader.result });
      console.log('Image sent to server');
    };
    reader.readAsDataURL(file); // Convert image to base64
  }
});
