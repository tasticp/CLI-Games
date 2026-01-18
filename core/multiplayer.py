"""
Multiplayer support system for CLI Games Launcher.
Handles local multiplayer sessions and basic online features.
"""

import json
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
import socket
import struct

class GameMode(Enum):
    """Multiplayer game modes."""
    LOCAL = "local"
    LAN = "lan"
    ONLINE = "online"
    SPECTATE = "spectate"

class Player:
    """Represents a multiplayer player."""
    
    def __init__(self, name: str, id: str, is_local: bool = True):
        self.name = name
        self.id = id
        self.is_local = is_local
        self.score = 0
        self.ready = False
        self.connected = True
        self.ping = 0
        self.stats = {}
    
    def update_score(self, score: int):
        """Update player score."""
        self.score = score
    
    def set_ready(self, ready: bool):
        """Set player ready status."""
        self.ready = ready
    
    def disconnect(self):
        """Disconnect player."""
        self.connected = False

@dataclass
class GameSession:
    """Represents a multiplayer game session."""
    session_id: str
    game_name: str
    mode: GameMode
    players: List[Player]
    host: str
    max_players: int
    started: bool = False
    created_at: float = 0.0
    settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()
        if self.settings is None:
            self.settings = {}

class NetworkMessage:
    """Network message for multiplayer communication."""
    
    def __init__(self, msg_type: str, data: Dict[str, Any]):
        self.msg_type = msg_type
        self.data = data
        self.timestamp = time.time()
    
    def to_bytes(self) -> bytes:
        """Convert message to bytes for network transmission."""
        msg_dict = {
            'type': self.msg_type,
            'data': self.data,
            'timestamp': self.timestamp
        }
        msg_json = json.dumps(msg_dict)
        return msg_json.encode('utf-8')
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'NetworkMessage':
        """Create message from bytes."""
        try:
            msg_json = data.decode('utf-8')
            msg_dict = json.loads(msg_json)
            return cls(msg_dict['type'], msg_dict['data'])
        except (json.JSONDecodeError, KeyError):
            return None

