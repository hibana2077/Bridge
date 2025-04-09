# TradingView Alert Bridge

A web application that bridges TradingView alerts to cryptocurrency exchanges, allowing automated trading based on TradingView signals.

## Features

- **User-friendly Interface**: Streamlit web application for easy configuration
- **Multiple Exchanges Support**: Connect to popular cryptocurrency exchanges via CCXT
- **Easy Configuration**: Create and manage alert configurations through the UI
- **TradingView Integration**: Receive and process TradingView alert webhooks
- **Order Execution**: Market, limit, stop-loss, and take-profit orders
- **Alert History**: Track all executed alerts and orders
- **Secure Storage**: Encrypted API keys in Redis database

## Project Structure

```
bridge/
  ├── backend/            # FastAPI backend
  │   ├── app/            # Application code
  │   │   ├── main.py     # FastAPI application
  │   │   ├── models.py   # Data models
  │   │   └── database.py # Redis database operations
  │   └── Dockerfile      # Backend Docker image
  ├── frontend/           # Streamlit frontend
  │   ├── app/            # Application code
  │   │   └── main.py     # Streamlit application
  │   └── Dockerfile      # Frontend Docker image
  └── data/               # Persistent data volume
docker-compose.yml        # Docker Compose configuration
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- TradingView account

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/hibana2077/Bridge
   cd Bridge
   ```

2. Configure environment variables:
   ```bash
   # Create a secure password and encryption key
   cp .env.example .env
   # Edit .env with your secure values
   ```

3. Start the application:
   ```bash
   docker-compose up -d
   ```

4. Access the web interface:
   - Frontend UI: http://localhost:8501
   - Backend API: http://localhost:8000

### Using the Application

1. **Add Exchange API Keys**:
   - Go to the "Exchange API Keys" section
   - Select an exchange and enter your API key and secret
   - Save the keys

2. **Create Alert Configurations**:
   - Go to the "Alert Configurations" section
   - Create a new configuration with your trading parameters
   - Save the configuration

3. **Configure TradingView Alert**:
   - In TradingView, create a new alert
   - Set the alert conditions according to your strategy
   - Set the webhook URL to your backend endpoint (e.g., http://your-server:8000/webhook/tradingview)
   - Format the message as JSON:
     ```json
     {
       "config_name": "your_config_name",
       "user_id": "default",
       "price": {{close}},
       "symbol": "{{ticker}}",
       "message": "{{strategy.order.comment}}"
     }
     ```

4. **Monitor Results**:
   - View real-time alert execution in the "Alert History" section
   - Check for any errors or issues

## Security Considerations

- Store API keys with restricted permissions (trading only, no withdrawals)
- Use IP restrictions on your exchange API keys when possible
- For production use, enable authentication for webhooks
- Keep your encryption key secure and don't share it
- Change the default Redis password in the .env file

## Troubleshooting

- **Connection Issues**: Ensure your server can receive webhooks from TradingView
- **Order Execution Errors**: Check the Alert History for detailed error messages
- **API Key Errors**: Verify API key permissions and that they are entered correctly

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Use at your own risk. The authors are not responsible for any financial losses incurred by using this software.

Trading cryptocurrencies involves significant risk and can result in the loss of your invested capital. You should not invest more than you can afford to lose.