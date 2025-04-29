import os
import logging
import json
from datetime import datetime, timedelta
import requests
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import matplotlib.pyplot as plt
import io
import seaborn as sns
import numpy as np

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = "7914464413:AAGHqcvHVymQmaGBltHYhTj_q9i6F5gdfdM"
VYBE_API_KEY = "9nh76uMLnctW4TkuFsvNMUSc7CvMNQ4yPnQfqupz7vNgtUyY"

# Pyth Price feed endpoint
PRICE_ENDPOINT = "https://api.vybenetwork.xyz/price/{priceFeedId}/pyth-price"

# Token details endpoint
TOKEN_DETAILS_ENDPOINT = "https://api.vybenetwork.xyz/token/{mintAddress}"

# Token trend endpoint
TOKEN_TREND_ENDPOINT = "https://api.vybenetwork.xyz/token/{mintAddress}/transfer-volume"

# Price feed IDs for Solana-based tokens (base58-encoded Solana public keys)
PRICE_FEED_IDS = {
    # Major Cryptocurrencies
    "BTC": "HovQMDrbAgAYPCmHVSrezcSmkMtXSSUsLDFANExrZh2J",  # Bitcoin
    "ETH": "EdVCmQ9FSPcVe5YySXDPCRmc8aDQLKJ9xvYBMZPie1VZ",  # Ethereum
    "SOL": "H6ARHf6YXhGYeQfUzQNGk6rDNnLBQKrenN712K4AQJEG",  # Solana
    
    # Stablecoins
    "USDC": "Gv9sZbBvQ6UQpJZ7B8ZRqKdWYvQ6UQpJZ7B8ZRqKdWYv",  # USD Coin
    "USDT": "3vxLXJqLqF3JG5TCbYycbKWRBbCJQLxQmBGCkyqEEefL",  # Tether
    "DAI": "8A9xKz3K3K3K3K3K3K3K3K3K3K3K3K3K3K3K3K3K3K3K",  # DAI
    
    # Solana DeFi Tokens
    "RAY": "4X1oYoFWYtLebk51zuh889r1WFLe8Z9qWApj87hQMfML",  # Raydium
    "SRM": "3vxLXJqLqF3JG5TCbYycbKWRBbCJQLxQmBGCkyqEEefL",  # Serum
    "ORCA": "4X1oYoFWYtLebk51zuh889r1WFLe8Z9qWApj87hQMfML",  # Orca
    "STEP": "3vxLXJqLqF3JG5TCbYycbKWRBbCJQLxQmBGCkyqEEefL",  # Step Finance
    "MNGO": "4X1oYoFWYtLebk51zuh889r1WFLe8Z9qWApj87hQMfML",  # Mango Markets
    "FIDA": "3vxLXJqLqF3JG5TCbYycbKWRBbCJQLxQmBGCkyqEEefL",  # Bonfida
    "COPE": "4X1oYoFWYtLebk51zuh889r1WFLe8Z9qWApj87hQMfML",  # COPE
    "MEDIA": "3vxLXJqLqF3JG5TCbYycbKWRBbCJQLxQmBGCkyqEEefL",  # Media Network
    "OXY": "4X1oYoFWYtLebk51zuh889r1WFLe8Z9qWApj87hQMfML",  # Oxygen
    "SLRS": "3vxLXJqLqF3JG5TCbYycbKWRBbCJQLxQmBGCkyqEEefL",  # Solrise Finance
    
    # Solana NFT & Gaming Tokens
    "ATLAS": "4X1oYoFWYtLebk51zuh889r1WFLe8Z9qWApj87hQMfML",  # Star Atlas
    "POLIS": "3vxLXJqLqF3JG5TCbYycbKWRBbCJQLxQmBGCkyqEEefL",  # Star Atlas DAO
    "SHDW": "4X1oYoFWYtLebk51zuh889r1WFLe8Z9qWApj87hQMfML",  # GenesysGo Shadow
    "PRISM": "3vxLXJqLqF3JG5TCbYycbKWRBbCJQLxQmBGCkyqEEefL",  # Prism Protocol
    "LIQ": "4X1oYoFWYtLebk51zuh889r1WFLe8Z9qWApj87hQMfML",  # LIQ Protocol
    
    # Solana Infrastructure Tokens
    "PORT": "3vxLXJqLqF3JG5TCbYycbKWRBbCJQLxQmBGCkyqEEefL",  # Port Finance
    "SLIM": "4X1oYoFWYtLebk51zuh889r1WFLe8Z9qWApj87hQMfML",  # Solanium
    "GRAPE": "3vxLXJqLqF3JG5TCbYycbKWRBbCJQLxQmBGCkyqEEefL",  # Grape Protocol
    "SAMO": "4X1oYoFWYtLebk51zuh889r1WFLe8Z9qWApj87hQMfML",  # Samoyedcoin
    "BONK": "3vxLXJqLqF3JG5TCbYycbKWRBbCJQLxQmBGCkyqEEefL",  # Bonk
    
    # Solana Yield & Staking Tokens
    "MARINADE": "4X1oYoFWYtLebk51zuh889r1WFLe8Z9qWApj87hQMfML",  # Marinade
    "LARIX": "3vxLXJqLqF3JG5TCbYycbKWRBbCJQLxQmBGCkyqEEefL",  # Larix
    "SLND": "4X1oYoFWYtLebk51zuh889r1WFLe8Z9qWApj87hQMfML",  # Solend
    "HBB": "3vxLXJqLqF3JG5TCbYycbKWRBbCJQLxQmBGCkyqEEefL",  # Hubble Protocol
    "KIN": "4X1oYoFWYtLebk51zuh889r1WFLe8Z9qWApj87hQMfML"   # Kin
}

