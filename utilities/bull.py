import random
from utilities.core import logger
from pyrogram import Client, raw
import asyncio
import aiohttp
from fake_useragent import UserAgent
from random import uniform
from data import config
import json
import os
import time
from aiohttp_socks import ProxyConnector
import ssl
import certifi


class BullBot:
    def __init__(self, thread: int, session_name: str, phone_number: str, proxy: [str, None]):
        self.account = session_name + '.session'
        self.thread = thread
        self.proxy = f"{config.PROXY_TYPES['REQUESTS']}://{proxy}" if proxy is not None else None
        self.user_agent_file = "./sessions/user_agents.json"
        self.statistics_file = "./statistics/stats.json"
        self.ref_link_file = "./sessions/ref_links.json"

        if proxy:
            proxy = {
                "scheme": config.PROXY_TYPES['TG'],
                "hostname": proxy.split(":")[1].split("@")[1],
                "port": int(proxy.split(":")[2]),
                "username": proxy.split(":")[0],
                "password": proxy.split(":")[1].split("@")[0]
            }

        with open("./data/api_config.json", "r") as f:
            apis = json.load(f)
            phone_number = apis[phone_number]
            api_id = phone_number[0]
            api_hash = phone_number[1]


        self.client = Client(
            name=session_name,
            api_id=api_id,
            api_hash=api_hash,
            workdir=config.WORKDIR,
            proxy=proxy,
            lang_code="ru"
        )


    async def init_async(self, proxy):
        self.refferal_link = await self.get_ref_link()
        user_agent = await self.get_user_agent()
        headers = {'User-Agent': user_agent}
        connector = ProxyConnector.from_url(self.proxy) if proxy else aiohttp.TCPConnector(verify_ssl=False)
        self.session = aiohttp.ClientSession(headers=headers, trust_env=True, connector=connector, timeout=aiohttp.ClientTimeout(120))
        self.initialized = True


    @classmethod
    async def create(cls, thread: int, session_name: str, phone_number: str, proxy: [str, None]):
        instance = cls(session_name=session_name, phone_number=phone_number, thread=thread, proxy=proxy)
        await instance.init_async(proxy)
        return instance


    async def get_ref_link(self):
        ref_links = await self.load_ref_links()
        if self.account in ref_links:
            if "Bull" in ref_links[self.account]:
                return ref_links[self.account]["Bull"]
        else:
            return None


    async def load_ref_links(self):
        if os.path.exists(self.ref_link_file):
            with open(self.ref_link_file, "r") as f:
                return json.load(f)
        else:
            return {}
        
    
    async def save_ref_links(self, ref_links):
        os.makedirs(os.path.dirname(self.ref_link_file), exist_ok=True)
        with open(self.ref_link_file, "w") as f:
            json.dump(ref_links, f, indent=4)


    async def referrals_check(self, resp_json):
            if self.refferal_link is None:
                ref_links = await self.load_ref_links()
                if self.account in ref_links:
                    bull_ref = ref_links[self.account]
                    bull_ref["Bull"] = resp_json["arguments"][0]["o"]["link"]
                else:
                    ref_links[self.account] = {'Bull': resp_json["arguments"][0]["o"]["link"]} 
                
                await self.save_ref_links(ref_links)


    async def get_user_agent(self):
        user_agents = await self.load_user_agents()
        if self.account in user_agents:
            return user_agents[self.account]
        else:
            new_user_agent = UserAgent(os='ios').random
            user_agents[self.account] = new_user_agent
            await self.save_user_agents(user_agents)
            return new_user_agent
        

    async def load_user_agents(self):
        if os.path.exists(self.user_agent_file):
            with open(self.user_agent_file, "r") as f:
                return json.load(f)
        else:
            return {}
        

    async def save_user_agents(self, user_agents):
        os.makedirs(os.path.dirname(self.user_agent_file), exist_ok=True)
        with open(self.user_agent_file, "w") as f:
            json.dump(user_agents, f, indent=4)


    async def get_stats(self, resp_json):
        stats = await self.load_stats()
        balance = resp_json["arguments"][0]["o"]["balance"]
        boost1 = resp_json["arguments"][0]["o"]["boost1"]
        boost2 = resp_json["arguments"][0]["o"]["boost2"]
        friends = resp_json["arguments"][0]["o"]["friends"]
        completed = resp_json["arguments"][0]["o"]["completed"]
        if self.account in stats:
            if "Bull" in stats[self.account]:
                stats[self.account]["Bull"] = {
                    "balance": balance,
                    "boost1": boost1,
                    "boost2": boost2,
                    "friends": friends,
                    "completed": completed
                }
            else:
                bull_stats = stats[self.account]
                bull_stats["Bull"] = {
                    "balance": balance,
                    "boost1": boost1,
                    "boost2": boost2,
                    "friends": friends,
                    "completed": completed
                }
        else:
            bull_stats = stats[self.account] = {"Bull": 
                {"balance": balance,
                "boost1": boost1,
                "boost2": boost2,
                "friends": friends,
                "completed": completed
                }
            }
        await self.save_stats(stats)
        

    async def load_stats(self):
        if os.path.exists(self.statistics_file):
            with open(self.statistics_file, "r") as f:
                return json.load(f)
        else:
            return {}


    async def save_stats(self, stats):
        os.makedirs(os.path.dirname(self.statistics_file), exist_ok=True)
        with open(self.statistics_file, "w") as f:
            json.dump(stats, f, indent=4)


    async def negotiate_request(self):
        negotiate_url = 'https://bullapp.online/hub/negotiate?negotiateVersion=1'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Referer': 'https://bullapp.online/app',
            'X-Requested-With': 'XMLHttpRequest',
            'X-SignalR-User-Agent': 'Microsoft SignalR/8.0 (8.0.0; Unknown OS; Browser; Unknown Runtime Version)',
            'Origin': 'https://bullapp.online',
            'DNT': '1',
            'Sec-GPC': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=6',
        }
        
        async with self.session.post(negotiate_url, headers=headers) as response:
            negotiate_response = await response.json()
        
        return negotiate_response['connectionToken']
        

    async def make_tasks(self, ws, resp_json):
        completed_tasks = resp_json["arguments"][0]["o"]["completed"]
        for mission in resp_json["arguments"][0]["o"]["missions"]:
            if mission["id"] not in completed_tasks:
                logger.success(f"Bull | Thread {self.thread} | {self.account} | Task id: {mission["id"]}")
                if 'url' in mission and 'https://t.me/' in mission["url"]:
                    await self.client.connect()
                    try:
                        if '+' in mission['url']:
                            await self.client.join_chat(mission['url'])
                        else:
                            await self.client.join_chat(mission['url'].split('/')[3])
                        await ws.send_str(json.dumps({"type": 6}) + '\x1e')
                        await asyncio.sleep(uniform(5,8))
                    except Exception as e:
                        print("e = ", e)

                    await self.client.disconnect()

                mission_claim_message = {
                    "arguments":[self.my_id, mission["id"]],
                    "invocationId":"0",
                    "target":"Mission",
                    "type": 1
                }
                await ws.send_str(json.dumps(mission_claim_message) + '\x1e')
                await asyncio.sleep(uniform(5, 8))


    async def upgrade_boosts(self, ws, resp_json):
        balance = resp_json["arguments"][0]["o"]["balance"]
        boost1_upgraded = 0
        boost2_upgraded = 0
        next_boost2 = resp_json["arguments"][0]["o"]["boost2_next"]
        if next_boost2 != None and balance > next_boost2["coins"]:
            boost2_message = {
                "arguments":[
                    self.my_id
                ],
                "invocationId":"1",
                "target":"Boost2",
                "type":1
            }
            await ws.send_str(json.dumps(boost2_message) + '\x1e')
            balance = balance - next_boost2["coins"]
            logger.success(f"Bull| Thread {self.thread} | {self.account} | Boost2 upgraded!, Balance: {balance}")
            boost2_upgraded += 1
            await asyncio.sleep(uniform(5, 8))

        # if balance > next_boost1["coins"]:
        #     boost1_message = {
        #         "arguments":[
        #             self.my_id
        #         ],
        #         "invocationId":"1",
        #         "target":"Boost1",
        #         "type":1
        #     }
        #     await ws.send_str(json.dumps(boost1_message) + '\x1e')
        #     balance = balance - next_boost1["coins"]
        #     logger.success(f"Bull | Thread {self.thread} | {self.account} | Boost1 upgraded!, Balance: {balance}")
        #     boost1_upgraded += 1 
        #     await asyncio.sleep(uniform(5, 8))
        
        return balance, boost1_upgraded, boost2_upgraded


    async def login(self):

        # Первый запрос на negotiate для получения токена
        connection_token = await self.negotiate_request()

        
        # Второй запрос на установление WebSocket-соединения
        websocket_url = f'wss://bullapp.online/hub?id={connection_token}'
        ws_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Origin': 'https://bullapp.online',
            'Sec-WebSocket-Version': '13',
            'Sec-WebSocket-Extensions': 'permessage-deflate',
            'Sec-WebSocket-Key': 'LU2h4wXCRP11ukRd/u5mXw==',
            'Sec-WebSocket-Protocol': 'json',
            'DNT': '1',
            'Sec-GPC': '1',
            'Connection': 'keep-alive, Upgrade',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'websocket',
            'Sec-Fetch-Site': 'same-origin',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Upgrade': 'websocket',
        }
        ssl_context = ssl.create_default_context()
        ssl_context.load_verify_locations(certifi.where())
        async with self.session.ws_connect(websocket_url, headers=ws_headers, ssl=ssl_context) as ws:
            # Отправляем {"protocol":"json","version":1}
            await ws.send_str(json.dumps({"protocol": "json", "version": 1}) + '\x1e')
            response = await ws.receive()
            
            # Проверяем ответ и выполняем дальнейшие шаги только если ответ успешный
            if response.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(response.data[:-1])  # Убираем терминатор \x1e
                if data == {}:
                    # Отправляем {"type":6} Пинг
                    await ws.send_str(json.dumps({"type": 6}) + '\x1e')
                    
                    # Отправляем {"arguments":[self.my_id,"en"],"invocationId":"0","target":"Init","type":1}
                    init_message = {
                        "arguments": [self.my_id, "en"],
                        "invocationId": "0",
                        "target": "Init",
                        "type": 1
                    }
                    await ws.send_str(json.dumps(init_message) + '\x1e')
                    
                    # Получаем ответ
                    response = await ws.receive()
                    resp_json = json.loads(response.data[:-1])
                    
                    # Проверяем реферальную ссылку и сохраняем, если ещё не сохранена
                    await self.referrals_check(resp_json)

                    # Выполянем все задания
                    await self.make_tasks(ws=ws, resp_json=resp_json)

                    # Забираем ежедневную награду
                    claim_daily_message = {"arguments":[self.my_id],"invocationId":"1","target":"DailyClaim","type":1}
                    await ws.send_str(json.dumps(claim_daily_message) + '\x1e')
                    await asyncio.sleep(uniform(5,8))
                    
                    # Улучшаем бусты, если можно
                    balance, boost1_upgraded, boost2_upgraded = await self.upgrade_boosts(ws, resp_json)
                    
                    resp_json["arguments"][0]["o"]["balance"] = balance
                    resp_json["arguments"][0]["o"]["boost1"] += boost1_upgraded
                    resp_json["arguments"][0]["o"]["boost2"] += boost2_upgraded
                    
                    # Записываем статистику
                    await self.get_stats(resp_json)

                    logger.info(f"Bull | Thread {self.thread} | {self.account} | Balance: {resp_json["arguments"][0]["o"]["balance"]}")

                    # Пинг
                    await ws.send_str(json.dumps({"type": 6}) + '\x1e')
                    await asyncio.sleep(uniform(3,5))

                    # Смотрим сколько осталось до клейма
                    claim_remain = resp_json["arguments"][0]["o"]["claim_remain"]
                    
                    # Клеймим или нет
                    if claim_remain == 0:
                        claim_message = {"arguments":[self.my_id],"invocationId":"1","target":"Claim","type":1}
                        await ws.send_str(json.dumps(claim_message) + '\x1e')
                        logger.success(f"Bull | Thread {self.thread} | {self.account} | Claimed!")
                    else:
                        time_to_sleep = claim_remain
                        logger.info(f"Bull | Thread {self.thread} | {self.account} | Sleep {time_to_sleep} seconds!")
                        for _ in range(int(time_to_sleep / 60)):
                            await asyncio.sleep(60)
                        
                
                    
                else:
                    print("Unexpected response:", data)
            else:
                print("Failed to establish WebSocket connection:", response)

            
            # logger.info(f"Bull | Thread {self.thread} | {self.account} | Sleep {time_to_sleep} seconds!")
            # await asyncio.sleep(time_to_sleep)


    async def click_start_button(self):
        clicked = False
        try:
            await self.client.connect()
            me = await self.client.get_me()
            self.my_id = me.id
            bot_username = "BullApp_bot"
            bot = await self.client.get_users(bot_username)

            try:
                messages = self.client.get_chat_history(bot.id, limit=1)
                async for message in messages:
                    if message.reply_markup and message.reply_markup.inline_keyboard:
                        # Проверяем, есть ли у нас хотя бы три ряда кнопок
                        if len(message.reply_markup.inline_keyboard) >= 3:
                            third_row_buttons = message.reply_markup.inline_keyboard[2]
                            # Проверяем, есть ли кнопка в третьем ряду
                            if third_row_buttons:
                                button = third_row_buttons[0]  # Берем первую кнопку третьего ряда
                                if button.url:  # Убедимся, что у кнопки есть url
                                    response = await self.session.get(button.url)
                                    logger.info(f"Bull | Thread {self.thread} | {self.account} | Button pressed, status: {response.status}")
                                    clicked = True
                                    await self.client.disconnect()
                                    return clicked
                else:
                    # Если кнопка не найдена, то берем рефаральную ссылку и по ней запускаем бота, потом нажимаем на кнопку
                    logger.info(f"Bull | Thread {self.thread} | {self.account} | Button not found, start with refferal link")
                    with open(self.ref_link_file, 'r') as file:
                        ref_links = json.load(file)
                        session_name = random.choice(list(ref_links.keys()))
                        atemp = 0
                        while "Bull" not in ref_links[session_name] and atemp < 100:
                            session_name = random.choice(list(ref_links.keys()))
                            atemp += 1
                        if atemp == 50:
                            start_param = "https://t.me/BullApp_bot?start=374069367_2816"
                            bot_username = "BullApp_bot"
                        else:
                            # print(ref_links[session_name])
                            referral_link = ref_links[session_name]["Bull"]
                            
                            logger.info(f"Bull | Thread {self.thread} | {self.account} | Selected session: {session_name}, Referral link: {referral_link}")
                            bot_username = referral_link.split("?start=")[0].split("/")[-1]
                            start_param = referral_link.split("?start=")[-1]
                        
                        result = await self.client.invoke(
                            raw.functions.messages.StartBot(
                                bot=await self.client.resolve_peer(bot_username),
                                peer=await self.client.resolve_peer(bot_username),
                                random_id=int(time.time() * 1000),
                                start_param=start_param
                            )
                        )
                        logger.info(f"Bull | Thread {self.thread} | {self.account} | Bot started")
                        clicked = False
            except Exception as e:
                clicked = False
                print("Error:", e)

            await self.client.disconnect()

        except:
            return clicked