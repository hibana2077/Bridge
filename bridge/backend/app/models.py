from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime


class ExchangeEnum(str, Enum):
    """Supported cryptocurrency exchanges"""
    BINANCE = "binance"
    COINBASE = "coinbase"
    BYBIT = "bybit"
    OKEX = "okex"
    KUCOIN = "kucoin"
    BITFINEX = "bitfinex"
    FTX = "ftx"
    HUOBI = "huobi"


class OrderTypeEnum(str, Enum):
    """Supported order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class PositionSideEnum(str, Enum):
    """Position side"""
    LONG = "long"
    SHORT = "short"


class ApiKeyModel(BaseModel):
    """Exchange API key model"""
    exchange: ExchangeEnum
    api_key: str
    api_secret: str


class AlertConfigModel(BaseModel):
    """TradingView alert configuration"""
    name: str = Field(..., description="Configuration name")
    exchange: ExchangeEnum = Field(..., description="Target exchange")
    symbol: str = Field(..., description="Trading pair (e.g., BTC/USDT)")
    order_type: OrderTypeEnum = Field(..., description="Order type")
    position_side: PositionSideEnum = Field(..., description="Position side (long/short)")
    quantity: Optional[float] = Field(None, description="Order quantity (or use percentage)")
    quantity_percentage: Optional[float] = Field(None, description="Order quantity as percentage of available balance")
    price: Optional[float] = Field(None, description="Price for limit orders")
    stop_loss: Optional[float] = Field(None, description="Stop loss price/percentage")
    take_profit: Optional[float] = Field(None, description="Take profit price/percentage")
    description: Optional[str] = Field(None, description="Alert description")


class TradingViewAlertModel(BaseModel):
    """TradingView alert webhook payload"""
    config_name: str = Field(..., description="Name of the configuration to use")
    user_id: str = Field(..., description="User ID")
    price: Optional[float] = Field(None, description="Current price from TradingView")
    volume: Optional[float] = Field(None, description="Current volume from TradingView")
    time: Optional[datetime] = Field(None, description="Alert time")
    exchange: Optional[str] = Field(None, description="Exchange from TradingView")
    symbol: Optional[str] = Field(None, description="Symbol from TradingView")
    message: Optional[str] = Field(None, description="Custom message from TradingView")
    additional_parameters: Optional[Dict[str, Any]] = Field(None, description="Any additional parameters from TradingView")


class OrderResultModel(BaseModel):
    """Result of order execution"""
    success: bool
    order_id: Optional[str] = None
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class UserModel(BaseModel):
    """User model"""
    user_id: str
    username: str
    email: Optional[str] = None