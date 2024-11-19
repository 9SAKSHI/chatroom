const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));

// Handle socket connections
io.on('connection', (socket) => {
  console.log('A user connected');

  socket.on('join', (username) => {
    socket.username = username;
    socket.broadcast.emit('message', `${username} has joined the chat`);
  });

  // Handle text chat messages
  socket.on('chatMessage', (data) => {
    io.emit('message', `${data.username}: ${data.message}`);
  });

  // Handle voice messages
  socket.on('voiceMessage', (data) => {
    // Broadcast the voice message to all clients
    io.emit('voiceMessage', { username: data.username, audioBlob: data.audioBlob });
    console.log('Voice message received and broadcasted');
  });

  // Handle image messages
  socket.on('imageMessage', (data) => {
    // Broadcast the image message to all clients
    io.emit('imageMessage', { username: data.username, imageData: data.imageData });
    console.log('Image message received and broadcasted');
  });

  // Handle disconnection
  socket.on('disconnect', () => {
    console.log('User disconnected');
    socket.broadcast.emit('message', `${socket.username} has left the chat`);
  });
});

// Start the server
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
