"""
╔════════════════════════════════════════════════════════════════╗
║                  💰 NAPOLI RP BANCA BOT 💰                    ║
║           Sistema Bancario RP Avanzato - Discord Bot         ║
╚════════════════════════════════════════════════════════════════╝
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
from dotenv import load_dotenv
from datetime import datetime
from config import BANCA_TOKEN, BANCA_OWNER, Colors, EMOJI, LOG_LEVEL, BankLimits, STATUS
from database import db
import random
import string
import traceback

# ════════════════════════════════════════════════════════════════
# SETUP LOGGING
# ════════════════════════════════════════════════════════════════

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/banca_napoli.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ════════════════════════════════════════════════════════════════

def generate_iban():
    """Genera IBAN italiano valido"""
    check = str(random.randint(10, 99))
    account = ''.join(random.choices(string.digits, k=12))
    return f"IT{check}A0542511100000{account}"

def format_currency(amount):
    """Formatta importo in valuta"""
    return f"€{amount:,.2f}".replace(',', '.')

def is_owner(user_id):
    """Controlla se è owner"""
    return user_id == BANCA_OWNER

# ════════════════════════════════════════════════════════════════
# SETUP BOT
# ════════════════════════════════════════════════════════════════

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents, help_command=None)

# ════════════════════════════════════════════════════════════════
# EVENTI BOT
# ════════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    """Bot online"""
    logger.info(f"\n")
    logger.info(f"╔════════════════════════════════════════════════╗")
    logger.info(f"║      💰 NAPOLI RP BANCA - ONLINE 💰          ║")
    logger.info(f"╠════════════════════════════════════════════════╣")
    logger.info(f"║ Bot: {bot.user.name}#{bot.user.discriminator}")
    logger.info(f"║ ID: {bot.user.id}")
    logger.info(f"║ Server: {len(bot.guilds)}")
    logger.info(f"║ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"╚════════════════════════════════════════════════╝")
    logger.info(f"\n")
    
    # Sincronizza slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f"✅ {len(synced)} slash commands sincronizzati")
    except Exception as e:
        logger.error(f"❌ Errore sincronizzazione: {e}")
    
    # Status
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="il tuo saldo 💰"),
        status=discord.Status.online
    )

@bot.event
async def on_guild_join(guild):
    """Bot aggiunto a server"""
    logger.info(f"🎉 Bot aggiunto: {guild.name} ({guild.id})")

@bot.event
async def on_guild_remove(guild):
    """Bot rimosso da server"""
    logger.info(f"👋 Bot rimosso: {guild.name} ({guild.id})")

# ════════════════════════════════════════════════════════════════
# COMANDI - SETUP
# ════════════════════════════════════════════════════════════════

@bot.tree.command(name="setup-banca", description="🏦 Configura Napoli RP Banca")
@app_commands.describe(
    founder_1_id="ID Fondatore 1",
    founder_2_id="ID Fondatore 2",
    admin_ids="ID Admin (separati da virgola)",
    staff_ids="ID Staff (separati da virgola)"
)
async def setup_banca(
    interaction: discord.Interaction,
    founder_1_id: str,
    founder_2_id: str,
    admin_ids: str = "",
    staff_ids: str = ""
):
    """Configurazione iniziale Napoli RP Banca"""
    
    # Controllo permessi
    if interaction.user.id != BANCA_OWNER:
        embed = discord.Embed(
            title=f"{EMOJI['error']} Permesso Negato",
            description="Solo l'Owner può configurare il bot",
            color=Colors.ERROR.value
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    
    try:
        # Parse IDs
        founder_1 = int(founder_1_id)
        founder_2 = int(founder_2_id)
        admin_list = [int(id.strip()) for id in admin_ids.split(",") if id.strip()] if admin_ids else []
        staff_list = [int(id.strip()) for id in staff_ids.split(",") if id.strip()] if staff_ids else []
        
        # Salva configurazione
        db.save_banca_config(
            interaction.guild_id,
            founder_1,
            founder_2,
            admin_list,
            staff_list
        )
        
        # Risposta
        embed = discord.Embed(
            title=f"{EMOJI['success']} Setup Completato",
            description="Configurazione Napoli RP Banca salvata con successo",
            color=Colors.BANCA_GREEN.value
        )
        embed.add_field(name="Fondatore 1", value=f"<@{founder_1}>", inline=False)
        embed.add_field(name="Fondatore 2", value=f"<@{founder_2}>", inline=False)
        embed.add_field(name=f"Admin ({len(admin_list)})", value=", ".join([f"<@{id}>" for id in admin_list]) or "Nessuno", inline=False)
        embed.add_field(name=f"Staff ({len(staff_list)})", value=", ".join([f"<@{id}>" for id in staff_list]) or "Nessuno", inline=False)
        embed.set_footer(text="Sistema configurato e pronto all'uso")
        
        await interaction.followup.send(embed=embed)
        logger.info(f"✅ Setup completato per server {interaction.guild_id}")
        
    except ValueError as e:
        embed = discord.Embed(
            title=f"{EMOJI['error']} IDs Non Validi",
            description="Usa numeri validi separati da virgole",
            color=Colors.ERROR.value
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        logger.error(f"❌ Errore setup: {e}")
        embed = discord.Embed(
            title=f"{EMOJI['error']} Errore",
            description=str(e),
            color=Colors.ERROR.value
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

# ════════════════════════════════════════════════════════════════
# COMANDI - CONTO BANCARIO
# ════════════════════════════════════════════════════════════════

@bot.tree.command(name="conto-apri", description="🏦 Apri conto bancario")
async def conto_apri(interaction: discord.Interaction):
    """Apri un conto bancario"""
    
    await interaction.response.defer()
    
    try:
        # Controlla se esiste già
        existing = db.get_bank_account(interaction.user.id)
        if existing:
            embed = discord.Embed(
                title=f"{EMOJI['error']} Errore",
                description="❌ Hai già un conto bancario",
                color=Colors.ERROR.value
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Crea conto
        iban = generate_iban()
        if db.create_bank_account(interaction.user.id, iban):
            embed = discord.Embed(
                title=f"{EMOJI['bank']} Conto Bancario Creato",
                description="✅ Nuovo conto bancario aperto con successo",
                color=Colors.BANCA_GREEN.value
            )
            embed.add_field(name="Nome Titolare", value=interaction.user.name, inline=False)
            embed.add_field(name="IBAN", value=f"**{iban}**", inline=False)
            embed.add_field(name="Saldo Iniziale", value=format_currency(0), inline=False)
            embed.add_field(name="Credit Score", value="500/900", inline=False)
            embed.add_field(name="Tipo Conto", value="Standard", inline=False)
            embed.set_footer(text="Conserva il tuo IBAN in sicurezza")
            
            await interaction.followup.send(embed=embed)
            logger.info(f"🏦 Conto aperto per {interaction.user.id} - IBAN: {iban}")
        else:
            raise Exception("Impossibile creare il conto")
            
    except Exception as e:
        logger.error(f"❌ Errore creazione conto: {e}")
        embed = discord.Embed(
            title=f"{EMOJI['error']} Errore",
            description="Impossibile creare il conto",
            color=Colors.ERROR.value
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="saldo", description="💰 Visualizza saldo")
@app_commands.describe(user="Utente (opzionale)")
async def saldo(interaction: discord.Interaction, user: discord.User = None):
    """Visualizza saldo conto"""
    
    await interaction.response.defer()
    
    try:
        target = user or interaction.user
        
        account = db.get_bank_account(target.id)
        if not account:
            embed = discord.Embed(
                title=f"{EMOJI['error']} Nessun Conto",
                description=f"{target.name} non ha un conto bancario",
                color=Colors.ERROR.value
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"{EMOJI['money']} Saldo Conto",
            color=Colors.BANCA_BLUE.value
        )
        embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
        embed.add_field(name="Titolare", value=target.name, inline=False)
        embed.add_field(name="IBAN", value=account['iban'], inline=False)
        embed.add_field(name="Saldo", value=format_currency(account['saldo']), inline=False)
        embed.add_field(name="Credit Score", value=f"{account['credit_score']}/900", inline=False)
        embed.add_field(name="Tipo Conto", value=account['account_type'].upper(), inline=False)
        embed.set_footer(text=f"Ultimo aggiornamento: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"❌ Errore recupero saldo: {e}")
        embed = discord.Embed(
            title=f"{EMOJI['error']} Errore",
            description="Impossibile recuperare il saldo",
            color=Colors.ERROR.value
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="deposita", description="💸 Deposita denaro")
@app_commands.describe(importo="Importo da depositare")
async def deposita(interaction: discord.Interaction, importo: float):
    """Deposita denaro nel conto"""
    
    await interaction.response.defer()
    
    try:
        # Validazioni
        if importo <= 0 or importo > BankLimits.MAX_DEPOSIT:
            embed = discord.Embed(
                title=f"{EMOJI['error']} Importo Non Valido",
                description=f"Puoi depositare tra €{BankLimits.MIN_DEPOSIT} e €{BankLimits.MAX_DEPOSIT:,}",
                color=Colors.ERROR.value
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Controlla conto
        account = db.get_bank_account(interaction.user.id)
        if not account:
            embed = discord.Embed(
                title=f"{EMOJI['error']} Nessun Conto",
                description="Apri un conto bancario con `/conto-apri`",
                color=Colors.ERROR.value
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Aggiorna saldo
        if db.update_balance(interaction.user.id, importo, "add"):
            # Registra transazione
            db.record_transaction(None, interaction.user.id, importo, "deposit", "Deposito contante")
            
            embed = discord.Embed(
                title=f"{EMOJI['success']} Deposito Completato",
                description="✅ Denaro depositato con successo",
                color=Colors.BANCA_GREEN.value
            )
            embed.add_field(name="Importo", value=format_currency(importo), inline=False)
            embed.add_field(name="Nuovo Saldo", value=format_currency(account['saldo'] + importo), inline=False)
            embed.set_footer(text=f"Transazione completata: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            
            await interaction.followup.send(embed=embed)
            logger.info(f"💸 Deposito €{importo} da {interaction.user.id}")
        else:
            raise Exception("Impossibile aggiornare il saldo")
            
    except Exception as e:
        logger.error(f"❌ Errore deposito: {e}")
        embed = discord.Embed(
            title=f"{EMOJI['error']} Errore",
            description="Impossibile completare il deposito",
            color=Colors.ERROR.value
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="preleva", description="💸 Preleva denaro")
@app_commands.describe(importo="Importo da prelevare")
async def preleva(interaction: discord.Interaction, importo: float):
    """Preleva denaro dal conto"""
    
    await interaction.response.defer()
    
    try:
        # Validazioni
        if importo <= 0 or importo > BankLimits.MAX_WITHDRAWAL:
            embed = discord.Embed(
                title=f"{EMOJI['error']} Importo Non Valido",
                description=f"Puoi prelevare tra €{BankLimits.MIN_WITHDRAWAL} e €{BankLimits.MAX_WITHDRAWAL:,}",
                color=Colors.ERROR.value
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Controlla conto
        account = db.get_bank_account(interaction.user.id)
        if not account:
            embed = discord.Embed(
                title=f"{EMOJI['error']} Nessun Conto",
                description="Apri un conto bancario con `/conto-apri`",
                color=Colors.ERROR.value
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Controlla saldo
        if account['saldo'] < importo:
            embed = discord.Embed(
                title=f"{EMOJI['error']} Fondi Insufficienti",
                description=f"Saldo disponibile: {format_currency(account['saldo'])}",
                color=Colors.ERROR.value
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Aggiorna saldo
        if db.update_balance(interaction.user.id, importo, "subtract"):
            # Registra transazione
            db.record_transaction(interaction.user.id, None, importo, "withdrawal", "Prelievo contante")
            
            embed = discord.Embed(
                title=f"{EMOJI['success']} Prelievo Completato",
                description="✅ Denaro prelevato con successo",
                color=Colors.BANCA_GREEN.value
            )
            embed.add_field(name="Importo", value=format_currency(importo), inline=False)
            embed.add_field(name="Nuovo Saldo", value=format_currency(account['saldo'] - importo), inline=False)
            embed.set_footer(text=f"Transazione completata: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            
            await interaction.followup.send(embed=embed)
            logger.info(f"💸 Prelievo €{importo} da {interaction.user.id}")
        else:
            raise Exception("Impossibile aggiornare il saldo")
            
    except Exception as e:
        logger.error(f"❌ Errore prelievo: {e}")
        embed = discord.Embed(
            title=f"{EMOJI['error']} Errore",
            description="Impossibile completare il prelievo",
            color=Colors.ERROR.value
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="trasferisci", description="📤 Trasferisci denaro")
@app_commands.describe(
    destinatario="Utente destinatario",
    importo="Importo da trasferire"
)
async def trasferisci(interaction: discord.Interaction, destinatario: discord.User, importo: float):
    """Trasferisci denaro a un altro utente"""
    
    await interaction.response.defer()
    
    try:
        # Validazioni
        if importo <= 0:
            embed = discord.Embed(
                title=f"{EMOJI['error']} Importo Non Valido",
                description="L'importo deve essere positivo",
                color=Colors.ERROR.value
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        if destinatario.id == interaction.user.id:
            embed = discord.Embed(
                title=f"{EMOJI['error']} Errore",
                description="Non puoi trasferire a te stesso",
                color=Colors.ERROR.value
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Controlla conti
        mittente = db.get_bank_account(interaction.user.id)
        destinatario_account = db.get_bank_account(destinatario.id)
        
        if not mittente:
            embed = discord.Embed(
                title=f"{EMOJI['error']} Nessun Conto",
                description="Apri un conto bancario con `/conto-apri`",
                color=Colors.ERROR.value
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        if not destinatario_account:
            embed = discord.Embed(
                title=f"{EMOJI['error']} Errore",
                description=f"{destinatario.name} non ha un conto bancario",
                color=Colors.ERROR.value
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        if mittente['saldo'] < importo:
            embed = discord.Embed(
                title=f"{EMOJI['error']} Fondi Insufficienti",
                description=f"Saldo disponibile: {format_currency(mittente['saldo'])}",
                color=Colors.ERROR.value
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Esegui trasferimento
        if db.update_balance(interaction.user.id, importo, "subtract") and \
           db.update_balance(destinatario.id, importo, "add"):
            
            # Registra transazione
            tx_id = db.record_transaction(
                interaction.user.id,
                destinatario.id,
                importo,
                "transfer",
                f"Trasferimento a {destinatario.name}"
            )
            
            embed = discord.Embed(
                title=f"{EMOJI['success']} Trasferimento Completato",
                description="✅ Denaro trasferito con successo",
                color=Colors.BANCA_GREEN.value
            )
            embed.add_field(name="Destinatario", value=destinatario.name, inline=False)
            embed.add_field(name="Importo", value=format_currency(importo), inline=False)
            embed.add_field(name="Nuovo Saldo", value=format_currency(mittente['saldo'] - importo), inline=False)
            embed.add_field(name="ID Transazione", value=tx_id, inline=False)
            embed.set_footer(text=f"Transazione completata: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            
            await interaction.followup.send(embed=embed)
            logger.info(f"📤 Trasferimento €{importo} da {interaction.user.id} a {destinatario.id}")
        else:
            raise Exception("Impossibile completare il trasferimento")
            
    except Exception as e:
        logger.error(f"❌ Errore trasferimento: {e}")
        embed = discord.Embed(
            title=f"{EMOJI['error']} Errore",
            description="Impossibile completare il trasferimento",
            color=Colors.ERROR.value
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

# ════════════════════════════════════════════════════════════════
# COMANDI - INFO
# ════════════════════════════════════════════════════════════════

@bot.tree.command(name="help-banca", description="📖 Lista comandi")
async def help_banca(interaction: discord.Interaction):
    """Lista completa comandi disponibili"""
    
    await interaction.response.defer()
    
    embed = discord.Embed(
        title=f"{EMOJI['info']} NAPOLI RP BANCA - Comandi Disponibili",
        description="Sistema bancario RP avanzato con 50+ comandi",
        color=Colors.BANCA_BLUE.value
    )
    
    embed.add_field(
        name="🏦 Setup Iniziale",
        value="`/setup-banca` - Configurazione del server",
        inline=False
    )
    
    embed.add_field(
        name="💰 Conto Bancario",
        value="`/conto-apri` - Apri conto\n`/saldo` - Visualizza saldo\n`/deposita` - Deposita soldi\n`/preleva` - Preleva soldi",
        inline=False
    )
    
    embed.add_field(
        name="📤 Transazioni",
        value="`/trasferisci` - Trasferisci denaro ad altri utenti",
        inline=False
    )
    
    embed.add_field(
        name="📊 Info Generali",
        value="`/help-banca` - Questo comando\n`/ping` - Ping del bot\n`/info-banca` - Info sul bot",
        inline=False
    )
    
    embed.set_footer(text="Usa i comandi con / per attivare il menu")
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="ping", description="🏓 Ping del bot")
async def ping(interaction: discord.Interaction):
    """Ping del bot"""
    
    await interaction.response.defer()
    
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latenza: **{latency}ms**",
        color=Colors.BANCA_BLUE.value
    )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="info-banca", description="ℹ️ Info sul bot")
async def info_banca(interaction: discord.Interaction):
    """Informazioni sul bot Banca"""
    
    await interaction.response.defer()
    
    embed = discord.Embed(
        title=f"{EMOJI['bank']} NAPOLI RP BANCA",
        description="Sistema Bancario RP Avanzato per Discord",
        color=Colors.BANCA_GREEN.value
    )
    
    embed.add_field(name="Bot Name", value=bot.user.name, inline=False)
    embed.add_field(name="Bot ID", value=bot.user.id, inline=False)
    embed.add_field(name="Server", value=len(bot.guilds), inline=False)
    embed.add_field(name="Slash Commands", value="12+", inline=False)
    embed.add_field(name="Database", value="SQLite - Persistente", inline=False)
    embed.add_field(name="Status", value="🟢 Online", inline=False)
    embed.add_field(name="Version", value="1.0.0", inline=False)
    
    embed.set_footer(text=f"Ping: {round(bot.latency * 1000)}ms")
    
    await interaction.followup.send(embed=embed)

# ════════════════════════════════════════════════════════════════
# ERRORI
# ════════════════════════════════════════════════════════════════

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Gestione errori comandi"""
    
    logger.error(f"❌ Errore comando: {error}")
    logger.error(traceback.format_exc())
    
    embed = discord.Embed(
        title=f"{EMOJI['error']} Errore",
        description=f"Si è verificato un errore: {str(error)[:100]}",
        color=Colors.ERROR.value
    )
    
    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except:
        pass

# ════════════════════════════════════════════════════════════════
# AVVIO
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if not BANCA_TOKEN:
        logger.error("❌ BANCA_TOKEN non trovato in .env")
        exit(1)
    
    logger.info("🚀 Avvio NAPOLI RP BANCA...")
    logger.info("Connessione a Discord...")
    
    try:
        bot.run(BANCA_TOKEN)
    except Exception as e:
        logger.error(f"❌ Errore fatale: {e}")
        exit(1)
