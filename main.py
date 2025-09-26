import asyncio
import time
import logging
import os
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import (
    MessageEntityMention, MessageEntityMentionName,
    ChannelParticipantsAdmins, ChannelParticipantsBots,
    ChatBannedRights, ChatAdminRights
)
from telethon.tl.functions.channels import (
    EditBannedRequest, EditAdminRequest,
    DeleteMessagesRequest
)
from telethon.tl.functions.messages import ReportRequest
import random
import aiohttp
from PIL import Image, ImageDraw, ImageFont
import io
import json

# Import web server for keep-alive
from web_server import keep_alive

# Start keep-alive server
keep_alive()

# Configuration from environment variables (for cloud deployment)
API_ID = int(os.environ.get('API_ID', 123456))
API_HASH = os.environ.get('API_HASH', 'your_api_hash_here')
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'your_bot_token_here')
SESSION_NAME = os.environ.get('SESSION_NAME', 'kingmarve_bot')
OWNER_ID = int(os.environ.get('OWNER_ID', 123456789))
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeepSeekAI:
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
    
    async def generate_response(self, message: str) -> str:
        if not self.api_key:
            return "❌ DeepSeek API key not configured."
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": message}
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['choices'][0]['message']['content'].strip()
                    else:
                        return f"❌ API error: {response.status}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

