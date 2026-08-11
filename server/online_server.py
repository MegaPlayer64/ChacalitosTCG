import asyncio
import json
import uuid
import random
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Room:
    def __init__(self, room_id, p1_writer, p2_writer):
        self.room_id = room_id
        self.p1_writer = p1_writer
        self.p2_writer = p2_writer

class RoomManager:
    def __init__(self):
        self.waiting_player = None
        self.rooms = {}
        self.client_to_room = {}

    def get_room(self, writer):
        return self.client_to_room.get(writer)

    async def matchmake(self, writer, player_name, deck):
        if self.waiting_player is None:
            logging.info(f"Jugador '{player_name}' esperando partida...")
            self.waiting_player = (writer, player_name, deck)
            return None
        else:
            if self.waiting_player[0] == writer:
                return None
                
            p1_writer, p1_name, p1_deck = self.waiting_player
            p2_writer = writer
            p2_name = player_name
            p2_deck = deck
            self.waiting_player = None
            
            room_id = str(uuid.uuid4())
            room = Room(room_id, p1_writer, p2_writer)
            self.rooms[room_id] = room
            self.client_to_room[p1_writer] = room
            self.client_to_room[p2_writer] = room
            
            logging.info(f"Partida encontrada: Sala {room_id} | {p1_name} vs {p2_name}")
            
            # Asignar roles aleatoriamente
            if random.choice([True, False]):
                p1_role, p2_role = 0, 1
            else:
                p1_role, p2_role = 1, 0
                
            # Generar semilla de aleatoriedad para sincronizar las barajas
            game_seed = random.randint(1, 999999)
            
            # Enviar MATCH_FOUND
            await send_message(p1_writer, {
                "type": "MATCH_FOUND",
                "room_id": room_id,
                "player_role": p1_role,
                "opponent_name": p2_name,
                "opponent_deck": p2_deck,
                "seed": game_seed
            })
            await send_message(p2_writer, {
                "type": "MATCH_FOUND",
                "room_id": room_id,
                "player_role": p2_role,
                "opponent_name": p1_name,
                "opponent_deck": p1_deck,
                "seed": game_seed
            })
            
            # Avisar a quien empieza el turno
            await send_message(p1_writer, {"type": "START_TURN", "active_player": 0})
            await send_message(p2_writer, {"type": "START_TURN", "active_player": 0})
            
            return room

    async def handle_disconnect(self, writer):
        room = self.client_to_room.get(writer)
        if room:
            opponent_writer = room.p2_writer if writer == room.p1_writer else room.p1_writer
            if opponent_writer:
                try:
                    await send_message(opponent_writer, {"type": "OPPONENT_DISCONNECTED"})
                except:
                    pass
            del self.rooms[room.room_id]
            self.client_to_room.pop(room.p1_writer, None)
            self.client_to_room.pop(room.p2_writer, None)
            logging.info(f"Sala {room.room_id} destruida por desconexión.")
        elif self.waiting_player and self.waiting_player[0] == writer:
            self.waiting_player = None
            logging.info("Jugador en espera se desconectó.")

room_manager = RoomManager()

async def send_message(writer, msg_dict):
    try:
        data = json.dumps(msg_dict).encode('utf-8')
        writer.write(data + b'\n')
        await writer.drain()
    except Exception as e:
        logging.error(f"Error al enviar mensaje: {e}")

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    logging.info(f"Nueva conexión desde {addr}")
    
    try:
        while True:
            try:
                data = await reader.readline()
                if not data:
                    break
                    
                try:
                    msg = json.loads(data.decode('utf-8'))
                except json.JSONDecodeError:
                    logging.error(f"JSON inválido desde {addr}")
                    continue
                    
                msg_type = msg.get("type")
                
                if msg_type == "JOIN_QUEUE":
                    await room_manager.matchmake(writer, msg.get("player_name", "Desconocido"), msg.get("deck", []))
                    
                elif msg_type == "GAME_ACTION" or msg_type == "END_TURN":
                    room = room_manager.get_room(writer)
                    if room:
                        opponent_writer = room.p2_writer if writer == room.p1_writer else room.p1_writer
                        # Retransmitir al oponente cambiando type a OPPONENT_ACTION (o END_TURN se deja igual y se avisa START_TURN en el servidor... no, el servidor solo hace relay por ahora)
                        if msg_type == "GAME_ACTION":
                            relay_msg = {
                                "type": "OPPONENT_ACTION",
                                "action": msg.get("action"),
                                "data": msg.get("data")
                            }
                        else:
                            relay_msg = msg # END_TURN
                            
                        await send_message(opponent_writer, relay_msg)
            except (ConnectionResetError, asyncio.IncompleteReadError, OSError, ConnectionAbortedError) as e:
                logging.warning(f"Desconexión abrupta detectada de {addr}: {e}")
                break
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"Excepción con cliente {addr}: {e}")
    finally:
        logging.info(f"Desconexión de {addr}")
        await room_manager.handle_disconnect(writer)
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

async def main():
    host = '0.0.0.0'
    port = 8888
    server = await asyncio.start_server(handle_client, host, port)
    
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logging.info(f'Servidor escuchando en {addrs}')
    
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
