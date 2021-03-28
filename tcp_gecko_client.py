
from typing import Optional
import socket
from enum import IntEnum
import struct
import time

TCPGECKO_TCP_PORT = 7331
TCPGECKO_PACKET_SIZE = 0x400
TCPGECKO_BLOCK_ZERO_PREFIX = 0xB0.to_bytes(1, 'big')


class TCPGeckoClient:
    class Commands(IntEnum):
        WRITE_8 = 0x01
        WRITE_16 = 0x02
        WRITE_32 = 0x03
        READ_MEMORY = 0x04
        READ_MEMORY_KERNEL = 0x05
        VALIDATE_ADDRESS_RANGE = 0x06
        MEMORY_DISASSEMBLE = 0x08
        READ_MEMORY_COMPRESSED = 0x09
        KERNEL_WRITE = 0x0B
        KERNEL_READ = 0x0C
        TAKE_SCREEN_SHOT = 0x0D
        UPLOAD_MEMORY = 0x41
        SERVER_STATUS = 0x50
        GET_DATA_BUFFER_SIZE = 0x51
        READ_FILE = 0x52
        READ_DIRECTORY = 0x53
        REPLACE_FILE = 0x54
        GET_CODE_HANDLER_ADDRESS = 0x55
        READ_THREADS = 0x56
        ACCOUNT_IDENTIFIER = 0x57
        FOLLOW_POINTER = 0x60
        REMOTE_PROCEDURE_CALL = 0x70
        GET_SYMBOL = 0x71
        MEMORY_SEARCH_32 = 0x72
        ADVANCED_MEMORY_SEARCH = 0x73
        EXECUTE_ASSEMBLY = 0x81
        PAUSE_CONSOLE = 0x82
        RESUME_CONSOLE = 0x83
        IS_CONSOLE_PAUSED = 0x84
        SERVER_VERSION = 0x99
        GET_OS_VERSION = 0x9A
        SET_DATA_BREAKPOINT = 0xA0
        SET_INSTRUCTION_BREAKPOINT = 0xA2
        TOGGLE_BREAKPOINT = 0xA5
        REMOVE_ALL_BREAKPOINTS = 0xA6
        POKE_REGISTERS = 0xA7
        GET_STACK_TRACE = 0xA8
        GET_ENTRY_POINT_ADDRESS = 0xB1
        RUN_KERNEL_COPY_SERVICE = 0xCD
        IOSU_HAX_READ_FILE = 0xD0
        GET_VERSION_HASH = 0xE0
        PERSIST_ASSEMBLY = 0xE1
        CLEAR_ASSEMBLY = 0xE2

    def __init__(self, read_timeout: int = 1.0):
        self._read_timeout = read_timeout
        self._connection = None  # type: Optional[socket.socket]

    def connect(self, ip_address: str) -> bool:
        if self._connection is not None:
            raise RuntimeError('Client already connected!')
        try:
            connection_socket = socket.create_connection((ip_address, TCPGECKO_TCP_PORT), timeout=1.0)
        except socket.timeout:
            return False
        if connection_socket is None:
            return False
        connection_socket.settimeout(self._read_timeout)
        if connection_socket is None:
            return False
        self._connection = connection_socket
        time.sleep(0.100)
        return True

    def disconnect(self):
        if self._connection is not None:
            self._connection.close()

    def get_server_version_hash(self):
        self._connection.send(self.Commands.GET_VERSION_HASH.to_bytes(1, 'big'))
        try:
            return struct.unpack('I', self._connection.recv(4))
        except socket.timeout:
            return None

    def read_memory_range(self, start_address: int, end_address: int) -> Optional[bytearray]:
        if end_address <= start_address:
            raise RuntimeError('Start Address less than End Address!')
        data_size_bytes = end_address - start_address
        chunk_count = data_size_bytes // TCPGECKO_PACKET_SIZE
        final_chunk_size = data_size_bytes % TCPGECKO_PACKET_SIZE
        to_send = struct.pack(
            '>LL', start_address, end_address
        )
        try:
            sent_bytes = self._connection.send(self.Commands.READ_MEMORY.to_bytes(1, byteorder='big'))
        except (ConnectionResetError, ConnectionRefusedError):
            return None
        if sent_bytes != 1:
            return None
        try:
            sent_bytes = self._connection.send(to_send)
        except (ConnectionResetError, ConnectionRefusedError):
            return None
        if sent_bytes != len(to_send):
            return None
        read_memory_values = bytearray()

        def read_chunk(chunk_length: int):
            try:
                prefix_byte = self._connection.recv(1)
            except socket.timeout:
                return None
            except ConnectionResetError:
                return None
            if prefix_byte == TCPGECKO_BLOCK_ZERO_PREFIX:
                return b'\x00' * chunk_length
            else:
                return self._connection.recv(data_size_bytes)
            return None

        for idx in range(chunk_count + 1):
            packet_size = final_chunk_size if idx == chunk_count else TCPGECKO_PACKET_SIZE
            data = read_chunk(packet_size)
            if data is None:
                return None
            read_memory_values.extend(data)
        
        return read_memory_values
    