class KingMarveBot:
    def __init__(self):
        self.client = None
        self.start_time = time.time()
        self.user_sessions = {}
        self.waiting_for_phone = {}
        self.waiting_for_code = {}
        self.deepseek_ai = DeepSeekAI()
        
        # Settings storage
        self.autoreply_status = {}
        self.antilink_status = {}
        self.antidelete_status = {}
        self.private_mode = {}
        self.autoreact_status = {}
        self.welcome_messages = {}

    async def start_bot(self):
        """Start the bot with cloud optimization"""
        try:
            self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
            
            # Register event handlers
            await self.register_handlers()
            
            # Start the bot
            await self.client.start(bot_token=BOT_TOKEN)
            
            logger.info("🌑 𝐊𝐈𝐍̃𝐆 𝐌𝐀̊𝐑𝐕𝐄̈ 𝐔𝐒𝐄𝐑 𝐁𝐎𝐓 Started!")
            logger.info("👑 𝗖𝗿𝗲𝗮𝘁𝗼𝗿: K1ÑG MÅRVË x Drenox")
            logger.info("🔥 𝗛𝗼𝘀𝘁𝗲𝗱 𝗼𝗻: CLOUD (24/7)")
            logger.info("📡 𝗦𝘁𝗮𝘁𝘂𝘀: Online 24/7")
            
            # Send startup message to owner
            if OWNER_ID:
                try:
                    await self.client.send_message(
                        OWNER_ID, 
                        "🤖 **Bot started successfully on cloud!**\n🌐 **Status:** Online 24/7"
                    )
                except:
                    pass
            
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            # Attempt to restart after delay
            await asyncio.sleep(60)
            await self.start_bot()

    async def register_handlers(self):
        """Register all event handlers"""
        
        # Authentication commands
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            await self.handle_start(event)
        
        @self.client.on(events.NewMessage(pattern='/connect'))
        async def connect_handler(event):
            await self.handle_connect(event)
        
        @self.client.on(events.NewMessage(pattern='/verify'))
        async def verify_handler(event):
            await self.handle_verify(event)
        
        @self.client.on(events.NewMessage(pattern='/disconnect'))
        async def disconnect_handler(event):
            await self.handle_disconnect(event)
        
        @self.client.on(events.NewMessage(pattern=r'\.reportbug'))
        async def reportbug_handler(event):
            await self.handle_reportbug(event)

        # Command categories
        @self.client.on(events.NewMessage(pattern=r'\.(ping|about|hello|vv)'))
        async def basic_handler(event):
            if await self.check_auth(event):
                await self.handle_basic_commands(event)

        @self.client.on(events.NewMessage(pattern=r'\.(sticker|tagall)'))
        async def group_handler(event):
            if await self.check_auth(event):
                await self.handle_group_commands(event)

        @self.client.on(events.NewMessage(pattern=r'\.(ban|unban|kick|mute|unmute|promote|demote)'))
        async def admin_handler(event):
            if await self.check_auth(event):
                await self.handle_admin_commands(event)

        @self.client.on(events.NewMessage(pattern=r'\.(pin|unpin|delete|lock|unlock)'))
        async def chat_handler(event):
            if await self.check_auth(event):
                await self.handle_chat_commands(event)

        @self.client.on(events.NewMessage(pattern=r'\.(antilink|antidelete|private|autoreply)'))
        async def settings_handler(event):
            if await self.check_auth(event):
                await self.handle_settings_commands(event)

        @self.client.on(events.NewMessage(pattern=r'\.(block|unblock|linkgc|setwelcome|track)'))
        async def utility_handler(event):
            if await self.check_auth(event):
                await self.handle_utility_commands(event)

        @self.client.on(events.NewMessage(pattern=r'\.(tovnote|purchase|info|pickuplines|uptime)'))
        async def fun_handler(event):
            if await self.check_auth(event):
                await self.handle_fun_commands(event)

        @self.client.on(events.NewMessage(pattern=r'\.(snake|toimage|gpt|get|pp|autoreact|clearadmins|channel|translate)'))
        async def advanced_handler(event):
            if await self.check_auth(event):
                await self.handle_advanced_commands(event)

        # Phone number handler
        @self.client.on(events.NewMessage())
        async def message_handler(event):
            user_id = event.sender_id
            if user_id in self.waiting_for_phone:
                await self.handle_phone_number(event)

    async def check_auth(self, event):
        """Check if user is authenticated"""
        user_id = event.sender_id
        if user_id not in self.user_sessions:
            await event.reply("❌ You need to connect first! Use `/connect`")
            return False
        return True

    # Authentication handlers
    async def handle_start(self, event):
        welcome_text = """
🌑 **𝐊𝐈𝐍̃𝐆 𝐌𝐀̊𝐑𝐕𝐄̈ 𝐔𝐒𝐄𝐑 𝐁𝐎𝐓**   

👑 **𝗖𝗿𝗲𝗮𝘁𝗼𝗿:** K1ÑG MÅRVË x Drenox  
🔥 **𝗛𝗼𝘀𝘁𝗲𝗱 𝗼𝗻:** CLOUD (24/7 Online)  
📞 **𝗖𝗢𝗡𝗧𝗔𝗖𝗧:** [t.me/ask_of_kingmarve]  

🤖 **To get started:**
1. Use `/connect` to connect your account
2. Send your phone number when asked
3. Use `/verify` with the code you receive

💡 **Bot features 24/7 uptime on cloud hosting!**
        """
        await event.reply(welcome_text)

    async def handle_connect(self, event):
        user_id = event.sender_id
        
        if user_id in self.user_sessions:
            await event.reply("✅ You are already connected!")
            return
        
        self.waiting_for_phone[user_id] = True
        await event.reply(
            "📱 **Please send your phone number in international format:**\n\n"
            "Example: `+1234567890`\n\n"
            "⚠️ **This will be used to log into your Telegram account.**"
        )

    async def handle_phone_number(self, event):
        user_id = event.sender_id
        
        if user_id not in self.waiting_for_phone:
            return
        
        phone_number = event.text.strip()
        
        if not re.match(r'^\+\d{10,15}$', phone_number):
            await event.reply("❌ Invalid phone number format. Use: `+1234567890`")
            return
        
        try:
            client = TelegramClient(StringSession(), API_ID, API_HASH)
            await client.connect()
            
            sent_code = await client.send_code_request(phone_number)
            
            self.waiting_for_code[user_id] = {
                'phone_number': phone_number,
                'phone_code_hash': sent_code.phone_code_hash,
                'client': client
            }
            
            del self.waiting_for_phone[user_id]
            
            await event.reply(
                "✅ **Verification code sent!**\n\n"
                "Use `/verify CODE` to complete login.\n"
                "Example: `/verify 12345`"
            )
            
        except Exception as e:
            await event.reply(f"❌ Error: {str(e)}")
            if user_id in self.waiting_for_phone:
                del self.waiting_for_phone[user_id]

    async def handle_verify(self, event):
        user_id = event.sender_id
        
        if user_id not in self.waiting_for_code:
            await event.reply("❌ No verification pending. Use `/connect` first.")
            return
        
        code = event.text.split(' ', 1)
        if len(code) < 2:
            await event.reply("❌ Usage: `/verify 12345`")
            return
        
        verification_code = code[1].strip()
        user_data = self.waiting_for_code[user_id]
        
        try:
            await user_data['client'].sign_in(
                phone=user_data['phone_number'],
                code=verification_code,
                phone_code_hash=user_data['phone_code_hash']
            )
            
            me = await user_data['client'].get_me()
            session_string = user_data['client'].session.save()
            
            self.user_sessions[user_id] = {
                'client': user_data['client'],
                'session_string': session_string,
                'user': me
            }
            
            del self.waiting_for_code[user_id]
            
            await event.reply(
                f"✅ **Successfully connected!**\n\n"
                f"👤 **User:** {me.first_name}\n"
                f"📱 **Phone:** {me.phone}\n"
                f"🆔 **ID:** {me.id}\n\n"
                f"💡 **You can now use all bot commands!**"
            )
            
        except Exception as e:
            await event.reply(f"❌ Verification failed: {str(e)}")

    async def handle_disconnect(self, event):
        user_id = event.sender_id
        
        if user_id in self.user_sessions:
            await self.user_sessions[user_id]['client'].disconnect()
            del self.user_sessions[user_id]
            
            if user_id in self.waiting_for_phone:
                del self.waiting_for_phone[user_id]
            if user_id in self.waiting_for_code:
                del self.waiting_for_code[user_id]
            
            await event.reply("✅ **Disconnected successfully!**")
        else:
            await event.reply("❌ You are not connected.")

    async def handle_reportbug(self, event):
        """Report bugs to the bot owner"""
        bug_report = event.text.split('.reportbug', 1)
        if len(bug_report) < 2 or not bug_report[1].strip():
            await event.reply("❌ Usage: `.reportbug bug_description`")
            return
        
        try:
            if OWNER_ID:
                bug_text = f"🐛 **Bug Report**\nFrom: {event.sender_id}\n\n{bug_report[1].strip()}"
                await event.client.send_message(OWNER_ID, bug_text)
            
            await event.reply("✅ **Bug report sent to developer!**")
        except Exception as e:
            await event.reply("❌ Failed to send bug report.")

    # Command implementations (shortened for brevity)
    async def handle_basic_commands(self, event):
        command = event.pattern_match.group(1).lower()
        
        if command == "ping":
            start = time.time()
            message = await event.reply("🏓 Pong!")
            end = time.time()
            await message.edit(f"🏓 Pong! `{round((end - start) * 1000, 3)}ms`")
            
        elif command == "about":
            about_text = """
🌑 **𝐊𝐈𝐍̃𝐆 𝐌𝐀̊𝐑𝐕𝐄̈ 𝐔𝐒𝐄𝐑 𝐁𝐎𝐓**
👑 **Creator:** K1ÑG MÅRVË x Drenox
🔥 **Hosted on:** CLOUD (24/7)
📞 **Contact:** @ask_of_kingmarve
💻 **Status:** Online 24/7
            """
            await event.reply(about_text)
            
        elif command == "hello":
            await event.reply("👋 Hello! I'm 𝐊𝐈𝐍̃𝐆 𝐌𝐀̊𝐑𝐕𝐄̈ 𝐔𝐒𝐄𝐑 𝐁𝐎𝐓!")
            
        elif command == "vv":
            await event.reply("👁️ Viewing...")

    async def handle_group_commands(self, event):
        command = event.pattern_match.group(1).lower()
        
        if command == "sticker":
            if event.reply_to_msg_id:
                reply = await event.get_reply_message()
                if reply.media:
                    await event.client.send_file(event.chat_id, reply.media, force_document=False)
                else:
                    await event.reply("❌ Reply to an image to make a sticker")
            else:
                await event.reply("❌ Reply to an image with .sticker")
                
        elif command == "tagall":
            if not await event.get_chat():
                await event.reply("❌ This command works in groups only")
                return
                
            participants = await event.client.get_participants(event.chat_id)
            mentions = []
            for participant in participants:
                if not participant.bot:
                    mentions.append(f"👤 [{participant.first_name}](tg://user?id={participant.id})")
            
            await event.reply("\n".join(mentions))

    # Add other command handlers similarly...
    async def handle_admin_commands(self, event):
        command = event.pattern_match.group(1).lower()
        await event.reply(f"🔧 Admin command: {command}")

    async def handle_chat_commands(self, event):
        command = event.pattern_match.group(1).lower()
        await event.reply(f"💬 Chat command: {command}")

    async def handle_settings_commands(self, event):
        command = event.pattern_match.group(1).lower()
        await event.reply(f"⚙️ Settings command: {command}")

    async def handle_utility_commands(self, event):
        command = event.pattern_match.group(1).lower()
        await event.reply(f"🔧 Utility command: {command}")

    async def handle_fun_commands(self, event):
        command = event.pattern_match.group(1).lower()
        
        if command == "uptime":
            uptime = time.time() - self.start_time
            hours, remainder = divmod(uptime, 3600)
            minutes, seconds = divmod(remainder, 60)
            await event.reply(f"⏰ **Uptime:** {int(hours)}h {int(minutes)}m {int(seconds)}s")
            
        elif command == "pickuplines":
            lines = [
                "Are you a magician? Because whenever I look at you, everyone else disappears.",
                "Do you have a map? I keep getting lost in your eyes.",
                "Is your name Google? Because you have everything I've been searching for.",
                "Are you a camera? Because every time I look at you, I smile.",
                "Do you believe in love at first sight, or should I walk by again?"
            ]
            await event.reply(random.choice(lines))
            
        else:
            await event.reply(f"🎉 Fun command: {command}")

    async def handle_advanced_commands(self, event):
        command = event.pattern_match.group(1).lower()
        text = event.text.split(' ', 1)
        args = text[1] if len(text) > 1 else ""
        
        if command == "gpt":
            if not args:
                await event.reply("❌ Usage: `.gpt your_question`")
                return
                
            async with event.client.action(event.chat_id, 'typing'):
                response = await self.deepseek_ai.generate_response(args)
                await event.reply(f"🤖 **DeepSeek AI:**\n\n{response}")
                
        elif command == "translate":
            if not args:
                await event.reply("❌ Usage: `.translate your_text`")
                return
            await event.reply(f"🌍 Translate: {args}")
            
        else:
            await event.reply(f"🚀 Advanced command: {command}")

async def main():
    bot = KingMarveBot()
    await bot.start_bot()

if __name__ == "__main__":
    # Cloud-optimized execution
    print("🌑 Starting 𝐊𝐈𝐍̃𝐆 𝐌𝐀̊𝐑𝐕𝐄̈ 𝐔𝐒𝐄𝐑 𝐁𝐎𝐓 on cloud...")
    asyncio.run(main())