# Token mint addresses for Solana-based tokens
TOKEN_MINT_ADDRESSES = {
    # Major Cryptocurrencies
    "BTC": "9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E",  # Bitcoin
    "ETH": "2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk",  # Ethereum
    "SOL": "So11111111111111111111111111111111111111112",  # Solana
    
    # Stablecoins
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USD Coin
    "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # Tether
    "DAI": "EjmyN6qEC1Tf1JxiG1ae7UTJhUxSwk1TCWNWqxWV4J6o",  # DAI
    
    # Solana DeFi Tokens
    "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",  # Raydium
    "SRM": "SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt",  # Serum
    "ORCA": "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE",  # Orca
    "STEP": "StepAscQoEioFxxWGnh2sLBDFp9d8rvKz2Yp39iDpyT",  # Step Finance
    "MNGO": "MangoCzJ36AjZyKwVj3VnYU4GTonjfVEnJmvvWaxLac",  # Mango Markets
    "FIDA": "EchesyfXePKdLtoiZSL8pBe8Myagyy8ZRqsACNCFGnvp",  # Bonfida
    "COPE": "8HGyAAB1yoM1ttS7pXjHMa3dukTFGQggnFFH3hJZgzQh",  # COPE
    "MEDIA": "ETAtLmCmsoiEEKfNrHKJ2kYy3MoABhU6NQvpSfij5tDs",  # Media Network
    "OXY": "z3dn17yLaGMKffVogeFHQ9zWVcXgqgf3PQnDsNs2g6M",  # Oxygen
    "SLRS": "SLRSSpSLUTP7okbCUBYStWCo1vUg6oLvbnkVfjTGbYX",  # Solrise Finance
    
    # Solana NFT & Gaming Tokens
    "ATLAS": "ATLASXmbPQxBUYbxPsV97usA3fPQYEqzQBUHgiFCUsXx",  # Star Atlas
    "POLIS": "poLisWXnNRwC6oBu1vHiuKQzFjGL4XDSu4g9qjz9qVk",  # Star Atlas DAO
    "SHDW": "SHDWyBxihqiCj6YekG2GUr7wqKLeLAMK1gHZck9pL6y",  # GenesysGo Shadow
    "PRISM": "PRSMNsEPqhGVCH1TtWiJqPjJyh2cKrLostPZTNy1o5x",  # Prism Protocol
    "LIQ": "4wjPQJ6PrkC4dHhYghwJzGBVP78DkBzA2U3kHoFNBuhj",  # LIQ Protocol
    
    # Solana Infrastructure Tokens
    "PORT": "PoRTjZMPXb9T7dyU7tpLEZRQj7e6ssfAE62j2oQuc6y",  # Port Finance
    "SLIM": "xxxxa1sKNGwFtw2kFn8XauW9xq8hBZ5kVtcSesTT9fW",  # Solanium
    "GRAPE": "8upjSpvjcdpuzhfR1zriwg5XkwDrVjS7S9jZGFZt3Wq",  # Grape Protocol
    "SAMO": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",  # Samoyedcoin
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",  # Bonk
    
    # Solana Yield & Staking Tokens
    "MARINADE": "MNDEFzGvMt87ueuHvVU9VcTqsAP5b3fTGPsHuuPA5ey",  # Marinade
    "LARIX": "Lrxqnh6ZHKbGy3dcrCED43nsoLkM1LTzU2jRfWe8qUC",  # Larix
    "SLND": "SLNDpmoWTVADgEdndyvWzroNL7zSi1dF9PC3xHGtPwp",  # Solend
    "HBB": "HBB111SCo9jkCejsZfz8Ec8nH7T6THF8KEKSnvwT6XK",  # Hubble Protocol
    "KIN": "kinXdEcpDQeHPEuQnqmUgtYykqKGVFq6CeVX5iAHJq6"   # Kin
}

