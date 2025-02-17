import asyncio
import random
import ssl
import time
import uuid
import json
import requests
import os, base64
from loguru import logger
from fake_useragent import UserAgent
from base64 import b64decode, b64encode
import aiohttp
from aiohttp import ClientSession, ClientWebSocketResponse
from urllib.parse import urlparse
from colorama import Fore, Style, init

init(autoreset=True)

def welcome():
    print(
        f"""
        {Fore.WHITE + Style.BRIGHT}
  
                  █████╗  ███████╗  █████╗       
                 ██╔══██╗ ██╔════╝ ██╔══██╗      
          █████╗ ███████║ ███████╗ ███████║ █████╗
          ╚════╝ ██╔══██║ ╚════██║ ██╔══██║ ╚════╝
                 ██║  ██║ ███████║ ██║  ██║      
                 ╚═╝  ╚═╝ ╚══════╝ ╚═╝  ╚═╝      
        """
        f"""
        {Fore.YELLOW + Style.BRIGHT}Grass - BOT {Fore.YELLOW + Style.BRIGHT}| Run With Proxy & Without Proxy 
        """
    )
def format_proxy(proxy_str):
    
    if not proxy_str:
        return None
    
    parsed = urlparse(proxy_str)
    if parsed.username and parsed.password:
        return f"{parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}"
    return proxy_str
async def connect_to_wss(socks5_proxy, user_id):
    user_agent = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"
    ]
    random_user_agent = random.choice(user_agent)
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy if socks5_proxy else "localhost"))
    logger.info(device_id)
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": random_user_agent,
                "Origin": "chrome-extension://ilehaonighjijnmpnagapkhpcdbhclfg"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://proxy2.wynd.network:4444"
            proxy_url = format_proxy(socks5_proxy)
            connector = aiohttp.TCPConnector(ssl_context=ssl_context)
            async with ClientSession(connector=connector) as session:
                async with session.ws_connect(uri, headers=custom_headers, proxy=proxy_url) as websocket:
                    response = await websocket.receive()
                    message = json.loads(response.data)
                    logger.info(message)
                    if message["action"] == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "extension",
                                "version": "5.0.0",
                                "extension_id": "ilehaonighjijnmpnagapkhpcdbhclfg"
                            }
                        }
                        logger.debug(auth_response)
                        await websocket.send_json(auth_response)
                        
                        response_auth = await websocket.receive()
                        message_auth = json.loads(response_auth.data)
                        logger.info(message_auth)
                        
                        if message_auth["action"] == "HTTP_REQUEST":
                            headers = {
                                "Content-Type": "application/json; charset=utf-8",
                                "User-Agent": custom_headers['User-Agent']
                            }

                            async with session.get(message_auth["data"]["url"], headers=headers, proxy=proxy_url) as response:
                                result = await response.json()
                                content = await response.text()
                                code = result.get('code')
                                if None == code:
                                    logger.error(f"Error send http")
                                    logger.error(f"Status : {response.status}")
                                else:
                                    logger.info(f"Send http success : {code}")
                                    logger.info(f"Status : {response.status}")
                                    response_body = base64.b64encode(content.encode()).decode()
                                    httpreq_response = {
                                        "id": message_auth["id"],
                                        "origin_action": "HTTP_REQUEST",
                                        "result": {
                                            "url": message_auth["data"]["url"],
                                            "status": response.status,
                                            "status_text": response.reason,
                                            "headers": dict(response.headers),
                                            "body": response_body
                                        }
                                    }
                                    logger.debug(httpreq_response)
                                    await websocket.send_json(httpreq_response)
                            
                        while True:
                            send_ping = {
                                "id": str(uuid.uuid4()),
                                "version": "1.0.0",
                                "action": "PING",
                                "data": {}
                            }
                            logger.debug(send_ping)
                            await websocket.send_json(send_ping)
                    
                            response_ping = await websocket.receive()
                            message_ping = json.loads(response_ping.data)
                            logger.info(message_ping)
                            
                            if message_ping["action"] == "PONG":
                                pong_response = {
                                    "id": message_ping["id"],
                                    "origin_action": "PONG"
                                }
                                logger.debug(pong_response)
                                await websocket.send_json(pong_response)
                                await asyncio.sleep(5)
        except Exception as e:
            logger.error(e)
            logger.error(socks5_proxy)

    
def print_question():
    print("1. Run With Proxy")
    print("2. Run Without Proxy")         

async def main():
    welcome()
    try:
        with open('user_id.txt', 'r') as file:
            _user_id = file.read().strip()
    except FileNotFoundError:
        logger.error("File user_id.txt Not Found!")
        return
   
    print_question()
    mode = input("✅ Please Choose [1 or 2] -> : ")
       
    if mode == "1":
        
        try:
            with open('local_proxies.txt', 'r') as file:
                local_proxies = file.read().splitlines()
            tasks = [asyncio.ensure_future(connect_to_wss(i, _user_id)) for i in local_proxies]
        except FileNotFoundError:
            logger.error("File local_proxies.txt Not Found!")
            return
    elif mode == "2":
        tasks = [asyncio.ensure_future(connect_to_wss("", _user_id))]
    else:
        logger.error("Only Choose No.1 or No.2 ✅")
        return
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
