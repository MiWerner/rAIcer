using System;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;

using System.Net.Sockets;
using System.Threading;
using System.Windows.Threading;
using System.ComponentModel;
using System.IO;

using System.Linq;

namespace IBallClient
{
    /// <summary>
    /// Interaktionslogik fuer MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        const int LOG_DELAY = 50;

        // Gibt an ob mit dem Server verbunden oder nicht
        bool _isConnected = false;

        // Gibt an ob die Spieldaten geloged werden sollen
        bool _isLogging = false;

        string _logFileName;

        Thread _threadConnection = null;

        // Variablen die die entsprechende
        byte _setForceUp = 0;
        byte _setForceDown = 0;
        byte _setForceLeft = 0;
        byte _setForceRight = 0;

        // Empfangsdaten
        const int IMG_WIDTH = 512;
        const int IMG_HEIGHT = 288;
        const int IMG_SIZE = IMG_WIDTH * IMG_HEIGHT * 3;
        const int DATA_SIZE = IMG_SIZE + 6;
        int _stride;

        byte[] _arrayImage = new byte[IMG_SIZE];

        // Spieler eigenschaften
        byte[] _arrayData = new byte[6];
        int _id = -999;

        public MainWindow()
        {
            InitializeComponent();
            imageScreenShot.RenderTransformOrigin = new Point(0.5, 0.5);
            ScaleTransform flipUD = new ScaleTransform();
            flipUD.ScaleY = -1;
            imageScreenShot.RenderTransform = flipUD;

            _stride = ((PixelFormats.Rgb24.BitsPerPixel + 7) / 8) * IMG_WIDTH;

        }

        private void Window_Closing(object sender, CancelEventArgs e)
        {
            if (_isConnected)
            {
                _isConnected = false;
                buttonConnect.Content = "Verbinden";

                Thread.Sleep(1000);
                if (_threadConnection.IsAlive)
                    _threadConnection.Abort();

                _threadConnection = null;
            }
        }

        private void Window_KeyDown(object sender, KeyEventArgs e)
        {
            if(Keyboard.IsKeyDown(Key.Up)) 
            {
                _setForceUp = 1;
            }
            if (Keyboard.IsKeyDown(Key.Down))
            {
                _setForceDown = 1;
            }
            if (Keyboard.IsKeyDown(Key.Left))
            {
                _setForceLeft = 1;
            }
            if (Keyboard.IsKeyDown(Key.Right))
            {
                _setForceRight = 1;
            }

            labelUp.Content = Convert.ToString(_setForceUp);
            labelDown.Content = Convert.ToString(_setForceDown);
            labelLeft.Content = Convert.ToString(_setForceLeft);
            labelRight.Content = Convert.ToString(_setForceRight);
        }

        private void Window_KeyUp(object sender, KeyEventArgs e)
        {
            if (Keyboard.IsKeyUp(Key.Up))
            {
                _setForceUp = 0;

            }
            if (Keyboard.IsKeyUp(Key.Down))
            {
                _setForceDown = 0;
            }
            if (Keyboard.IsKeyUp(Key.Left))
            {
                _setForceLeft = 0;
            }
            if (Keyboard.IsKeyUp(Key.Right))
            {
                _setForceRight = 0;
            }

            labelUp.Content = Convert.ToString(_setForceUp);
            labelDown.Content = Convert.ToString(_setForceDown);
            labelLeft.Content = Convert.ToString(_setForceLeft);
            labelRight.Content = Convert.ToString(_setForceRight);
        }


        private void NewDataRecieved(byte[] inData)
        {
            // daten Kopieren und Aufteilen
            lock (_arrayData)
            {
                Array.Copy(inData, 0, _arrayData, 0, 6);
                
            }
            lock (_arrayImage)
            {
                Array.Copy(inData, 6, _arrayImage, 0, IMG_SIZE);

            }

            // mach irgendwas mit den daten, wie zB Anzeigen und ausgeben
            lock (_arrayImage)
            {
                imageScreenShot.Source = BitmapSource.Create(IMG_WIDTH, IMG_HEIGHT, 96d, 96d, PixelFormats.Rgb24, null, _arrayImage, _stride);
            }

            // Hier koennen die Daten verarbeitet werden
            lock (_arrayData)
            {
                if (_id == -999)
                    _id = Convert.ToInt16(_arrayData[0]);

                labelID.Content = Convert.ToInt16(_arrayData[0]).ToString();
                labelStatus.Content = Convert.ToInt16(_arrayData[1]).ToString();
                labelCLap.Content = Convert.ToInt16(_arrayData[2]).ToString();
                labelNumLap.Content = Convert.ToInt16(_arrayData[3]).ToString();
                labelDmg.Content = Convert.ToInt16(_arrayData[4]).ToString();
                labelRank.Content = Convert.ToInt16(_arrayData[5]).ToString();
            }
            
            
        }

