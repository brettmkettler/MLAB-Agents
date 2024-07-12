using Newtonsoft.Json;

namespace AshAMQP.TestApp
{
    class Program
    {
        static async Task Main(string[] args)
        {
            var client = new AMQPClient("68.221.122.91", "unityAgent", "mlab120!", useSSL: true);

            client.OnConnected += Client_OnConnected;
            client.OnError += Client_OnError;
            client.OnDisconnect += Client_OnDisconnect;
            client.OnStateChanged += Client_OnStateChanged;

            client.Connect();

            // Give some time for the connection to establish
            await Task.Delay(2000);

            if (client.State == ClientStates.Connected)
            {
                client.Subscribe("unity_assessment_queue", message => Console.WriteLine($"Received from unity_assessment_queue: {message}"));
                client.Subscribe("unity_quality_queue", message => Console.WriteLine($"Received from unity_quality_queue: {message}"));
                client.Subscribe("unity_master_queue", message => Console.WriteLine($"Received from unity_master_queue: {message}"));

                var exampleMessage = new { msg = "Hello, World!" , location = "TestBench" , user = "Ash" };

                client.PublishMessage("unity_assessment_queue", JsonConvert.SerializeObject(exampleMessage));
                client.PublishMessage("unity_quality_queue", JsonConvert.SerializeObject(exampleMessage));
                client.PublishMessage("unity_master_queue", JsonConvert.SerializeObject(exampleMessage));

                Console.WriteLine("Messages sent. Press any key to exit...");
                Console.ReadKey();

                client.Disconnect();
            }
            else
            {
                Console.WriteLine("Could not establish connection to RabbitMQ.");
            }
        }

        private static void Client_OnStateChanged(AMQPClient client, ClientStates oldState, ClientStates newState)
        {
            Console.WriteLine($"State changed from {oldState} to {newState}");
        }

        private static void Client_OnDisconnect(AMQPClient client, string reasonMessage)
        {
            Console.WriteLine($"Disconnected: {reasonMessage}");
        }

        private static void Client_OnError(AMQPClient client, string error)
        {
            Console.WriteLine($"Error: {error}");
        }

        private static void Client_OnConnected(AMQPClient client)
        {
            Console.WriteLine("Connected to RabbitMQ");
        }
    }
}
