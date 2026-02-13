# PyRedis — A Redis Server Built from Scratch in Python

Ever wondered what happens between typing `SET mykey "hello"` and getting back `OK`? I did — so I built an entire Redis server from scratch to find out.

**PyRedis** is a fully functional Redis server implementation written in Python. It speaks the real RESP (Redis Serialization Protocol) over raw TCP sockets, handles thousands of concurrent connections using a single-threaded `asyncio` event loop, and implements a rich set of Redis commands — all without depending on any Redis libraries.

## What It Supports

- **Strings** with TTL expiration using monotonic clocks and lazy eviction
- **Lists** with blocking pops (`BLPOP`) that suspend the coroutine until data arrives
- **Streams** with auto-generated IDs and blocking reads (`XREAD BLOCK`) via cooperative async waiters
- **Transactions** (`MULTI`/`EXEC`/`DISCARD`) with per-connection command queuing and atomic execution
- **Master-Replica Replication** — a full implementation of the PSYNC handshake, RDB snapshot transfer, real-time write command propagation, offset tracking, and the `WAIT` command for synchronous replication acknowledgments using `asyncio.Condition`

## Why I Built It

I use Redis daily but treated it as a black box. Building it forced me to solve problems that don't appear in typical web development: parsing binary protocols byte by byte, coordinating distributed state across replicas, and designing clean abstractions for a system that needs to be extended with new commands over time.

## How It's Built

The architecture follows a clean layered design. A RESP parser and encoder handle serialization. A command handler dispatches to a registry of self-contained command modules (each Redis command is its own class). A pluggable storage layer manages typed values with TTL support. A replication module handles the master-replica lifecycle end to end. Everything is type-hinted, tested with `pytest-asyncio`, and designed to be read as much as run.

## Tech

Python · asyncio · RESP Protocol · TCP Sockets · Distributed Systems · pytest

[GitHub](https://github.com/albertopastormr/pyredis) · [Deep Dive Blog Post](#)
