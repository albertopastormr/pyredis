import socket  # noqa: F401


def main():
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    print("Server started on port 6379")
    client_socket, addr = server_socket.accept()
    print(f"Connected by {addr}")
    
    client_socket.close()
    server_socket.close()


if __name__ == "__main__":
    main()