		// Daten Empfang und Senden Thread
        private void runThread()
        {
            
            TcpClient clientSocket = null; 

            try
            {
                var port = 5007;
                string ip = "localhost";
                Application.Current.Dispatcher.BeginInvoke(
                    DispatcherPriority.Background, new Action(() => {
                        port = Convert.ToInt32(textPort.Text);
                        ip = textIP.Text;
                    })
                );
                              

			    // Verbindung herstellen
                clientSocket = new TcpClient(ip, port);
                _isConnected = true;

                Application.Current.Dispatcher.BeginInvoke(
                    DispatcherPriority.Background, new Action(() => {
                        buttonConnect.Content = "Trennen";
                        buttonConnectLog.Content = "Trennen";

                    })
                );
                


            }
            catch (Exception ex)
            {
                
                Console.WriteLine("Unable to connect, because of " + ex);
                _isLogging = false;
            }
            

            byte[] sendBytes = new byte[5];
            
            byte[] bytesFrom = new byte[DATA_SIZE];

            int delayCnt = 0;
            bool writeIn = false;
            bool writeOut = false;
			// Datenschleife
            while (_isConnected)
            {
                Thread.Sleep(15);
                try
                {
                    NetworkStream networkStream = clientSocket.GetStream();

                    // Wenn Daten da sind, empfangen und weiterverarbeiten
                    if (networkStream.DataAvailable)
                    {

                        lock (bytesFrom)
                        {
                            networkStream.Read(bytesFrom, 0, DATA_SIZE);

                            // Schreibe Empfangsdaten in File
                            if (_isLogging && writeIn)
                            {
                                writeIn = false;
                                using (var stream = new StreamWriter(_logFileName, true))
                                {
                                    int[] numbers = Array.ConvertAll(bytesFrom, c => (int)c);
                                    stream.WriteLine(string.Join(" ", numbers));
                                }
                            }
                        }
                        // neue daten sind da
                        Application.Current.Dispatcher.BeginInvoke( DispatcherPriority.Background, new Action(() =>
                        {
                            lock (bytesFrom)
                            {
                                NewDataRecieved(bytesFrom);
                            }
                        }));

                       
                    }

                    // Bewegungsdaten senden
                    sendBytes[0] = Convert.ToByte((Int16)_id);
                    sendBytes[1] = Convert.ToByte(_setForceUp);
                    sendBytes[2] = Convert.ToByte(_setForceDown);
                    sendBytes[3] = Convert.ToByte(_setForceLeft);
                    sendBytes[4] = Convert.ToByte(_setForceRight);

                    networkStream.Write(sendBytes, 0, 5);
                    networkStream.Flush();

                    // schreibe Bewegungsdaten in File
                    if(_isLogging && writeOut)
                    {
                        writeOut = false;
                        using (var stream = new StreamWriter(_logFileName, true))
                        {

                            int[] numbers = Array.ConvertAll(sendBytes, c => (int)c);

                            stream.WriteLine(string.Join(" ", numbers));
                        }

                        
                    }

                    if(_isLogging)
                    {
                        delayCnt++;
                        if(delayCnt >= LOG_DELAY)
                        {
                            delayCnt = 0;
                            writeOut = true;
                            writeIn = true;
                        }
                    }
                        


                }
                catch (Exception ex)
                {
                    Console.WriteLine("Fehler");
                    //Application.Current.Dispatcher.BeginInvoke(
                    //DispatcherPriority.Background, new Action(() =>
                    //{
                    //    textConsole.Text = "Verbindung nicht moeglich, da " + ex + "\n";
                    //})
                    //);
                }
            }
        }

        // Der Verbinden-Button wird geklickt
        private void buttonConnect_Click(object sender, RoutedEventArgs e)
        {
            if (_isConnected)
            {
                _isConnected = false;
                _isLogging = false;
                buttonConnect.Content = "Verbinden";

                textIP.IsEnabled = true;
                textPort.IsEnabled = true;

                Thread.Sleep(1000);
                if (_threadConnection.IsAlive)
                    _threadConnection.Abort();

                _threadConnection = null;
            }
            else
            {
                _threadConnection = new Thread(runThread);
                _threadConnection.Start();
                textIP.IsEnabled = false;
                textPort.IsEnabled = false;
                _isLogging = false;

            }

        }

        // Der Verbinden-Button mit Logger Funktion wird geklickt
        private void buttonConnectLog_Click(object sender, RoutedEventArgs e)
        {
            if (_isConnected)
            {
                _isConnected = false;
                _isLogging = false;
                buttonConnect.Content = "Verbinden";
                buttonConnectLog.Content = "Verbinden";

                textIP.IsEnabled = true;
                textPort.IsEnabled = true;

                Thread.Sleep(1000);
                if (_threadConnection.IsAlive)
                    _threadConnection.Abort();

                _threadConnection = null;
            }
            else
            {

                // aktualisiert den Logfilenamen
                Microsoft.Win32.SaveFileDialog dlg = new Microsoft.Win32.SaveFileDialog();
                dlg.FileName = "";
                dlg.DefaultExt = ".log";
                dlg.Filter = "Log File (.log)|*.log";
                Nullable<bool> result = dlg.ShowDialog();

                if (result == false)
                    return;

                    // Save document
               _logFileName = dlg.FileName;

                _isLogging = true;
                _threadConnection = new Thread(runThread);
                _threadConnection.Start();
                textIP.IsEnabled = false;
                textPort.IsEnabled = false;
            }
        }

    }
}