class MultiplayerManager:
    """Manages multiplayer sessions and networking."""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.sessions: Dict[str, GameSession] = {}
        self.current_session: Optional[GameSession] = None
        self.player: Optional[Player] = None
        self.network_socket: Optional[socket.socket] = None
        self.server_address = None
        self.is_hosting = False
        self.clients: Dict[str, socket.socket] = {}
        self.message_handlers: Dict[str, Callable] = {}
        
        # Register default message handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default network message handlers."""
        self.message_handlers.update({
            'join_request': self._handle_join_request,
            'join_response': self._handle_join_response,
            'game_start': self._handle_game_start,
            'player_update': self._handle_player_update,
            'game_state': self._handle_game_state,
            'disconnect': self._handle_disconnect,
            'chat': self._handle_chat
        })
    
    def create_session(self, game_name: str, mode: GameMode, 
                   max_players: int, settings: Dict[str, Any] = None) -> str:
        """Create a new multiplayer session."""
        import uuid
        session_id = str(uuid.uuid4())[:8]  # Short ID for easier sharing
        
        session = GameSession(
            session_id=session_id,
            game_name=game_name,
            mode=mode,
            players=[],
            host="local",
            max_players=max_players,
            settings=settings or {}
        )
        
        self.sessions[session_id] = session
        self.current_session = session
        
        return session_id
    
    def join_session(self, session_id: str, player_name: str) -> bool:
        """Join an existing session."""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        if len(session.players) >= session.max_players:
            return False
        
        # Create player
        import uuid
        player_id = str(uuid.uuid4())[:8]
        player = Player(player_name, player_id)
        
        session.players.append(player)
        
        if session.mode == GameMode.LOCAL:
            session.started = len(session.players) == session.max_players
        
        return True
    
    def leave_session(self):
        """Leave current session."""
        if not self.current_session:
            return
        
        if self.player:
            # Remove player from session
            self.current_session.players = [
                p for p in self.current_session.players 
                if p.id != self.player.id
            ]
            
            self.player = None
        
        # Clean up empty sessions
        if len(self.current_session.players) == 0:
            del self.sessions[self.current_session.session_id]
            self.current_session = None
    
    def start_local_game(self) -> bool:
        """Start a local multiplayer game."""
        if not self.current_session or self.current_session.mode != GameMode.LOCAL:
            return False
        
        self.current_session.started = True
        return True
    
    def host_lan_game(self, port: int = 7777) -> bool:
        """Host a LAN game."""
        try:
            self.network_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.network_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.network_socket.bind(('', port))
            self.network_socket.listen(5)
            
            self.is_hosting = True
            self.server_address = f"0.0.0.0:{port}"
            
            # Start server in separate thread
            server_thread = threading.Thread(target=self._server_loop, daemon=True)
            server_thread.start()
            
            return True
        except Exception as e:
            print(f"Failed to host game: {e}")
            return False
    
    def join_lan_game(self, address: str, player_name: str) -> bool:
        """Join a LAN game."""
        try:
            host, port = address.split(':')
            port = int(port)
            
            self.network_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.network_socket.connect((host, port))
            
            # Create player
            import uuid
            player_id = str(uuid.uuid4())[:8]
            self.player = Player(player_name, player_id, is_local=False)
            
            # Send join request
            join_msg = NetworkMessage('join_request', {
                'player_name': player_name,
                'player_id': player_id
            })
            
            self._send_message(join_msg)
            
            return True
        except Exception as e:
            print(f"Failed to join game: {e}")
            return False
    
    def _server_loop(self):
        """Server loop for hosting games."""
        while self.is_hosting:
            try:
                client_socket, address = self.network_socket.accept()
                client_id = f"{address[0]}:{address[1]}"
                self.clients[client_id] = client_socket
                
                # Start client handler thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_id),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.is_hosting:
                    print(f"Server error: {e}")
                break
    
    def _handle_client(self, client_socket: socket.socket, client_id: str):
        """Handle a connected client."""
        while self.is_hosting:
            try:
                # Receive message length first
                length_data = client_socket.recv(4)
                if not length_data:
                    break
                
                msg_length = struct.unpack('!I', length_data)[0]
                
                # Receive message data
                msg_data = b''
                while len(msg_data) < msg_length:
                    chunk = client_socket.recv(msg_length - len(msg_data))
                    if not chunk:
                        break
                    msg_data += chunk
                
                if len(msg_data) == msg_length:
                    message = NetworkMessage.from_bytes(msg_data)
                    if message:
                        self._process_message(message, client_id)
                
            except Exception as e:
                print(f"Client handler error: {e}")
                break
            finally:
                # Clean up disconnected client
                if client_id in self.clients:
                    del self.clients[client_id]
                client_socket.close()
    
    def _send_message(self, message: NetworkMessage):
        """Send a network message."""
        if not self.network_socket:
            return
        
        try:
            msg_bytes = message.to_bytes()
            msg_length = struct.pack('!I', len(msg_bytes))
            
            self.network_socket.send(msg_length + msg_bytes)
        except Exception as e:
            print(f"Send error: {e}")
    
    def _process_message(self, message: NetworkMessage, sender_id: str = None):
        """Process received network message."""
        if message.msg_type in self.message_handlers:
            self.message_handlers[message.msg_type](message, sender_id)
    
    def _handle_join_request(self, message: NetworkMessage, sender_id: str):
        """Handle join request from client."""
        player_name = message.data.get('player_name', 'Unknown')
        player_id = message.data.get('player_id', 'unknown')
        
        if self.current_session and len(self.current_session.players) < self.current_session.max_players:
            player = Player(player_name, player_id, is_local=False)
            self.current_session.players.append(player)
            
            # Send join response
            response = NetworkMessage('join_response', {
                'success': True,
                'session_id': self.current_session.session_id,
                'players': len(self.current_session.players)
            })
            
            # Send to all clients
            self._broadcast_to_clients(response)
    
    def _handle_join_response(self, message: NetworkMessage, sender_id: str):
        """Handle join response from server."""
        success = message.data.get('success', False)
        
        if success and self.player:
            print(f"Successfully joined game session!")
    
    def _handle_game_start(self, message: NetworkMessage, sender_id: str):
        """Handle game start message."""
        if self.current_session:
            self.current_session.started = True
            print("Game started!")
    
    def _handle_player_update(self, message: NetworkMessage, sender_id: str):
        """Handle player state updates."""
        # This would be implemented by individual games
        pass
    
    def _handle_game_state(self, message: NetworkMessage, sender_id: str):
        """Handle game state updates."""
        # This would be implemented by individual games
        pass
    
    def _handle_disconnect(self, message: NetworkMessage, sender_id: str):
        """Handle player disconnect."""
        if self.current_session:
            player_id = message.data.get('player_id')
            self.current_session.players = [
                p for p in self.current_session.players 
                if p.id != player_id
            ]
            
            if sender_id in self.clients:
                del self.clients[sender_id]
    
    def _handle_chat(self, message: NetworkMessage, sender_id: str):
        """Handle chat messages."""
        player_name = message.data.get('player_name', 'Unknown')
        chat_text = message.data.get('text', '')
        print(f"[Chat] {player_name}: {chat_text}")
    
    def _broadcast_to_clients(self, message: NetworkMessage):
        """Send message to all connected clients."""
        for client_socket in self.clients.values():
            try:
                msg_bytes = message.to_bytes()
                msg_length = struct.pack('!I', len(msg_bytes))
                client_socket.send(msg_length + msg_bytes)
            except Exception as e:
                print(f"Broadcast error: {e}")
    
    def get_available_sessions(self) -> List[Dict[str, Any]]:
        """Get list of available sessions."""
        sessions = []
        
        for session_id, session in self.sessions.items():
            if session.mode == GameMode.LOCAL:
                sessions.append({
                    'session_id': session_id,
                    'game_name': session.game_name,
                    'mode': session.mode.value,
                    'players': len(session.players),
                    'max_players': session.max_players,
                    'host': session.host,
                    'can_join': len(session.players) < session.max_players
                })
        
        return sessions
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        return {
            'session_id': session.session_id,
            'game_name': session.game_name,
            'mode': session.mode.value,
            'players': [
                {
                    'name': p.name,
                    'id': p.id,
                    'score': p.score,
                    'ready': p.ready,
                    'local': p.is_local
                }
                for p in session.players
            ],
            'max_players': session.max_players,
            'host': session.host,
            'started': session.started,
            'created_at': session.created_at,
            'settings': session.settings
        }
    
    def send_chat_message(self, text: str):
        """Send a chat message."""
        if not self.player or not self.network_socket:
            return
        
        chat_msg = NetworkMessage('chat', {
            'player_name': self.player.name,
            'player_id': self.player.id,
            'text': text
        })
        
        self._send_message(chat_msg)
    
    def disconnect(self):
        """Disconnect from current game."""
        if self.player and self.network_socket:
            # Send disconnect message
            disconnect_msg = NetworkMessage('disconnect', {
                'player_id': self.player.id
            })
            
            self._send_message(disconnect_msg)
            self.network_socket.close()
            self.network_socket = None
        
        if self.is_hosting:
            self.is_hosting = False
            for client_socket in self.clients.values():
                client_socket.close()
            self.clients.clear()
        
        self.player = None
        self.current_session = None
    
    def save_sessions(self):
        """Save active sessions to file."""
        sessions_data = {}
        
        for session_id, session in self.sessions.items():
            if session.mode == GameMode.LOCAL:
                sessions_data[session_id] = {
                    'game_name': session.game_name,
                    'mode': session.mode.value,
                    'players': [
                        {'name': p.name, 'id': p.id, 'score': p.score}
                        for p in session.players
                    ],
                    'max_players': session.max_players,
                    'settings': session.settings,
                    'created_at': session.created_at
                }
        
        # Save to config
        config_data = self.config.load_leaderboard()
        config_data['multiplayer_sessions'] = sessions_data
        self.config.save_leaderboard(config_data)
    
    def load_sessions(self):
        """Load saved sessions."""
        config_data = self.config.load_leaderboard()
        sessions_data = config_data.get('multiplayer_sessions', {})
        
        for session_id, session_data in sessions_data.items():
            # Recreate players
            players = []
            for player_data in session_data.get('players', []):
                player = Player(
                    player_data['name'],
                    player_data['id'],
                    is_local=True
                )
                player.score = player_data.get('score', 0)
                players.append(player)
            
            # Recreate session
            session = GameSession(
                session_id=session_id,
                game_name=session_data['game_name'],
                mode=GameMode(session_data['mode']),
                players=players,
                host="local",
                max_players=session_data['max_players'],
                settings=session_data.get('settings', {}),
                created_at=session_data.get('created_at', time.time())
            )
            
            self.sessions[session_id] = session
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get multiplayer statistics."""
        total_sessions = len(self.sessions)
        local_sessions = len([s for s in self.sessions.values() if s.mode == GameMode.LOCAL])
        
        active_players = sum(len(s.players) for s in self.sessions.values())
        unique_players = len(set(
            p.id for session in self.sessions.values()
            for p in session.players
        ))
        
        return {
            'total_sessions': total_sessions,
            'local_sessions': local_sessions,
            'lan_sessions': total_sessions - local_sessions,
            'active_players': active_players,
            'unique_players': unique_players,
            'is_hosting': self.is_hosting,
            'connected_players': len(self.clients) if self.is_hosting else 0,
            'current_session': self.current_session.session_id if self.current_session else None
        }