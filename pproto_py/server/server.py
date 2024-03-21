import asyncio


class Server:
    def __init__(self, host="127.0.0.1", port=8888) -> None:
        self.__host = host
        self.__port = port

    async def __handle_coroutine(self, reader, writer):
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info("peername")
        print(f"Received {message!r} from {addr!r}")
        print(f"Send: {message!r}")
        writer.write(data)
        await writer.drain()
        print("Close the connection")
        writer.close()
        await writer.wait_closed()

    async def run(self):
        server = await asyncio.start_server(self.__handle_coroutine, self.__host, self.__port)
        addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
        print(f"Serving on {addrs}")
        async with server:
            await server.serve_forever()


async def main():
    server = Server()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
