using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Threading;

public class Server
{
    private const int SERVER_PORT = 12345;
    private const int PACKET_SIZE = 1024;
    private static Random random = new Random();

    private static void ReceiveFile()
    {
        // Create a UDP socket
        using (var serverSocket = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, ProtocolType.Udp))
        {
            // Bind the socket to the specified port
            serverSocket.Bind(new IPEndPoint(IPAddress.Any, SERVER_PORT));

            // Receive the number of packets from the client
            byte numPacketsBuffer = new byte;
            EndPoint clientEndPoint = new IPEndPoint(IPAddress.Any, 0);
            serverSocket.ReceiveFrom(numPacketsBuffer, ref clientEndPoint);
            int numPackets = BitConverter.ToInt32(numPacketsBuffer, 0);

            // Receive the file data in packets
            byte fileData = new byte[numPackets * PACKET_SIZE];
            int expectedSeqNum = 0;
            for (int i = 0; i < numPackets; i++)
            {
                // Receive packet
                byte packetBuffer = new byte[PACKET_SIZE + 6];
                serverSocket.ReceiveFrom(packetBuffer, ref clientEndPoint);

                // Simulate random delay
                Thread.Sleep(random.Next(0, 500));

                // Extract packet data
                int seqNum = BitConverter.ToInt32(packetBuffer, 0);
                ushort checksum = BitConverter.ToUInt16(packetBuffer, 4);
                byte packetData = new byte[packetBuffer.Length - 6];
                Array.Copy(packetBuffer, 6, packetData, 0, packetData.Length);

                // Verify checksum
                ushort calculatedChecksum = CalculateCRC16(packetData);
                if (calculatedChecksum!= checksum)
                {
                    Console.WriteLine("Error: Checksum mismatch");
                    // Handle retransmission or other error recovery mechanisms
                }

                // Check sequence number
                if (seqNum!= expectedSeqNum)
                {
                    Console.WriteLine("Error: Incorrect sequence number");
                    // Handle retransmission or other error recovery mechanisms
                }

                // Copy packet data to file data array
                Array.Copy(packetData, 0, fileData, i * PACKET_SIZE, packetData.Length);

                // Send ACK
                byte ack = BitConverter.GetBytes(expectedSeqNum);
                serverSocket.SendTo(ack, clientEndPoint);

                expectedSeqNum = (expectedSeqNum + 1) % 2;
            }

            // Save the received file data
            File.WriteAllBytes("received_image.jpg", fileData);
            Console.WriteLine("File received successfully!");
        }
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
        ReceiveFile();
    }
}