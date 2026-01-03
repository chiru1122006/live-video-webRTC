"""
WebRTC Multi-User Video Streaming - Signaling Server
=====================================================
This Flask server handles ONLY signaling for WebRTC connections.
No media streams pass through this server - all video/audio is peer-to-peer.
"""

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'webrtc-video-secret-key-change-in-production'

# Initialize SocketIO with WebSocket transport
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# In-memory room management
# Structure: { room_id: { user_id: { 'username': str, 'sid': str } } }
rooms = {}


@app.route('/')
def index():
    """Serve the main application page."""
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connection."""
    logger.info(f"Client connected: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection - clean up user from all rooms."""
    sid = request.sid
    logger.info(f"Client disconnected: {sid}")
    
    # Find and remove user from their room
    for room_id in list(rooms.keys()):
        room = rooms[room_id]
        for user_id in list(room.keys()):
            if room[user_id]['sid'] == sid:
                username = room[user_id]['username']
                del room[user_id]
                
                # Notify other users in the room
                emit('user-left', {
                    'userId': user_id,
                    'username': username
                }, room=room_id)
                
                logger.info(f"User {username} ({user_id}) left room {room_id}")
                
                # Clean up empty rooms
                if not room:
                    del rooms[room_id]
                    logger.info(f"Room {room_id} deleted (empty)")
                
                return


@socketio.on('join-room')
def handle_join_room(data):
    """
    Handle user joining a room.
    Creates the room if it doesn't exist.
    Notifies existing users about the new user.
    Sends list of existing users to the new user.
    """
    room_id = data['roomId']
    user_id = data['userId']
    username = data['username']
    sid = request.sid
    
    logger.info(f"User {username} ({user_id}) joining room {room_id}")
    
    # Create room if it doesn't exist
    if room_id not in rooms:
        rooms[room_id] = {}
        logger.info(f"Created new room: {room_id}")
    
    # Check room capacity (max 6 users for mesh topology)
    if len(rooms[room_id]) >= 6:
        emit('room-full', {'message': 'Room is full (max 6 users)'})
        return
    
    # Get existing users before adding new user
    existing_users = [
        {'userId': uid, 'username': info['username']}
        for uid, info in rooms[room_id].items()
    ]
    
    # Add new user to room
    rooms[room_id][user_id] = {
        'username': username,
        'sid': sid
    }
    
    # Join the SocketIO room
    join_room(room_id)
    
    # Send existing users to the new user
    emit('existing-users', {'users': existing_users})
    
    # Notify existing users about the new user
    emit('user-joined', {
        'userId': user_id,
        'username': username
    }, room=room_id, skip_sid=sid)
    
    logger.info(f"Room {room_id} now has {len(rooms[room_id])} users")


@socketio.on('leave-room')
def handle_leave_room(data):
    """Handle user explicitly leaving a room."""
    room_id = data['roomId']
    user_id = data['userId']
    
    if room_id in rooms and user_id in rooms[room_id]:
        username = rooms[room_id][user_id]['username']
        del rooms[room_id][user_id]
        
        leave_room(room_id)
        
        # Notify other users
        emit('user-left', {
            'userId': user_id,
            'username': username
        }, room=room_id)
        
        logger.info(f"User {username} ({user_id}) left room {room_id}")
        
        # Clean up empty rooms
        if not rooms[room_id]:
            del rooms[room_id]
            logger.info(f"Room {room_id} deleted (empty)")


@socketio.on('offer')
def handle_offer(data):
    """
    Relay WebRTC offer to specific peer.
    The offer contains the SDP (Session Description Protocol) for the connection.
    """
    room_id = data['roomId']
    target_user_id = data['targetUserId']
    
    if room_id in rooms and target_user_id in rooms[room_id]:
        target_sid = rooms[room_id][target_user_id]['sid']
        emit('offer', {
            'offer': data['offer'],
            'fromUserId': data['fromUserId'],
            'fromUsername': data['fromUsername']
        }, room=target_sid)
        logger.debug(f"Relayed offer from {data['fromUserId']} to {target_user_id}")


@socketio.on('answer')
def handle_answer(data):
    """
    Relay WebRTC answer to specific peer.
    The answer is the response to an offer, completing the SDP exchange.
    """
    room_id = data['roomId']
    target_user_id = data['targetUserId']
    
    if room_id in rooms and target_user_id in rooms[room_id]:
        target_sid = rooms[room_id][target_user_id]['sid']
        emit('answer', {
            'answer': data['answer'],
            'fromUserId': data['fromUserId']
        }, room=target_sid)
        logger.debug(f"Relayed answer from {data['fromUserId']} to {target_user_id}")


@socketio.on('ice-candidate')
def handle_ice_candidate(data):
    """
    Relay ICE candidate to specific peer.
    ICE candidates are used for NAT traversal and connectivity checks.
    """
    room_id = data['roomId']
    target_user_id = data['targetUserId']
    
    if room_id in rooms and target_user_id in rooms[room_id]:
        target_sid = rooms[room_id][target_user_id]['sid']
        emit('ice-candidate', {
            'candidate': data['candidate'],
            'fromUserId': data['fromUserId']
        }, room=target_sid)
        logger.debug(f"Relayed ICE candidate from {data['fromUserId']} to {target_user_id}")


@socketio.on('get-room-info')
def handle_get_room_info(data):
    """Return information about a specific room."""
    room_id = data.get('roomId')
    
    if room_id and room_id in rooms:
        emit('room-info', {
            'roomId': room_id,
            'userCount': len(rooms[room_id]),
            'users': [info['username'] for info in rooms[room_id].values()]
        })
    else:
        emit('room-info', {
            'roomId': room_id,
            'userCount': 0,
            'users': []
        })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("WebRTC Multi-User Video Streaming Server")
    print("="*60)
    print("Server starting on http://localhost:5000")
    print("Open this URL in multiple browser tabs to test")
    print("="*60 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
