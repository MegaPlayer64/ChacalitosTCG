import json
import uuid
import random
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter()


class Room:
    def __init__(self, room_id: str, p1_ws: WebSocket, p2_ws: WebSocket):
        self.room_id = room_id
        self.p1_ws = p1_ws
        self.p2_ws = p2_ws


class RoomManager:
    def __init__(self):
        self.waiting_player = None
        self.rooms = {}
        self.client_to_room = {}

    def get_room(self, ws: WebSocket):
        return self.client_to_room.get(ws)

    async def matchmake(self, ws: WebSocket, player_name: str, deck: list):
        if self.waiting_player is None:
            logging.info(f"Jugador '{player_name}' esperando partida...")
            self.waiting_player = (ws, player_name, deck)
            return None
        else:
            if self.waiting_player[0] == ws:
                return None

            p1_ws, p1_name, p1_deck = self.waiting_player
            p2_ws = ws
            p2_name = player_name
            p2_deck = deck
            self.waiting_player = None

            room_id = str(uuid.uuid4())
            room = Room(room_id, p1_ws, p2_ws)
            self.rooms[room_id] = room
            self.client_to_room[p1_ws] = room
            self.client_to_room[p2_ws] = room

            logging.info(f"Partida encontrada: Sala {room_id} | {p1_name} vs {p2_name}")

            # Asignar roles aleatoriamente
            if random.choice([True, False]):
                p1_role, p2_role = 0, 1
            else:
                p1_role, p2_role = 1, 0

            # Generar semilla de aleatoriedad para sincronizar las barajas
            game_seed = random.randint(1, 999999)

            # Enviar MATCH_FOUND
            await send_message(p1_ws, {
                "type": "MATCH_FOUND",
                "room_id": room_id,
                "player_role": p1_role,
                "opponent_name": p2_name,
                "opponent_deck": p2_deck,
                "seed": game_seed
            })
            await send_message(p2_ws, {
                "type": "MATCH_FOUND",
                "room_id": room_id,
                "player_role": p2_role,
                "opponent_name": p1_name,
                "opponent_deck": p1_deck,
                "seed": game_seed
            })

            # Avisar a quien empieza el turno
            await send_message(p1_ws, {"type": "START_TURN", "active_player": 0})
            await send_message(p2_ws, {"type": "START_TURN", "active_player": 0})

            return room

    async def handle_disconnect(self, ws: WebSocket):
        room = self.client_to_room.get(ws)
        if room:
            opponent_ws = room.p2_ws if ws == room.p1_ws else room.p1_ws
            if opponent_ws:
                await send_message(opponent_ws, {"type": "OPPONENT_DISCONNECTED"})

            self.rooms.pop(room.room_id, None)
            self.client_to_room.pop(room.p1_ws, None)
            self.client_to_room.pop(room.p2_ws, None)
            logging.info(f"Sala {room.room_id} destruida por desconexión.")
        elif self.waiting_player and self.waiting_player[0] == ws:
            self.waiting_player = None
            logging.info("Jugador en espera se desconectó.")


room_manager = RoomManager()


async def send_message(ws: WebSocket, msg_dict: dict):
    try:
        await ws.send_json(msg_dict)
    except Exception as e:
        logging.error(f"Error al enviar mensaje WebSocket: {e}")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_host = websocket.client.host if websocket.client else "desconocido"
    logging.info(f"Nueva conexión WebSocket desde {client_host}")

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                msg = json.loads(raw_data)
            except json.JSONDecodeError:
                logging.error(f"JSON inválido desde {client_host}")
                continue

            msg_type = msg.get("type")

            if msg_type == "JOIN_QUEUE":
                await room_manager.matchmake(
                    websocket,
                    msg.get("player_name", "Desconocido"),
                    msg.get("deck", [])
                )

            elif msg_type in ("GAME_ACTION", "END_TURN"):
                room = room_manager.get_room(websocket)
                if room:
                    opponent_ws = room.p2_ws if websocket == room.p1_ws else room.p1_ws
                    if msg_type == "GAME_ACTION":
                        relay_msg = {
                            "type": "OPPONENT_ACTION",
                            "action": msg.get("action"),
                            "data": msg.get("data")
                        }
                    else:
                        relay_msg = msg  # END_TURN

                    await send_message(opponent_ws, relay_msg)

    except WebSocketDisconnect:
        logging.info(f"Cliente WebSocket desconectado: {client_host}")
    except Exception as e:
        logging.warning(f"Desconexión abrupta de {client_host}: {e}")
    finally:
        await room_manager.handle_disconnect(websocket)