using System;
using System.Windows.Forms;
using System.Threading;

namespace RDT_2._2_GUI
{
    public partial class Form1: Form
    {
        public Form1()
        {
            InitializeComponent();
        }

        private void sendButton_Click(object sender, EventArgs e)
        {
            // Use a separate thread for sending to avoid blocking the UI
            Thread sendThread = new Thread(() =>
            {
                Client.SendFile("phase_2.jpg");
            });
            sendThread.Start();
        }

        private void receiveButton_Click(object sender, EventArgs e)
        {
            // Use a separate thread for receiving to avoid blocking the UI
            Thread receiveThread = new Thread(() =>
            {
                Server.ReceiveFile();
            });
            receiveThread.Start();
        }
    }
}