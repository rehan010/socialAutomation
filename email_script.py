import asyncio
import aioreloader
from aiosmtpd.controller import Controller

async def handle_message(server, session, envelope, **kwargs):
    print(f"New message received: {envelope.message}")

async def start_debugging_server():
    controller = Controller(handle_message, hostname="localhost", port=1025)
    controller.start()

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    aioreloader.start()
    asyncio.run(start_debugging_server())
