from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_socketio import SocketIO, join_room, leave_room, emit
from database.models import SessionLocal, Document, Version
import datetime, random, string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key'
socketio = SocketIO(app)

# Active Users and Room Tracking
active_users = {}  # { room_name: { sid: username } }
cursor_positions = {}  # { room_name: { username: offset } }
existing_rooms = {}  # { room_id: { 'room_name': str, 'email': str } }

# ------------------ Routes ------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_room', methods=['POST'])
def create_room():
    name = request.form['name']
    email = request.form['email']
    room_name = request.form['room_name']

    # Generate Unique Room ID
    room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    existing_rooms[room_id] = {'room_name': room_name, 'email': email}

    # Save Document Entry in DB (Optional: can skip if just in-memory)
    db = SessionLocal()
    doc = Document(room_name=room_id, content='')
    db.add(doc)
    db.commit()
    db.close()

    # Confirmation Page with Room ID
    return render_template('room_created.html', room_id=room_id, room_name=room_name, email=email)

@app.route('/join_room', methods=['POST'])
def join_room_route():
    room_id = request.form['room_id']
    if room_id in existing_rooms:
        return redirect(url_for('room', room_name=room_id))
    else:
        flash('Invalid Room ID. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/room/<room_name>')
def room(room_name):
    db = SessionLocal()
    doc = db.query(Document).filter(Document.room_name == room_name).first()
    saved_content = doc.content if doc else ''
    db.close()
    return render_template('room.html', room_name=room_name, saved_content=saved_content)

@app.route('/versions/<room_name>')
def get_versions(room_name):
    db = SessionLocal()
    versions = db.query(Version).filter(Version.room_name == room_name).order_by(Version.saved_at.desc()).limit(10).all()
    db.close()
    return jsonify({
        'versions': [
            {'content': v.content, 'saved_at': v.saved_at.strftime("%Y-%m-%d %H:%M:%S")}
            for v in versions
        ]
    })
@app.route('/create')
def create():
    return render_template('index.html')  # Placeholder page for + New Room

@app.route('/documents')
def documents():
    return render_template('documents.html')

@app.route("/my_rooms_page")
def my_rooms_page():
    return render_template("my_rooms.html")


@app.route('/activity')
def activity():
    return render_template('activity.html')

@app.route('/settings')
def settings():
    # Dummy settings data — replace with real DB/user settings if needed
    user_settings = {
        'dark_mode': False,  # or True if enabled
    }
    return render_template('settings.html', settings=user_settings)


# ------------------ Socket.IO Events ------------------

@socketio.on('connect')
def handle_connect():
    print(f'User connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    print(f'User disconnected: {sid}')
    for room in list(active_users.keys()):
        if sid in active_users[room]:
            username = active_users[room].pop(sid)
            emit('update_user_list', {'users': list(active_users[room].values())}, to=room)
        if not active_users[room]:
            del active_users[room]

@socketio.on('join')
def handle_join(data):
    room = data['room']
    username = data.get('username', 'Anonymous')
    sid = request.sid
    join_room(room)

    if room not in active_users:
        active_users[room] = {}
    active_users[room][sid] = username

    print(f"{username} joined room: {room}")
    emit('update_user_list', {'users': list(active_users[room].values())}, to=room)

    # Send Current Document Content
    db = SessionLocal()
    doc = db.query(Document).filter(Document.room_name == room).first()
    saved_content = doc.content if doc else ''
    db.close()
    emit('receive_update', {'content': saved_content}, to=sid)

@socketio.on('text_update')
def handle_text_update(data):
    room = data['room']
    content = data['content']

    db = SessionLocal()
    doc = db.query(Document).filter(Document.room_name == room).first()
    if doc:
        doc.content = content
        doc.updated_at = datetime.datetime.utcnow()
    else:
        doc = Document(room_name=room, content=content)
        db.add(doc)
    db.commit()

    version = Version(room_name=room, content=content)
    db.add(version)
    db.commit()
    db.close()

    emit('receive_update', {'content': content}, to=room, include_self=False)

@socketio.on('cursor_position')
def handle_cursor_position(data):
    room = data['room']
    username = data['username']
    offset = data['offset']

    if room not in cursor_positions:
        cursor_positions[room] = {}
    cursor_positions[room][username] = offset

    emit('update_cursors', {'cursors': [
        {'username': user, 'offset': pos} for user, pos in cursor_positions[room].items()
    ]}, to=room)

@socketio.on('send_message')
def handle_send_message(data):
    room = data['room']
    message = data['message']
    username = active_users[room].get(request.sid, 'Anonymous')
    emit('receive_message', {'user': username, 'message': message}, to=room)

# ------------------ Main ------------------
if __name__ == '__main__':
    socketio.run(app, debug=True)
