using System;
using System.Collections.Concurrent;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;
using RabbitMQ.Client.Exceptions;

namespace AshAMQP
{
    public delegate void OnConnectedDelegate(AMQPClient client);
    public delegate void OnErrorDelegate(AMQPClient client, string error);
    public delegate void OnDisconnectDelegate(AMQPClient client, string reasonMessage);
    public delegate void OnStateChangedDelegate(AMQPClient client, ClientStates oldState, ClientStates newState);

    public enum ClientStates
    {
        Disconnected,
        Connecting,
        Connected,
        Disconnecting
    }

    public sealed class AMQPClient
    {
        private IConnection? connection;
        private IModel? channel;

        private readonly string hostname;
        private readonly string username;
        private readonly string password;
        private readonly string virtualHost;
        private readonly bool useSSL;
        private readonly ConnectionFactory factory;

        public event OnConnectedDelegate? OnConnected;
        public event OnErrorDelegate? OnError;
        public event OnDisconnectDelegate? OnDisconnect;
        public event OnStateChangedDelegate? OnStateChanged;

        public ClientStates State
        {
            get => this.state;
            private set
            {
                var oldState = this.state;
                if (oldState != value)
                {
                    this.state = value;
                    this.OnStateChanged?.Invoke(this, oldState, this.state);
                }
            }
        }
        private ClientStates state;

        public AMQPClient(string hostname, string username, string password, bool useSSL = false, string virtualHost = "/")
        {
            this.hostname = hostname;
            this.username = username;
            this.password = password;
            this.virtualHost = virtualHost;
            this.useSSL = useSSL;
            this.factory = new ConnectionFactory
            {
                HostName = this.hostname,
                UserName = this.username,
                Password = this.password,
                VirtualHost = this.virtualHost,
                Port = useSSL ? AmqpTcpEndpoint.UseDefaultPort : 5672, // Use port 5672 for non-SSL connections
            };

            if (this.useSSL)
            {
                this.factory.Ssl = new SslOption
                {
                    Enabled = true,
                    ServerName = this.hostname, // Ensure this matches your server's SSL certificate CN
                    AcceptablePolicyErrors = System.Net.Security.SslPolicyErrors.RemoteCertificateChainErrors | 
                                             System.Net.Security.SslPolicyErrors.RemoteCertificateNameMismatch | 
                                             System.Net.Security.SslPolicyErrors.RemoteCertificateNotAvailable
                };
            }
        }

        public void Connect()
        {
            try
            {
                Console.WriteLine("Attempting to connect to RabbitMQ...");
                this.State = ClientStates.Connecting;
                this.connection = this.factory.CreateConnection();
                this.channel = this.connection.CreateModel();
                this.State = ClientStates.Connected;
                this.OnConnected?.Invoke(this);
                Console.WriteLine("Successfully connected to RabbitMQ.");
            }
            catch (BrokerUnreachableException ex)
            {
                this.OnError?.Invoke(this, ex.Message);
                this.State = ClientStates.Disconnected;
                Console.WriteLine($"BrokerUnreachableException: {ex.Message}");
                if (ex.InnerException != null)
                {
                    Console.WriteLine($"InnerException: {ex.InnerException.Message}");
                }
            }
            catch (Exception ex)
            {
                this.OnError?.Invoke(this, ex.Message);
                this.State = ClientStates.Disconnected;
                Console.WriteLine($"Exception: {ex.Message}");
                if (ex.InnerException != null)
                {
                    Console.WriteLine($"InnerException: {ex.InnerException.Message}");
                }
            }
        }

        public void Disconnect()
        {
            try
            {
                this.State = ClientStates.Disconnecting;
                this.channel?.Close();
                this.connection?.Close();
                this.State = ClientStates.Disconnected;
                this.OnDisconnect?.Invoke(this, "Disconnected gracefully");
                Console.WriteLine("Successfully disconnected from RabbitMQ.");
            }
            catch (Exception ex)
            {
                this.OnError?.Invoke(this, ex.Message);
                Console.WriteLine($"Exception during disconnect: {ex.Message}");
            }
        }

        public void PublishMessage(string queueName, string message)
        {
            var body = Encoding.UTF8.GetBytes(message);
            this.channel?.BasicPublish(exchange: "", routingKey: queueName, basicProperties: null, body: body);
            Console.WriteLine($"Message published to queue {queueName}: {message}");
        }

        public void Subscribe(string queueName, Action<string> onMessageReceived)
        {
            if (this.channel == null)
            {
                throw new InvalidOperationException("Cannot subscribe when channel is not initialized.");
            }

            var consumer = new EventingBasicConsumer(this.channel);
            consumer.Received += (model, ea) =>
            {
                var body = ea.Body.ToArray();
                var message = Encoding.UTF8.GetString(body);
                onMessageReceived(message);
                Console.WriteLine($"Message received from queue {queueName}: {message}");
            };
            this.channel.BasicConsume(queue: queueName, autoAck: true, consumer: consumer);
            Console.WriteLine($"Subscribed to queue {queueName}");
        }
    }
}
