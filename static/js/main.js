const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

const ROOM_NAME = window.location.pathname.split('/').pop();
const USERNAME = 'User' + Math.floor(Math.random() * 10000);

// Elements
const editor = document.getElementById('editor');
const chatInput = document.getElementById('chatInput');
const chatBox = document.getElementById('chatBox');
const usersList = document.getElementById('usersList');
const userAvatars = document.getElementById('userAvatars');

// Join Room with Username
socket.emit('join', { room: ROOM_NAME, username: USERNAME });

// Emit Document Update on Typing (Debounced)
let typingTimer;
editor.addEventListener('input', () => {
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => {
        const content = editor.innerHTML;
        socket.emit('text_update', { room: ROOM_NAME, content: content });
    }, 300);
});

// Receive Document Updates from Server
socket.on('receive_update', (data) => {
    if (editor.innerHTML !== data.content) {
        editor.innerHTML = data.content;
    }
});

// Send Chat Message
function sendMessage() {
    const message = chatInput.value.trim();
    if (message) {
        socket.emit('send_message', { room: ROOM_NAME, message: message, username: USERNAME });
        chatInput.value = '';
    }
}

// Receive Chat Messages
socket.on('receive_message', (data) => {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('bg-white/30', 'rounded-md', 'px-3', 'py-2', 'mb-2', 'break-words');
    msgDiv.innerHTML = `<strong>${data.username}</strong>: ${data.message}`;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
});

// Update Active Users List
socket.on('update_user_list', (data) => {
    usersList.innerHTML = '';
    userAvatars.innerHTML = '';

    data.users.forEach(user => {
        // Active User List
        const li = document.createElement('li');
        li.classList.add('flex', 'items-center', 'gap-2');
        li.innerHTML = `<span class="h-3 w-3 bg-green-400 rounded-full animate-pulse"></span> ${user}`;
        usersList.appendChild(li);

        // Live Presence Avatar
        const avatar = document.createElement('div');
        avatar.classList.add('w-8', 'h-8', 'rounded-full', 'border-2', 'border-white', 'bg-gradient-to-br', 'from-indigo-400', 'to-purple-500');
        userAvatars.appendChild(avatar);
    });
});

// Capture cursor position on selection change
editor.addEventListener('mouseup', sendCursorPosition);
editor.addEventListener('keyup', sendCursorPosition);

function sendCursorPosition() {
    const selection = window.getSelection();
    if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        const offset = range.startOffset;

        socket.emit('cursor_position', { room: ROOM_NAME, username: USERNAME, offset: offset });
    }
}

// Listen for cursor updates from server
socket.on('update_cursors', (data) => {
    const cursorContainer = document.getElementById('cursorContainer');
    cursorContainer.innerHTML = '';  // Clear existing cursors

    data.cursors.forEach(cursor => {
        if (cursor.username !== USERNAME) {  // Skip own cursor
            const span = document.createElement('span');
            span.classList.add('cursor-indicator');
            span.style.left = `${cursor.offset * 7}px`;  // Approximate positioning
            span.innerHTML = `<span class="cursor-name">${cursor.username}</span>`;
            cursorContainer.appendChild(span);
        }
    });
});


// Fetch Version History & Restore
function fetchVersions() {
    fetch(`/versions/${ROOM_NAME}`)
        .then(response => response.json())
        .then(data => {
            const versionList = document.getElementById('versionList');
            versionList.innerHTML = '';
            data.versions.forEach(version => {
                const btn = document.createElement('button');
                btn.innerText = `Restore @ ${version.saved_at}`;
                btn.classList.add('block', 'w-full', 'text-left', 'hover:bg-indigo-100', 'p-2', 'rounded');
                btn.onclick = () => {
                    editor.innerHTML = version.content;
                    socket.emit('text_update', { room: ROOM_NAME, content: version.content });
                    closeModal();
                };
                versionList.appendChild(btn);
            });
            document.getElementById('versionModal').classList.remove('hidden');
        });
}

function closeModal() {
    document.getElementById('versionModal').classList.add('hidden');
}

// (Optional Future Enhancements)
// TODO: Add Typing Indicators
// TODO: Add User Color Badges or Custom Avatars
// TODO: Handle Connection Rejoin Logic
