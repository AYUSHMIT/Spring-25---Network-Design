using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Threading;

public class Client
{
    private const int SERVER_PORT = 12345;
    private const int PACKET_SIZE = 1024;
    private static Random random = new Random();

    private static void SendFile(string filePath)
    {
        // Create a UDP socket
        using (var clientSocket = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, ProtocolType.Udp))
        {
            // Read the file data
            byte fileData = File.ReadAllBytes(filePath);

            // Calculate the number of packets
            int numPackets = (int)Math.Ceiling((double)fileData.Length / PACKET_SIZE);

            // Send the number of packets to the server
            clientSocket.SendTo(BitConverter.GetBytes(numPackets), new IPEndPoint(IPAddress.Loopback, SERVER_PORT));

            // Send the file data in packets
            int seqNum = 0;
            for (int i = 0; i < numPackets; i++)
            {
                int offset = i * PACKET_SIZE;
                int packetSize = Math.Min(PACKET_SIZE, fileData.Length - offset);
                byte packetData = new byte[packetSize];
                Array.Copy(fileData, offset, packetData, 0, packetSize);

                // Simulate random delay
                Thread.Sleep(random.Next(0, 500));

                // Calculate checksum
                ushort checksum = CalculateCRC16(packetData);

                // Create packet
                byte packet = CreatePacket(seqNum, checksum, packetData);

                // Send packet
                clientSocket.SendTo(packet, new IPEndPoint(IPAddress.Loopback, SERVER_PORT));

                // Wait for ACK
                byte ackBuffer = new byte;
                clientSocket.Receive(ackBuffer);
                int ackSeqNum = BitConverter.ToInt32(ackBuffer, 0);

                // Check for ACK errors
                if (ackSeqNum!= seqNum)
                {
                    Console.WriteLine($"Error: Incorrect ACK sequence number. Expected {seqNum}, got {ackSeqNum}");
                    // Handle retransmission or other error recovery mechanisms
                }

                seqNum = (seqNum + 1) % 2;
            }

            Console.WriteLine("File sent successfully!");
        }
    }

    private static byte CreatePacket(int seqNum, ushort checksum, byte data)
    {
        byte packet = new byte[4 + 2 + data.Length];
        BitConverter.GetBytes(seqNum).CopyTo(packet, 0);
        BitConverter.GetBytes(checksum).CopyTo(packet, 4);
        data.CopyTo(packet, 6);
        return packet;
    }

    private static ushort CalculateCRC16(byte data)
    {
        ushort crc = 0xFFFF;
        for (int i = 0; i < data.Length; i++)
        {
            crc ^= (ushort)(data[i] << 8);
            for (int j = 0; j < 8; j++)
            {
                if ((crc & 0x8000) > 0)
                {
                    crc = (ushort)((crc << 1) ^ 0x8005);
                }
                else
                {
                    crc <<= 1;
                }
            }
        }
        return crc;
    }

    public static void Main(string args)
    {
        // Example usage
        string filePath = "phase_2.jpg";
        SendFile(filePath);
    }
}