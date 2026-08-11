import socket
import threading
import json
import logging
from kivy.clock import Clock

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class OnlineController:
    def __init__(self):
        self.sock = None
        self.connected = False
        self._listen_thread_handle = None
        
        # Callbacks para la UI
        self.on_match_found = None
        self.on_opponent_action = None
        self.on_start_turn = None
        self.on_disconnect = None

    def connect(self, host, port, player_name):
        """Conecta al servidor en segundo plano."""
        if self.connected:
            logging.warning("Ya estás conectado.")
            return

        def _connect_task():
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(10.0) # Timeout inicial para conexión
                self.sock.connect((host, port))
                self.sock.settimeout(None) # Bloqueo indefinido para el loop
                self.connected = True
                self.player_name = player_name
                logging.info(f"Conectado a {host}:{port} como {player_name}")
                
                # Iniciar hilo de escucha
                self._listen_thread_handle = threading.Thread(target=self._listen_thread, daemon=True)
                self._listen_thread_handle.start()
                
            except Exception as e:
                logging.error(f"Error al conectar: {e}")
                self.connected = False
                if self.sock:
                    self.sock.close()
                    
        threading.Thread(target=_connect_task, daemon=True).start()

    def join_matchmaking(self, deck):
        """Envía solicitud para buscar partida."""
        if not self.connected:
            logging.error("No se puede buscar partida: No conectado.")
            return
            
        payload = {
            "type": "JOIN_QUEUE",
            "player_name": getattr(self, 'player_name', 'Jugador'),
            "deck": deck
        }
        self._send_raw(payload)

    def send_action(self, action_type, payload_data):
        """Envía una acción de juego al servidor."""
        if not self.connected:
            return
            
        if action_type == "END_TURN":
            msg = {"type": "END_TURN"}
        else:
            msg = {
                "type": "GAME_ACTION",
                "action": action_type,
                "data": payload_data
            }
        self._send_raw(msg)

    def _send_raw(self, msg_dict):
        try:
            data = json.dumps(msg_dict).encode('utf-8') + b'\n'
            self.sock.sendall(data)
        except Exception as e:
            logging.error(f"Error al enviar datos: {e}")
            self.disconnect()

    def _listen_thread(self):
        """Hilo dedicado a escuchar mensajes del servidor de forma asíncrona."""
        file_obj = self.sock.makefile('rb')
        try:
            while self.connected:
                line = file_obj.readline()
                if not line:
                    break
                
                try:
                    msg = json.loads(line.decode('utf-8'))
                    self._handle_message(msg)
                except json.JSONDecodeError:
                    logging.error("Recibido JSON inválido del servidor.")
        except Exception as e:
            if self.connected:
                logging.error(f"Conexión perdida: {e}")
        finally:
            self.disconnect()
            if self.on_disconnect:
                Clock.schedule_once(lambda dt: self.on_disconnect(), 0)

    def _handle_message(self, msg):
        """Redirige el mensaje al callback correspondiente en el hilo principal."""
        msg_type = msg.get("type")
        
        if msg_type == "MATCH_FOUND":
            if self.on_match_found:
                Clock.schedule_once(lambda dt: self.on_match_found(msg), 0)
                
        elif msg_type == "OPPONENT_ACTION" or msg_type == "END_TURN":
            if self.on_opponent_action:
                Clock.schedule_once(lambda dt: self.on_opponent_action(msg), 0)
                
        elif msg_type == "START_TURN":
            if self.on_start_turn:
                Clock.schedule_once(lambda dt: self.on_start_turn(msg), 0)
                
        elif msg_type == "OPPONENT_DISCONNECTED":
            if self.on_disconnect:
                Clock.schedule_once(lambda dt: self.on_disconnect(msg), 0)

    def disconnect(self):
        """Cierra el socket y limpia el estado."""
        self.connected = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except:
                pass
            self.sock = None
        logging.info("Desconectado del servidor.")
