from typing import Dict, Any
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        # user_name -> WebSocket
        self.connections: Dict[str, WebSocket] = {}

    def connect(self, user_name: str, websocket: WebSocket) -> None:
        client_host, client_port = websocket.client
        print(f"[LOG] : {user_name} has connected from {client_host}:{client_port}")
        self.connections[user_name] = websocket

    def disconnect(self, user_name: str) -> None:
        self.connections.pop(user_name, None)

    def get_connection(self, user_name: str) -> WebSocket | None:
        return self.connections.get(user_name)

    async def send_current_focus(self, user_name: str, focus: int) -> None:
        websocket = self.get_connection(user_name)
        if websocket:
            print(f"[LOG] :     Manager send {user_name} - focus : {focus}")
            await websocket.send_json({"focus": focus})