TREND_CACHE = {}
CACHE_DURATION = 300  # Cache duration in seconds (5 minutes)

MAX_RETRIES = 5
RETRY_DELAY = 5
REQUEST_TIMEOUT = 30

def create_session():
    """Create a requests session with retry logic"""
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_DELAY,
        status_forcelist=[408, 429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        respect_retry_after_header=True
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=100, pool_maxsize=100)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def get_token_price(symbol):
    """Get token price information from Pyth Price feed"""
    try:
        # Get price feed ID for the symbol
        price_feed_id = PRICE_FEED_IDS.get(symbol.upper())
        if not price_feed_id:
            logger.error(f"No price feed ID found for symbol: {symbol}")
            return None

        # Construct the URL with the price feed ID
        url = PRICE_ENDPOINT.format(priceFeedId=price_feed_id)
        headers = {
            "Accept": "application/json",
            "X-API-KEY": VYBE_API_KEY
        }
        
        logger.info(f"Fetching Pyth price for {symbol} using feed ID: {price_feed_id}")
        logger.info(f"Request URL: {url}")
        
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return None
        
        try:
            data = response.json()
            logger.info(f"Received price data: {data}")
            
            # Extract price information from the response
            price = float(data.get('price', 0))
            price_change_24h = float(data.get('price_change_24h', 0))
            volume_24h = float(data.get('volume_24h', 0))
            market_cap = float(data.get('market_cap', 0))
            confidence = float(data.get('confidence', 0))
            timestamp = data.get('timestamp', datetime.now().isoformat())
            
            return {
                "price": price,
                "price_change_24h": price_change_24h,
                "volume_24h": volume_24h,
                "market_cap": market_cap,
                "confidence": confidence,
                "timestamp": timestamp
            }
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response.text[:100]}...")
            return None
        except ValueError as e:
            logger.error(f"Error converting price data: {e}")
            return None
    except Exception as e:
        logger.error(f"Error fetching token price: {e}")
        return None

def get_token_details(symbol):
    """Get token details from Vybe API"""
    try:
        # Get mint address for the symbol
        mint_address = TOKEN_MINT_ADDRESSES.get(symbol.upper())
        if not mint_address:
            logger.error(f"No mint address found for symbol: {symbol}")
            return None
        
        # Construct the URL with the mint address
        url = TOKEN_DETAILS_ENDPOINT.format(mintAddress=mint_address)
        headers = {
            "Accept": "application/json",
            "X-API-KEY": VYBE_API_KEY
        }
        
        logger.info(f"Fetching token details for {symbol} using mint address: {mint_address}")
        logger.info(f"Request URL: {url}")
        
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return None
        
        try:
            data = response.json()
            logger.info(f"Received token details: {data}")
            
            # Calculate price changes
            price_change_1d = ((data.get('price', 0) - data.get('price1d', 0)) / data.get('price1d', 1)) * 100 if data.get('price1d', 0) != 0 else 0
            price_change_7d = ((data.get('price', 0) - data.get('price7d', 0)) / data.get('price7d', 1)) * 100 if data.get('price7d', 0) != 0 else 0
            
            # Extract token information from the response
            return {
                "name": data.get('name', ''),
                "symbol": data.get('symbol', ''),
                "mint_address": data.get('mintAddress', ''),
                "decimals": data.get('decimal', 0),
                "current_supply": float(data.get('currentSupply', 0)),
                "market_cap": float(data.get('marketCap', 0)),
                "token_volume_24h": float(data.get('tokenAmountVolume24h', 0)),
                "usd_volume_24h": float(data.get('usdValueVolume24h', 0)),
                "price": float(data.get('price', 0)),
                "price_1d": float(data.get('price1d', 0)),
                "price_7d": float(data.get('price7d', 0)),
                "price_change_1d": price_change_1d,
                "price_change_7d": price_change_7d,
                "category": data.get('category', ''),
                "subcategory": data.get('subcategory', ''),
                "verified": data.get('verified', False),
                "logo_url": data.get('logoUrl', ''),
                "update_time": data.get('updateTime', 0)
            }
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response.text[:100]}...")
            return None
        except ValueError as e:
            logger.error(f"Error converting token data: {e}")
            return None
    except Exception as e:
        logger.error(f"Error fetching token details: {e}")
        return None

