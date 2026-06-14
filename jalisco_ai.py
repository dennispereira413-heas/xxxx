"""
╔════════════════════════════════════════════════════════════════╗
║                  🔥 JALISCO AI BOT 🔥                          ║
║           Gestione Server Mafioso - Discord Bot               ║
╚════════════════════════════════════════════════════════════════╝
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
from dotenv import load_dotenv
from datetime import datetime
from config import JALISCO_TOKEN, JALISCO_OWNER, Colors, EMOJI, LOG_LEVEL
from database import db

# ════════════════════════════════════════════════════════════════
# SETUP LOGGING
# ════════════════════════════════════════════════════════════════

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/jalisco_ai.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════
# SETUP BOT
# ════════════════════════════════════════════════════════════════

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)

# ════════════════════════════════════════════════════════════════
# EVENTI BOT
# ════════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    """Bot online"""
    logger.info(f"\n")
    logger.info(f"╔════════════════════════════════════════════════╗")
    logger.info(f"║        🔥 JALISCO AI - ONLINE 🔥             ║")
    logger.info(f"╠════════════════════════════════════════════════╣")
    logger.info(f"║ Bot: {bot.user.name}#{bot.user.discriminator}")
    logger.info(f"║ ID: {bot.user.id}")
    logger.info(f"║ Server: {len(bot.guilds)}")
    logger.info(f"║ Utenti: {len(set(bot.get_all_members()))}")
    logger.info(f"║ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"╚════════════════════════════════════════════════╝")
    logger.info(f"\n")
    
    # Sincronizza slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f"✅ {len(synced)} slash commands sincronizzati")
    except Exception as e:
        logger.error(f"❌ Errore sincronizzazione comandi: {e}")
    
    # Status bot
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="il server 👑"
        ),
        status=discord.Status.online
    )

@bot.event
async def on_guild_join(guild):
    """Bot aggiunto a server"""
    logger.info(f"🎉 Bot aggiunto al server: {guild.name} ({guild.id})")

@bot.event
async def on_guild_remove(guild):
    """Bot rimosso da server"""
    logger.info(f"👋 Bot rimosso dal server: {guild.name} ({guild.id})")

# ════════════════════════════════════════════════════════════════
# COMANDI - SETUP
# ════════════════════════════════════════════════════════════════

@bot.tree.command(name="setup-jalisco", description="🔧 Configura Jalisco AI")
@app_commands.describe(
    owner_id="ID Owner",
    don_ids="ID Don (separati da virgola)",
    admin_ids="ID Admin (separati da virgola)",
    moderator_ids="ID Moderatori (separati da virgola)"
)
async def setup_jalisco(
    interaction: discord.Interaction,
    owner_id: str,
    don_ids: str,
    admin_ids: str,
    moderator_ids: str
):
    """Configurazione iniziale Jalisco AI"""
    
    # Controllo permessi
    if interaction.user.id != JALISCO_OWNER:
        embed = discord.Embed(
            title=f"{EMOJI['error']} Permesso Negato",
            description="Solo l'Owner può configurare il bot",
            color=Colors.ERROR.value
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    try:
        # Parse IDs
        owner_id_int = int(owner_id)
        don_list = [int(id.strip()) for id in don_ids.split(",") if id.strip()]
        admin_list = [int(id.strip()) for id in admin_ids.split(",") if id.strip()]
        mod_list = [int(id.strip()) for id in moderator_ids.split(",") if id.strip()]
        
        # Salva configurazione
        db.save_jalisco_config(
            interaction.guild_id,
            owner_id_int,
            don_list,
            admin_list,
            mod_list
        )
        
        # Risposta
        embed = discord.Embed(
            title=f"{EMOJI['success']} Setup Completato",
            description="Configurazione Jalisco AI salvata",
            color=Colors.JALISCO_GOLD.value
        )
        embed.add_field(name="Owner", value=f"<@{owner_id_int}>", inline=False)
        embed.add_field(name=f"Don ({len(don_list)})", value=", ".join([f"<@{id}>" for id in don_list]) or "Nessuno", inline=False)
        embed.add_field(name=f"Admin ({len(admin_list)})", value=", ".join([f"<@{id}>" for id in admin_list]) or "Nessuno", inline=False)
        embed.add_field(name=f"Moderatori ({len(mod_list)})", value=", ".join([f"<@{id}>" for id in mod_list]) or "Nessuno", inline=False)
        
        await interaction.response.send_message(embed=embed)
        logger.info(f"✅ Setup completato per server {interaction.guild_id}")
        
    except ValueError:
        embed = discord.Embed(
            title=f"{EMOJI['error']} IDs Non Validi",
            description="Usa numeri validi separati da virgole",
            color=Colors.ERROR.value
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ════════════════════════════════════════════════════════════════
# COMANDI - UTENTI
# ════════════════════════════════════════════════════════════════

@bot.tree.command(name="user-info", description="📊 Informazioni utente")
@app_commands.describe(user="Utente da controllare")
async def user_info(interaction: discord.Interaction, user: discord.User = None):
    """Visualizza informazioni utente"""
    
    target = user or interaction.user
    
    # Recupera dati database
    user_data = db.get_bank_account(target.id)  # Usa banca come fallback
    
    embed = discord.Embed(
        title=f"{EMOJI['info']} Profilo Utente",
        color=Colors.JALISCO_GOLD.value
    )
    embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
    embed.add_field(name="Username", value=target.name, inline=True)
    embed.add_field(name="ID", value=target.id, inline=True)
    embed.add_field(name="Creato", value=target.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="Joined", value=target.joined_at.strftime("%d/%m/%Y") if target.joined_at else "N/A", inline=True)
    
    await interaction.response.send_message(embed=embed)

# ════════════════════════════════════════════════════════════════
# COMANDI - TICKET
# ════════════════════════════════════════════════════════════════

@bot.tree.command(name="ticket-apri", description="🎫 Apri un ticket")
@app_commands.describe(
    topic="Argomento ticket",
    description="Descrizione del problema"
)
async def ticket_apri(interaction: discord.Interaction, topic: str, description: str):
    """Apri un ticket di supporto"""
    
    # Crea ticket
    ticket_id = db.create_ticket(interaction.user.id, topic, description)
    
    if ticket_id:
        embed = discord.Embed(
            title=f"{EMOJI['pending']} Ticket Creato",
            description=f"Ticket ID: **{ticket_id}**",
            color=Colors.JALISCO_GOLD.value
        )
        embed.add_field(name="Argomento", value=topic, inline=False)
        embed.add_field(name="Descrizione", value=description, inline=False)
        embed.add_field(name="Status", value="🟡 In Attesa", inline=False)
        
        await interaction.response.send_message(embed=embed)
        logger.info(f"🎫 Ticket {ticket_id} creato da {interaction.user.id}")
    else:
        embed = discord.Embed(
            title=f"{EMOJI['error']} Errore",
            description="Impossibile creare il ticket",
            color=Colors.ERROR.value
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ════════════════════════════════════════════════════════════════
# COMANDI - INFO
# ════════════════════════════════════════════════════════════════

@bot.tree.command(name="help-jalisco", description="📖 Lista comandi")
async def help_jalisco(interaction: discord.Interaction):
    """Lista completa comandi disponibili"""
    
    embed = discord.Embed(
        title=f"{EMOJI['info']} JALISCO AI - Comandi Disponibili",
        description="Tutti i comandi slash disponibili",
        color=Colors.JALISCO_GOLD.value
    )
    
    # Categorie comandi
    embed.add_field(
        name="🔧 Setup",
        value="`/setup-jalisco` - Configurazione iniziale",
        inline=False
    )
    
    embed.add_field(
        name="👤 Utenti",
        value="`/user-info` - Info utente\\n`/ban` - Banna utente\\n`/unban` - Sbanna utente",
        inline=False
    )
    
    embed.add_field(
        name="🎫 Ticket",
        value="`/ticket-apri` - Apri ticket\\n`/ticket-chiudi` - Chiudi ticket",
        inline=False
    )
    
    embed.add_field(
        name="📊 Info",
        value="`/help-jalisco` - Questo comando\\n`/server-info` - Info server",
        inline=False
    )
    
    embed.set_footer(text="Usa i comandi con / per attivare il menu")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="🏓 Ping del bot")
async def ping(interaction: discord.Interaction):
    """Ping del bot"""
    
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latenza: **{latency}ms**",
        color=Colors.JALISCO_GOLD.value
    )
    
    await interaction.response.send_message(embed=embed)

# ════════════════════════════════════════════════════════════════
# ERRORI
# ════════════════════════════════════════════════════════════════

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Gestione errori comandi"""
    
    logger.error(f"❌ Errore comando: {error}")
    
    embed = discord.Embed(
        title=f"{EMOJI['error']} Errore",
        description=f"Si è verificato un errore: {str(error)[:100]}",
        color=Colors.ERROR.value
    )
    
    try:
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except:
        pass

# ════════════════════════════════════════════════════════════════
# AVVIO
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if not JALISCO_TOKEN:
        logger.error("❌ JALISCO_TOKEN non trovato in .env")
        exit(1)
    
    logger.info("🚀 Avvio JALISCO AI...")
    bot.run(JALISCO_TOKEN)
