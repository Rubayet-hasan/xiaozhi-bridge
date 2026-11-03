import asyncio
import json
import threading
import requests
import websockets
from flask import Flask
import os

app = Flask('')

@app.route('/')
def home():
    return "Render MCP Bridge Server is Live!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ⚠️ আপনার Xiaozhi MCP টোকেনটি এখানে বসাবেন
XIAOZHI_TOKEN = "wss://api.xiaozhi.me/mcp/?token=eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjExNDgxMzYsImFnZW50SWQiOjI1ODU4MTksImVuZHBvaW50SWQiOiJhZ2VudF8yNTg1ODE5IiwicHVycG9zZSI6Im1jcC1lbmRwb2ludCIsImlhdCI6MTc5MzcyMTQwNiwiZXhwIjoxODI1Mjc5MDA2fQ.rk3EemCvk6JcxHGVMuguLSsT0KWzTRXXpHDSPr0TSl6QXMr3H1U8zkUYzYGyfOoJ4rSFFswp6Cs0aKVPInlxOA" 
BLYNK_TOKEN = "5LoTt2CBH3kqC6ZbJ0qM9qstNigAFClw"

def send_to_blynk(state_value):
    url = f"https://blynk.cloud/external/api/update?token={BLYNK_TOKEN}&v1={state_value}"
    try:
        response = requests.get(url)
        return response.status_code == 200
    except Exception:
        return False

async def connect_xiaozhi_mcp():
    ws_url = f"wss://api.xiaozhi.me/mcp/?token={XIAOZHI_TOKEN}"
    while True:
        try:
            async with websockets.connect(ws_url) as ws:
                print("Connected to Xiaozhi MCP!")
                tool_registration = {
                    "type": "register_tools",
                    "tools": [{
                        "name": "control_esp8266_led",
                        "description": "Control ESP8266 LED light state",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "state": {"type": "integer", "enum": [0, 1]}
                            },
                            "required": ["state"]
                        }
                    }]
                }
                await ws.send(json.dumps(tool_registration))

                while True:
                    message = await ws.recv()
                    data = json.loads(message)
                    if data.get("type") == "call_tool" and data.get("name") == "control_esp8266_led":
                        state_val = data["args"]["state"]
                        success = send_to_blynk(state_val)
                        result_payload = {
                            "type": "tool_result",
                            "call_id": data.get("call_id"),
                            "result": "Success" if success else "Failed"
                        }
                        await ws.send(json.dumps(result_payload))
        except Exception:
            await asyncio.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    asyncio.run(connect_xiaozhi_mcp())
