const socket = io();

function sendMessage() {
    const msgInput = document.getElementById('chatInput');
    const msg = msgInput.value.trim();
    if (msg) {
        socket.emit('send_message', { room: ROOM_NAME, message: msg });
        msgInput.value = '';
    }
}

socket.on('receive_message', (data) => {
    const chatBox = document.getElementById('chatBox');
    const msgDiv = document.createElement('div');
    msgDiv.className = "bg-white/20 px-3 py-2 rounded-lg text-sm";
    msgDiv.innerText = `${data.user}: ${data.message}`;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
});

socket.on('update_user_list', (data) => {
    const avatarsDiv = document.getElementById('userAvatars');
    avatarsDiv.innerHTML = '';
    data.users.forEach(user => {
        const avatar = document.createElement('img');
        avatar.src = `/static/assets/avatar${(user.charCodeAt(0) % 5) + 1}.png`; // Random avatar
        avatar.alt = user;
        avatarsDiv.appendChild(avatar);
    });
});
