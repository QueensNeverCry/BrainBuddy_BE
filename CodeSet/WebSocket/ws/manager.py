from typing import Dict
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        # user_name -> WebSocket
        self.connections: Dict[str, WebSocket] = {}

    def connect(self, user_name: str, websocket: WebSocket) -> None:
        client_host, client_port = websocket.client
        print(f"{user_name} has connected from {client_host}:{client_port}")
        self.connections[user_name] = websocket

    def disconnect(self, user_name: str) -> None:
        self.connections.pop(user_name, None)

    def get_connection(self, user_name: str) -> WebSocket | None:
        return self.connections.get(user_name)

    async def send_personal_message(self, user_name: str, message: str) -> None:
        websocket = self.get_connection(user_name)
        if websocket:
            await websocket.send_json(message)

    async def broadcast(self, message: str) -> None:
        for websocket in self.active_connections.values():
            await websocket.send_json(message)

