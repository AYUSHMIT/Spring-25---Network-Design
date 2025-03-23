def simulate_loss(probability):
    """
    Simulates packet loss with the given probability.
    """
    return random.random() < probability

def introduce_bit_error(packet, error_probability):
    """
    Introduces a random bit error into the packet with the given probability.
    """
    if random.random() < error_probability:
        index = random.randint(0, len(packet) - 1)
        bit_index = random.randint(0, 7)
        byte_array = bytearray(packet)
        byte_array[index] ^= (1 << bit_index)  # Flip the bit
        return bytes(byte_array)
    return packet

def read_bmp_file(file_path):
    """
    Reads a BMP file and returns its binary content.
    """
    with open(file_path, 'rb') as bmp_file:
        return bmp_file.read()

def write_bmp_file(file_path, data):
    """
    Writes binary data to a BMP file.
    """
    with open(file_path, 'wb') as bmp_file:
        bmp_file.write(data)