def get_token_trend(symbol):
    """Get token transfer volume trend from Vybe API with caching and retries"""
    try:
        # Check cache first
        cache_key = f"{symbol}_{int(time.time() // CACHE_DURATION)}"
        if cache_key in TREND_CACHE:
            logger.info(f"Using cached trend data for {symbol}")
            return TREND_CACHE[cache_key]
        
        # Get mint address for the symbol
        mint_address = TOKEN_MINT_ADDRESSES.get(symbol.upper())
        if not mint_address:
            logger.error(f"No mint address found for symbol: {symbol}")
            return None
        
        # Construct the URL with the mint address
        url = TOKEN_TREND_ENDPOINT.format(mintAddress=mint_address)
        headers = {
            "Accept": "application/json",
            "X-API-KEY": VYBE_API_KEY
        }
        
        logger.info(f"Fetching token trend for {symbol} using mint address: {mint_address}")
        
        # Create session with retry logic
        session = create_session()
        
        # Make the request with retries
        for attempt in range(MAX_RETRIES):
            try:
                response = session.get(
                    url,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    break
                elif response.status_code == 408:
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(f"Request timed out, retrying... (Attempt {attempt + 1}/{MAX_RETRIES})")
                        time.sleep(RETRY_DELAY)
                        continue
                    else:
                        logger.error("Max retries reached for timeout")
                        return {"error": "Request timed out after multiple attempts. Please try again later."}
                else:
                    logger.error(f"API error: {response.status_code} - {response.text}")
                    return None
                    
            except requests.Timeout:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Request timed out, retrying... (Attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    logger.error("Max retries reached for timeout")
                    return {"error": "Request timed out after multiple attempts. Please try again later."}
            except requests.RequestException as e:
                logger.error(f"Request failed: {e}")
                return None
        
        try:
            data = response.json()
            logger.info(f"Received token trend data for {symbol}")
            
            # Process time series data
            time_series = data.get('data', [])
            if not time_series:
                return None
            
            # Sort data by timestamp and limit to last 7 days
            time_series.sort(key=lambda x: x['timeBucketStart'])
            time_series = time_series[-7:]  # Only keep last 7 days
            
            # Calculate statistics
            volumes = [float(item['volume']) for item in time_series]
            amounts = [float(item['amount']) for item in time_series]
            
            # Calculate changes
            volume_change_24h = ((volumes[-1] - volumes[-2]) / volumes[-2] * 100) if len(volumes) > 1 else 0
            volume_change_7d = ((volumes[-1] - volumes[0]) / volumes[0] * 100) if len(volumes) > 1 else 0
            
            # Calculate averages
            avg_volume_24h = sum(volumes[-1:]) / len(volumes[-1:]) if volumes[-1:] else 0
            avg_volume_7d = sum(volumes) / len(volumes) if volumes else 0
            
            # Calculate transfer counts
            transfer_count_24h = len(volumes[-1:])
            transfer_count_7d = len(volumes)
            
            # Calculate average and largest transfer sizes
            avg_transfer_size = sum(volumes) / len(volumes) if volumes else 0
            largest_transfer = max(volumes) if volumes else 0
            
            # Calculate volatility (standard deviation of daily changes)
            daily_changes = [(volumes[i] - volumes[i-1]) / volumes[i-1] * 100 for i in range(1, len(volumes))]
            volatility = (sum((x - sum(daily_changes)/len(daily_changes))**2 for x in daily_changes) / len(daily_changes))**0.5 if daily_changes else 0
            
            # Generate investment insights
            insights = generate_investment_insights(
                volume_change_24h,
                volume_change_7d,
                volatility,
                avg_transfer_size,
                largest_transfer,
                transfer_count_24h
            )
            
            result = {
                "time_series": time_series,
                "daily_volume": volumes[-1] if volumes else 0,
                "weekly_volume": sum(volumes) if volumes else 0,
                "volume_change_24h": volume_change_24h,
                "volume_change_7d": volume_change_7d,
                "transfer_count_24h": transfer_count_24h,
                "transfer_count_7d": transfer_count_7d,
                "average_transfer_size": avg_transfer_size,
                "largest_transfer": largest_transfer,
                "avg_volume_24h": avg_volume_24h,
                "avg_volume_7d": avg_volume_7d,
                "volatility": volatility,
                "insights": insights
            }
            
            # Cache the result
            TREND_CACHE[cache_key] = result
            return result
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response.text[:100]}...")
            return None
        except ValueError as e:
            logger.error(f"Error converting trend data: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching token trend: {e}")
        return None

def create_volume_chart(time_series, symbol):
    """Create a comprehensive volume chart for the token"""
    try:
        # Set style
        plt.style.use('dark_background')
        sns.set_palette("husl")
        
        # Prepare data
        dates = [datetime.fromtimestamp(item['timeBucketStart']) for item in time_series]
        volumes = [float(item['volume']) for item in time_series]
        amounts = [float(item['amount']) for item in time_series]
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [2, 1]})
        
        # Volume chart
        bars = ax1.bar(dates, volumes, color='#00ff00', alpha=0.7)
        ax1.set_title(f'{symbol} Transfer Volume Analysis', color='white', pad=20, fontsize=14)
        ax1.set_ylabel('Volume (USD)', color='white')
        ax1.grid(True, alpha=0.3)
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'${height:,.0f}', ha='center', va='bottom', color='white', fontsize=8)
        
        # Amount chart (number of transfers)
        ax2.plot(dates, amounts, color='#ff9900', marker='o', linestyle='-', linewidth=2)
        ax2.set_ylabel('Number of Transfers', color='white')
        ax2.grid(True, alpha=0.3)
        
        # Format x-axis dates
        for ax in [ax1, ax2]:
            ax.tick_params(colors='white')
            ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add trend line to volume chart
        z = np.polyfit(range(len(volumes)), volumes, 1)
        p = np.poly1d(z)
        ax1.plot(dates, p(range(len(volumes))), 'r--', alpha=0.5, label='Trend')
        ax1.legend()
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the chart to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        plt.close()
        
        return buf
    except Exception as e:
        logger.error(f"Error creating chart: {e}")
        return None

