import time
import discord
from discord.ext import commands

# Configuration des intents
intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.presences = True  # Indispensable pour détecter "Wardogs"

bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionnaire pour suivre les sessions : {user_id: timestamp_debut}
active_sessions = {}

# Ton ID de salon textuel pour les rapports et UnbelievaBoat
COMMANDS_CHANNEL_ID = 1558847340738252810  


def is_playing_wardogs(member: discord.Member) -> bool:
    """Vérifie si le membre a le jeu 'Wardogs' dans ses activités en cours."""
    for activity in member.activities:
        if isinstance(activity, discord.Game) and "wardogs" in activity.name.lower():
            return True
        elif activity.name and "wardogs" in activity.name.lower():
            return True
    return False


@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user} ! Prêt pour le suivi Wardogs.")


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    current_time = time.time()
    user_id = member.id

    # CAS 1 : Le joueur REJOINT un salon vocal
    if before.channel is None and after.channel is not None:
        if is_playing_wardogs(member):
            active_sessions[user_id] = current_time

    # CAS 2 : Le joueur CHANGE de salon ou arrête de jouer à Wardogs en restant en vocal
    elif before.channel is not None and after.channel is not None:
        if user_id in active_sessions and not is_playing_wardogs(member):
            await end_session(member, current_time)

    # CAS 3 : Le joueur QUITTE totalement le vocal
    elif before.channel is not None and after.channel is None:
        if user_id in active_sessions:
            await end_session(member, current_time)


async def end_session(member: discord.Member, leave_time: float):
    user_id = member.id
    start_time = active_sessions.pop(user_id, None)
    
    if not start_time:
        return

    # Calcul de la durée en minutes
    duration_seconds = leave_time - start_time
    duration_minutes = int(duration_seconds / 60)

    # Sécurité : Si le joueur est resté moins de 2 minutes, on ignore
    if duration_minutes < 2:
        return

    # Calcul des pièces : 1 heure (60 min) = 1 pièce entière
    earned_coins = round(duration_minutes / 60.0)

    if earned_coins < 1:
        return  # Moins d'une heure jouée, pas de pièce distribuée

    channel = bot.get_channel(COMMANDS_CHANNEL_ID)
    if channel:
        # Envoi de la commande UnbelievaBoat pour créditer le joueur
        await channel.send(f"!give {member.mention} {earned_coins}")

        hours = duration_minutes // 60
        minutes = duration_minutes % 60
        
        # Embed de rapport pour la communauté
        embed = discord.Embed(
            title="🎖️ RAPPORT DE FIN DE MISSION - WARDOGS",
            color=discord.Color.gold()
        )
        embed.add_field(name="Soldat", value=member.mention, inline=False)
        embed.add_field(name="Temps de vocal sur le jeu", value=f"{hours}h {minutes}min", inline=True)
        embed.add_field(name="Gain UnbelievaBoat", value=f"🪙 `+{earned_coins} pièce(s) ajoutée(s)`", inline=True)
        
        await channel.send(embed=embed)


# Lancement du bot avec ton token
bot.run("MTU2NjQ0NjU5NzI0NjU1MDAyNg.Gq-MYS.zNwQNSZ_VGsyv0d9n5Nws_kjEL0TClxUqvchhk")