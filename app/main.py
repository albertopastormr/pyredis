import socket  # noqa: F401


def main():
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    print("Server started on port 6379")
    client_socket, addr = server_socket.accept()
    print(f"Connected by {addr}")

    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        command = data.decode("utf-8").strip()
        print(f"Received raw: {data}")     # Debugging: See the bytes
        print(f"Decoded: '{command}'")    # Debugging: See the clean string

        if command == "PING":
            client_socket.sendall(b"+PONG\r\n")
        elif command == "SET":
            client_socket.sendall(b"+OK\r\n")
        elif command == "GET":
            client_socket.sendall(b"+OK\r\n")
        else:
            client_socket.sendall(b"-ERR unknown command\r\n")

    client_socket.close()
    server_socket.close()


if __name__ == "__main__":
    main()
