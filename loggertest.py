import kapascan.logger as logger
host = '192.168.254.51'

scpi_socket = logger.SCPISocket(host)
scpi_socket.connect()
scpi_socket.command("HEY")
#scpi_socket.disconnect()