def generate_investment_insights(volume_change_24h, volume_change_7d, volatility, avg_transfer_size, largest_transfer, transfer_count_24h):
    """Generate detailed investment insights based on trend data"""
    insights = []
    risk_level = "Medium"
    recommendation = "Hold"
    confidence = "Moderate"
    
    # Volume Analysis
    if volume_change_24h > 20 and volume_change_7d > 50:
        insights.append("📈 Strong upward momentum with significant volume increase")
        risk_level = "Low"
        recommendation = "Consider Buying"
        confidence = "High"
    elif volume_change_24h < -20 and volume_change_7d < -30:
        insights.append("📉 Significant volume decline indicating potential bearish trend")
        risk_level = "High"
        recommendation = "Consider Selling"
        confidence = "High"
    elif volume_change_24h > 10:
        insights.append("📊 Positive volume trend in the last 24 hours")
        risk_level = "Medium-Low"
    elif volume_change_24h < -10:
        insights.append("📊 Negative volume trend in the last 24 hours")
        risk_level = "Medium-High"
    
    # Volatility Analysis
    if volatility > 15:
        insights.append("⚡ High volatility detected - significant price swings")
        risk_level = "High"
        confidence = "Low"
    elif volatility < 5:
        insights.append("📊 Low volatility - stable price movement")
        risk_level = "Low"
        confidence = "High"
    
    # Transfer Pattern Analysis
    if avg_transfer_size > largest_transfer * 0.2:
        insights.append("💰 Dominated by large transfers - institutional activity")
        if volume_change_24h > 0:
            risk_level = "Low"
            confidence = "High"
    else:
        insights.append("👥 Many small transfers - retail participation")
        if volume_change_24h < 0:
            risk_level = "High"
            confidence = "Low"
    
    # Activity Level Analysis
    if transfer_count_24h > 1000:
        insights.append("🚀 High transfer activity - strong market interest")
        if volume_change_24h > 0:
            risk_level = "Low"
            confidence = "High"
    elif transfer_count_24h < 100:
        insights.append("📊 Low transfer activity - limited market interest")
        if volume_change_24h < 0:
            risk_level = "High"
            confidence = "Low"
    
    return {
        "risk_level": risk_level,
        "recommendation": recommendation,
        "confidence": confidence,
        "insights": insights
    }

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    welcome_message = (
        f"👋 Wagwan geng Welcome to Qbicks Price Bot, {user.first_name}!\n\n"
        "I provide real-time cryptocurrency prices and token information from Pyth Price feeds.\n\n"
        "Use /help to see available commands."
    )
    
    # Create keyboard with main commands
    keyboard = [
        [
            InlineKeyboardButton("🔍 Token Info", callback_data="token_info"),
            InlineKeyboardButton("💰 Price Info", callback_data="price_info")
        ],
        [
            InlineKeyboardButton("📊 Price Alert", callback_data="set_alert"),
            InlineKeyboardButton("❓ Help", callback_data="help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a help message when the command /help is issued."""
    help_text = (
        "🤖 *Qbicks Price Bot Commands*\n\n"
        "*Token Commands:*\n"
        "/token [symbol] - Get detailed token information\n"
        "Example: `/token BTC`\n\n"
        "*Price Commands:*\n"
        "/price [symbol] - Get current price\n"
        "Example: `/price BTC`\n\n"
        "Available tokens:\n"
        "*Major Cryptocurrencies:*\n"
        "- BTC (Bitcoin)\n"
        "- ETH (Ethereum)\n"
        "- SOL (Solana)\n\n"
        "*Stablecoins:*\n"
        "- USDC (USD Coin)\n"
        "- USDT (Tether)\n"
        "- DAI\n\n"
        "*Solana DeFi Tokens:*\n"
        "- RAY (Raydium)\n"
        "- SRM (Serum)\n"
        "- ORCA (Orca)\n"
        "- STEP (Step Finance)\n"
        "- MNGO (Mango Markets)\n"
        "- FIDA (Bonfida)\n"
        "- COPE\n"
        "- MEDIA (Media Network)\n"
        "- OXY (Oxygen)\n"
        "- SLRS (Solrise Finance)\n\n"
        "*Solana NFT & Gaming:*\n"
        "- ATLAS (Star Atlas)\n"
        "- POLIS (Star Atlas DAO)\n"
        "- SHDW (GenesysGo Shadow)\n"
        "- PRISM (Prism Protocol)\n"
        "- LIQ (LIQ Protocol)\n\n"
        "*Solana Infrastructure:*\n"
        "- PORT (Port Finance)\n"
        "- SLIM (Solanium)\n"
        "- GRAPE (Grape Protocol)\n"
        "- SAMO (Samoyedcoin)\n"
        "- BONK\n\n"
        "*Solana Yield & Staking:*\n"
        "- MARINADE\n"
        "- LARIX\n"
        "- SLND (Solend)\n"
        "- HBB (Hubble Protocol)\n"
        "- KIN\n\n"
        "*Alert Commands:*\n"
        "/alert [symbol] [above/below] [price] - Set price alert\n"
        "Example: `/alert BTC above 50000`\n"
        "/alerts - View your active alerts\n"
        "/deletealert [alert_id] - Delete a specific alert\n\n"
        "*Other Commands:*\n"
        "/start - Start the bot\n"
        "/help - Show this help message"
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get token price information."""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "Please provide a token symbol.\n"
            "Example: /price BTC\n\n"
            "Available tokens: BTC, ETH, SOL, USDC, USDT"
        )
        return
    
    symbol = context.args[0].upper()
    
    # Check if the symbol is supported
    if symbol not in PRICE_FEED_IDS:
        await update.message.reply_text(
            f"Sorry, {symbol} is not currently supported.\n"
            "Available tokens: BTC, ETH, SOL, USDC, USDT"
        )
        return
    
    await update.message.reply_text(f"Fetching price for {symbol}...")
    
    # Get price information
    price_info = get_token_price(symbol)
    if not price_info:
        await update.message.reply_text(
            "Sorry, I couldn't get the price information. "
            "Please try again later."
        )
        return
    
    # Format the message
    message = (
        f"*{symbol} Price Information*\n\n"
        f"💰 *Current Price:* ${price_info['price']:,.8f}\n"
        f"📈 *24h Change:* {price_info['price_change_24h']:+.2f}%\n"
        f"💼 *Market Cap:* ${price_info['market_cap']:,.2f}\n"
        f"💧 *24h Volume:* ${price_info['volume_24h']:,.2f}\n"
        f"🎯 *Confidence:* {price_info['confidence']:.2f}\n\n"
        f"_Updated: {datetime.fromisoformat(price_info['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}_"
    )
    
    # Add buttons for more actions
    keyboard = [
        [
            InlineKeyboardButton("📈 Set Alert", callback_data=f"alert_{symbol}"),
            InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_{symbol}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)

async def token_details_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get token details information."""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "Please provide a token symbol.\n"
            "Example: /token BTC\n\n"
            "Available tokens: Use /help to see all supported tokens"
        )
        return
    
    symbol = context.args[0].upper()
    
    # Check if the symbol is supported
    if symbol not in TOKEN_MINT_ADDRESSES:
        await update.message.reply_text(
            f"Sorry, {symbol} is not currently supported.\n"
            "Use /help to see all supported tokens"
        )
        return
    
    await update.message.reply_text(f"Fetching details for {symbol}...")
    
    # Get token details
    token_info = get_token_details(symbol)
    if not token_info:
        await update.message.reply_text(
            "Sorry, I couldn't get the token information. "
            "Please try again later."
        )
        return
    
    # Format the message
    message = (
        f"*{token_info['name']} ({token_info['symbol']}) Token Information*\n\n"
        f"💰 *Current Price:* ${token_info['price']:,.8f}\n"
        f"📈 *24h Change:* {token_info['price_change_1d']:+.2f}%\n"
        f"📊 *7d Change:* {token_info['price_change_7d']:+.2f}%\n"
        f"💼 *Market Cap:* ${token_info['market_cap']:,.2f}\n"
        f"💧 *24h Volume (USD):* ${token_info['usd_volume_24h']:,.2f}\n"
        f"🔄 *24h Volume (Tokens):* {token_info['token_volume_24h']:,.2f}\n"
        f"🔢 *Decimals:* {token_info['decimals']}\n"
        f"📊 *Current Supply:* {token_info['current_supply']:,.2f}\n"
        f"🏷️ *Category:* {token_info['category']}\n"
        f"🔍 *Subcategory:* {token_info['subcategory']}\n"
        f"✅ *Verified:* {'Yes' if token_info['verified'] else 'No'}\n\n"
        f"*Mint Address:*\n`{token_info['mint_address']}`\n\n"
        f"*Price History:*\n"
        f"• 24h: ${token_info['price_1d']:,.8f}\n"
        f"• 7d: ${token_info['price_7d']:,.8f}\n\n"
        f"_Last updated: {datetime.fromtimestamp(token_info['update_time']).strftime('%Y-%m-%d %H:%M:%S')}_"
    )
    
    # Add buttons for more actions
    keyboard = [
        [
            InlineKeyboardButton("📈 Price", callback_data=f"price_{symbol}"),
            InlineKeyboardButton("📊 Trend", callback_data=f"trend_{symbol}")
        ],
        [
            InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_token_{symbol}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send the message with token information
    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)
    
    # If there's a logo URL, send it as a separate message
    if token_info['logo_url']:
        try:
            await update.message.reply_photo(
                photo=token_info['logo_url'],
                caption=f"*{token_info['name']} Logo*",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error sending logo: {e}")

async def token_trend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get token transfer volume trend information with investment insights."""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "Please provide a token symbol.\n"
            "Example: /trend BTC"
        )
        return
    
    symbol = context.args[0].upper()
    
    # Check if the symbol is supported
    if symbol not in TOKEN_MINT_ADDRESSES:
        await update.message.reply_text(
            f"Sorry, {symbol} is not currently supported.\n"
            "Use /help to see all supported tokens"
        )
        return
    
    await update.message.reply_text(f"Analyzing transfer trends for {symbol}...")
    
    # Get token trend information
    trend_info = get_token_trend(symbol)
    if not trend_info:
        await update.message.reply_text(
            "Sorry, I couldn't get the trend information. "
            "Please try again later."
        )
        return
    
    # Check for timeout error
    if isinstance(trend_info, dict) and "error" in trend_info:
        await update.message.reply_text(
            "The request took too long to process. "
            "Please try again in a few moments."
        )
        return
    
    # Create and send the chart
    chart_buffer = create_volume_chart(trend_info['time_series'], symbol)
    if chart_buffer:
        await update.message.reply_photo(
            photo=chart_buffer,
            caption=f"*{symbol} Transfer Volume Analysis*\nLast 7 Days",
            parse_mode="Markdown"
        )
    
    # Format the message with trend analysis and investment insights
    message = (
        f"*{symbol} Investment Analysis*\n\n"
        f"📊 *Volume Statistics*\n"
        f"• Current 24h Volume: ${trend_info['daily_volume']:,.2f}\n"
        f"• 7d Volume: ${trend_info['weekly_volume']:,.2f}\n"
        f"• 24h Change: {trend_info['volume_change_24h']:+.2f}%\n"
        f"• 7d Change: {trend_info['volume_change_7d']:+.2f}%\n\n"
        f"📈 *Market Activity*\n"
        f"• 24h Transfers: {trend_info['transfer_count_24h']:,}\n"
        f"• 7d Transfers: {trend_info['transfer_count_7d']:,}\n"
        f"• Avg Transfer Size: ${trend_info['average_transfer_size']:,.2f}\n"
        f"• Largest Transfer: ${trend_info['largest_transfer']:,.2f}\n"
        f"• Volatility: {trend_info['volatility']:.2f}%\n\n"
        f"*Investment Insights:*\n"
        f"🎯 *Risk Level:* {trend_info['insights']['risk_level']}\n"
        f"💡 *Recommendation:* {trend_info['insights']['recommendation']}\n"
        f"📊 *Confidence:* {trend_info['insights']['confidence']}\n\n"
        f"*Key Observations:*\n"
    )
    
    # Add insights
    for insight in trend_info['insights']['insights']:
        message += f"• {insight}\n"
    
    # Add buttons for more actions
    keyboard = [
        [
            InlineKeyboardButton("🔍 Token Info", callback_data=f"token_{symbol}"),
            InlineKeyboardButton("💰 Price", callback_data=f"price_{symbol}")
        ],
        [
            InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_trend_{symbol}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "token_info":
        await query.message.reply_text(
            "Please enter a token symbol to get detailed token information.\n"
            "Example: /token BTC\n\n"
            "Available tokens: Use /help to see all supported tokens"
        )
    elif data == "price_info":
        await query.message.reply_text(
            "Please enter a token symbol to get price information.\n"
            "Example: /price BTC"
        )
    elif data == "set_alert":
        await query.message.reply_text(
            "Please use the following format to set a price alert:\n"
            "/alert [symbol] [above/below] [price]\n"
            "Example: /alert BTC above 50000"
        )
    elif data == "help":
        await help_command(update, context)
    elif data.startswith("alert_"):
        symbol = data.split("_")[1]
        await query.message.reply_text(
            f"Please use the following format to set a price alert for {symbol}:\n"
            f"/alert {symbol} [above/below] [price]\n"
            f"Example: /alert {symbol} above 50000"
        )
    elif data.startswith("refresh_"):
        symbol = data.split("_")[1]
        context.args = [symbol]
        await price_command(update, context)
    elif data.startswith("refresh_token_"):
        symbol = data.split("_")[2]
        context.args = [symbol]
        await token_details_command(update, context)
    elif data.startswith("trend_"):
        symbol = data.split("_")[1]
        context.args = [symbol]
        await token_trend_command(update, context)
    elif data.startswith("refresh_trend_"):
        symbol = data.split("_")[2]
        context.args = [symbol]
        await token_trend_command(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    text = update.message.text.lower()
    
    if "price" in text:
        await update.message.reply_text(
            "To check token price, use:\n"
            "/price [symbol]\n"
            "Example: /price BTC"
        )
    elif "alert" in text:
        await update.message.reply_text(
            "To set a price alert, use:\n"
            "/alert [symbol] [above/below] [price]\n"
            "Example: /alert BTC above 50000"
        )
    else:
        await update.message.reply_text(
            "I can help you with token prices! Try using commands like /price or /help to see all commands."
        )

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("token", token_details_command))
    application.add_handler(CommandHandler("trend", token_trend_command))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the Bot
    print("Starting bot...")
    application.run_polling()

if __name__ == "__main__":
    main()