# WebRTC Multi-User Video Streaming Application

A complete peer-to-peer video conferencing application using WebRTC for real-time communication.

## Features

- ✅ Multi-user video and audio streaming (up to 6 users per room)
- ✅ Real-time, low-latency WebRTC connections
- ✅ Peer-to-peer mesh topology (no media through server)
- ✅ Room creation and joining
- ✅ Dynamic video grid layout
- ✅ Audio/Video toggle controls
- ✅ Automatic cleanup on user disconnect
- ✅ Responsive design for mobile devices

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Flask + SocketIO                      │
│                   (Signaling Server)                     │
│  - Room management                                       │
│  - User tracking                                         │
│  - Relay: offers, answers, ICE candidates               │
└─────────────────────────────────────────────────────────┘
         │              │              │
    Signaling      Signaling      Signaling
         │              │              │
         ▼              ▼              ▼
    ┌────────┐    ┌────────┐    ┌────────┐
    │ User A │◄──►│ User B │◄──►│ User C │
    └────────┘    └────────┘    └────────┘
              Direct P2P Media Streams
```

## Tech Stack

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python 3, Flask, Flask-SocketIO
- **Streaming**: WebRTC (RTCPeerConnection)
- **Signaling**: WebSocket via Socket.IO
- **NAT Traversal**: Google STUN servers

## Requirements

- Python 3.8 or higher
- Modern web browser with WebRTC support (Chrome, Firefox, Edge, Safari)
- Camera and microphone

## Local Development

### Windows

1. Double-click `run.bat` or run in terminal:
   ```cmd
   run.bat
   ```

### Linux/macOS

1. Make the script executable and run:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

### Manual Setup

1. Create and activate virtual environment:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the server:
   ```bash
   python app.py
   ```

4. Open http://localhost:5000 in multiple browser tabs

## Testing Locally

1. Open http://localhost:5000 in your first browser tab
2. Enter a username and create a room (or enter a room ID)
3. Open http://localhost:5000 in a second browser tab (or different browser)
4. Enter a different username and join the same room
5. Both users should see each other's video/audio

## Cloud Deployment

### Option 1: DigitalOcean / Linode / AWS EC2

1. Create a VM with Ubuntu 22.04

2. SSH into the server and install dependencies:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv nginx certbot python3-certbot-nginx
   ```

3. Clone or upload the application:
   ```bash
   mkdir -p /var/www/webrtc-video
   cd /var/www/webrtc-video
   # Upload files here
   ```

4. Set up the application:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn
   ```

5. Create systemd service (`/etc/systemd/system/webrtc-video.service`):
   ```ini
   [Unit]
   Description=WebRTC Video Server
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/webrtc-video
   Environment="PATH=/var/www/webrtc-video/venv/bin"
   ExecStart=/var/www/webrtc-video/venv/bin/gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers 1 --bind 0.0.0.0:5000 app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

6. Configure Nginx (`/etc/nginx/sites-available/webrtc-video`):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

7. Enable and start services:
   ```bash
   sudo ln -s /etc/nginx/sites-available/webrtc-video /etc/nginx/sites-enabled/
   sudo systemctl enable webrtc-video
   sudo systemctl start webrtc-video
   sudo systemctl restart nginx
   ```

8. Set up HTTPS (required for WebRTC in production):
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

### Option 2: Heroku

1. Create `Procfile`:
   ```
   web: gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers 1 app:app
   ```

2. Deploy:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

### Option 3: Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--worker-class", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "--workers", "1", "--bind", "0.0.0.0:5000", "app:app"]
```

Build and run:
```bash
docker build -t webrtc-video .
docker run -p 5000:5000 webrtc-video
```

## Important Notes for Production

### HTTPS is Required
WebRTC requires HTTPS in production (except for localhost). Without HTTPS:
- `getUserMedia()` will fail
- Users cannot share camera/microphone

### TURN Server
For production use across different networks, you may need a TURN server for users behind symmetric NATs. Options:
- [Coturn](https://github.com/coturn/coturn) - Self-hosted, free
- [Twilio TURN](https://www.twilio.com/stun-turn) - Paid service
- [Xirsys](https://xirsys.com/) - Free tier available

Add TURN configuration in `index.html`:
```javascript
const CONFIG = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        {
            urls: 'turn:your-turn-server.com:3478',
            username: 'user',
            credential: 'password'
        }
    ]
};
```

## Limitations of Mesh WebRTC

1. **Bandwidth**: Each user sends their stream to all other users. With N users, each uploads N-1 streams.

2. **Scalability**: Mesh works well for 4-6 users. Beyond that, consider:
   - SFU (Selective Forwarding Unit) architecture
   - Commercial solutions like Twilio, Daily.co, Vonage

3. **CPU Usage**: Encoding and decoding multiple streams is CPU-intensive.

4. **NAT Traversal**: Some corporate networks may block P2P connections. TURN server required.

5. **Quality Adaptation**: Basic implementation doesn't adapt quality based on network conditions.

## Browser Compatibility

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | 60+ | ✅ Full Support |
| Firefox | 55+ | ✅ Full Support |
| Safari | 11+ | ✅ Full Support |
| Edge | 79+ | ✅ Full Support |
| Opera | 47+ | ✅ Full Support |

## Troubleshooting

### Camera/Microphone not working
- Check browser permissions
- Ensure HTTPS in production
- Try a different browser

### Users can't connect
- Check firewall settings
- Ensure STUN servers are accessible
- Consider adding TURN server

### High latency
- Check network conditions
- Reduce video resolution in config
- Ensure users are geographically close

## License

MIT License - Feel free to use in your projects!
