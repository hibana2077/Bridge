from fastapi import FastAPI, HTTPException, Depends, Body, Query
from fastapi.middleware.cors import CORSMiddleware
import ccxt
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from .models import (
    TradingViewAlertModel,
    AlertConfigModel,
    ApiKeyModel,
    OrderResultModel,
    ExchangeEnum,
    OrderTypeEnum,
    PositionSideEnum
)

from .database import (
    save_exchange_api_key,
    get_exchange_api_key,
    delete_exchange_api_key,
    save_alert_config,
    get_alert_config,
    get_all_alert_configs,
    delete_alert_config,
    save_alert_history,
    get_alert_history
)

app = FastAPI(title="TradingView Alert Bridge")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, update with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exchange client cache
exchange_clients = {}

def get_exchange_client(user_id: str, exchange_name: str):
    """Get or create exchange client from cache"""
    client_key = f"{user_id}:{exchange_name}"
    
    if client_key in exchange_clients:
        return exchange_clients[client_key]
        
    # Get API credentials
    credentials = get_exchange_api_key(user_id, exchange_name)
    if not credentials or "api_key" not in credentials:
        raise HTTPException(status_code=404, detail=f"API keys not found for exchange {exchange_name}")
    
    try:
        # Create CCXT exchange client
        exchange_class = getattr(ccxt, exchange_name)
        client = exchange_class({
            'apiKey': credentials['api_key'],
            'secret': credentials['api_secret'],
            'enableRateLimit': True,
        })
        
        # Cache client
        exchange_clients[client_key] = client
        return client
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating exchange client: {str(e)}")

@app.get("/")
def read_root():
    return {"status": "ok", "service": "TradingView Alert Bridge"}

# API key management endpoints
@app.post("/api/keys", response_model=dict)
async def add_api_key(api_key: ApiKeyModel):
    """Add or update exchange API keys"""
    try:
        user_id = "default"  # In a real app, get from auth
        result = save_exchange_api_key(
            user_id, 
            api_key.exchange.value, 
            api_key.api_key, 
            api_key.api_secret
        )
        return {"success": result, "message": "API keys saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/keys/{exchange}")
async def get_api_key_status(exchange: str):
    """Check if API keys exist for an exchange"""
    try:
        user_id = "default"  # In a real app, get from auth
        keys = get_exchange_api_key(user_id, exchange)
        return {"has_keys": bool(keys)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/keys/{exchange}")
async def remove_api_key(exchange: str):
    """Delete API keys for an exchange"""
    try:
        user_id = "default"  # In a real app, get from auth
        result = delete_exchange_api_key(user_id, exchange)
        return {"success": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Alert configuration endpoints
@app.post("/api/config", response_model=dict)
async def create_alert_config(config: AlertConfigModel):
    """Create or update an alert configuration"""
    try:
        user_id = "default"  # In a real app, get from auth
        result = save_alert_config(user_id, config.name, config.dict())
        return {"success": result, "message": "Configuration saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config/{config_name}", response_model=AlertConfigModel)
async def get_config(config_name: str):
    """Get a specific alert configuration"""
    try:
        user_id = "default"  # In a real app, get from auth
        config = get_alert_config(user_id, config_name)
        if not config:
            raise HTTPException(status_code=404, detail=f"Configuration {config_name} not found")
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config", response_model=List[AlertConfigModel])
async def list_configs():
    """List all alert configurations"""
    try:
        user_id = "default"  # In a real app, get from auth
        configs = get_all_alert_configs(user_id)
        return configs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/config/{config_name}")
async def remove_config(config_name: str):
    """Delete an alert configuration"""
    try:
        user_id = "default"  # In a real app, get from auth
        result = delete_alert_config(user_id, config_name)
        return {"success": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# TradingView webhook endpoint
@app.post("/webhook/tradingview", response_model=OrderResultModel)
async def process_tradingview_alert(alert: TradingViewAlertModel):
    """Process incoming TradingView alert"""
    try:
        # Get configuration
        config = get_alert_config(alert.user_id, alert.config_name)
        if not config:
            raise HTTPException(status_code=404, detail=f"Configuration '{alert.config_name}' not found")
        
        # Get exchange client
        exchange = get_exchange_client(alert.user_id, config["exchange"])
        
        # Prepare order parameters
        symbol = config["symbol"]
        order_type = config["order_type"]
        side = "buy" if config["position_side"] == "long" else "sell"
        
        params = {}
        
        # Determine quantity
        quantity = None
        if config.get("quantity"):
            quantity = config["quantity"]
        elif config.get("quantity_percentage"):
            # Get balance and calculate quantity
            balance = exchange.fetch_balance()
            base_currency = symbol.split("/")[1]  # For BTC/USDT, get USDT
            
            if base_currency not in balance:
                raise HTTPException(status_code=400, detail=f"No balance found for {base_currency}")
                
            available = float(balance[base_currency]['free'])
            current_price = alert.price if alert.price else float(exchange.fetch_ticker(symbol)['last'])
            
            quantity = (available * config["quantity_percentage"] / 100) / current_price
        
        if not quantity:
            raise HTTPException(status_code=400, detail="Could not determine order quantity")
        
        # Execute order based on type
        order_result = None
        
        if order_type == "market":
            order_result = exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=quantity
            )
        elif order_type == "limit":
            price = alert.price if alert.price else config.get("price")
            if not price:
                raise HTTPException(status_code=400, detail="Price required for limit orders")
                
            order_result = exchange.create_order(
                symbol=symbol,
                type='limit',
                side=side,
                amount=quantity,
                price=price
            )
        elif order_type in ("stop_loss", "take_profit"):
            price = alert.price if alert.price else config.get("price")
            if not price:
                raise HTTPException(status_code=400, detail=f"Price required for {order_type} orders")
                
            # Different exchanges use different parameter names for these orders
            # This is a simplified example
            params["stopPrice"] = price
            
            order_result = exchange.create_order(
                symbol=symbol,
                type='stop',
                side=side,
                amount=quantity,
                price=price,
                params=params
            )
        
        # Save result to history
        result = OrderResultModel(
            success=True,
            order_id=order_result["id"] if order_result and "id" in order_result else None,
            message="Order executed successfully",
            details=order_result,
            timestamp=datetime.now()
        )
        
        # Save to history
        history_data = {
            "config_name": alert.config_name,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": alert.price,
            "timestamp": result.timestamp.isoformat(),
            "success": True,
            "order_id": result.order_id,
            "details": result.details
        }
        save_alert_history(alert.user_id, history_data)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        error_result = OrderResultModel(
            success=False,
            message=f"Error executing order: {str(e)}",
            timestamp=datetime.now()
        )
        
        # Save error to history
        history_data = {
            "config_name": alert.config_name,
            "timestamp": error_result.timestamp.isoformat(),
            "success": False,
            "message": error_result.message,
        }
        save_alert_history(alert.user_id, history_data)
        
        return error_result

# Alert history endpoint
@app.get("/api/history", response_model=List[Dict[str, Any]])
async def get_user_alert_history(limit: int = Query(20, ge=1, le=100)):
    """Get user's alert history"""
    try:
        user_id = "default"  # In a real app, get from auth
        history = get_alert_history(user_id, limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Exchange list endpoint
@app.get("/api/exchanges", response_model=List[str])
async def list_exchanges():
    """List all supported exchanges"""
    return [e.value for e in ExchangeEnum]