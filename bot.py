import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from dotenv import load_dotenv

# Chargement du token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Fichiers
BALANCES_FILE = "data/balances.json"
SHOP_FILE = "data/shop.json"

# Fonctions utilitaires
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def get_balance(user_id):
    balances = load_json(BALANCES_FILE)
    return balances.get(str(user_id), 0)

def update_balance(user_id, amount):
    balances = load_json(BALANCES_FILE)
    uid = str(user_id)
    balances[uid] = balances.get(uid, 0) + amount
    save_json(BALANCES_FILE, balances)

def get_shop():
    return load_json(SHOP_FILE)

# Bot setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    print(f"{bot.user} est connecté.")

# Slash Commands

@tree.command(name="solde", description="Voir ton solde.")
async def solde(interaction: discord.Interaction):
    bal = get_balance(interaction.user.id)
    await interaction.response.send_message(f"💰 Ton solde est de {bal} AlBaidaCoins.")

@tree.command(name="magasin", description="Voir les objets en vente.")
async def magasin(interaction: discord.Interaction):
    shop = get_shop()
    items = "\n".join([f"- **{item}** : {price} AlBaidaCoins" for item, price in shop.items()])
    await interaction.response.send_message(f"🛒 Magasin:\n{items}")

@tree.command(name="acheter", description="Acheter un objet.")
@app_commands.describe(objet="Nom de l'objet à acheter")
async def acheter(interaction: discord.Interaction, objet: str):
    shop = get_shop()
    uid = interaction.user.id
    if objet not in shop:
        await interaction.response.send_message("❌ Objet introuvable.")
        return
    price = shop[objet]
    if get_balance(uid) < price:
        await interaction.response.send_message("❌ Tu n'as pas assez d'argent.")
        return
    update_balance(uid, -price)
    await interaction.response.send_message(f"✅ Tu as acheté **{objet}** pour {price} AlBaidaCoins.")

@tree.command(name="envoyer", description="Envoyer de l'argent à un autre membre.")
@app_commands.describe(membre="Personne à qui tu veux envoyer", montant="Montant à envoyer")
async def envoyer(interaction: discord.Interaction, membre: discord.Member, montant: int):
    if montant <= 0:
        await interaction.response.send_message("❌ Montant invalide.")
        return
    sender_id = interaction.user.id
    if get_balance(sender_id) < montant:
        await interaction.response.send_message("❌ Tu n'as pas assez d'argent.")
        return
    update_balance(sender_id, -montant)
    update_balance(membre.id, montant)
    await interaction.response.send_message(f"✅ Tu as envoyé {montant} AlBaidaCoins à {membre.display_name}.")

@tree.command(name="admin_ajouter", description="(Admin) Ajouter de l'argent à un membre.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(membre="Membre", montant="Montant")
async def admin_ajouter(interaction: discord.Interaction, membre: discord.Member, montant: int):
    update_balance(membre.id, montant)
    await interaction.response.send_message(f"✅ {montant} AlBaidaCoins ajoutés à {membre.display_name}.")

@tree.command(name="admin_ajouter_objet", description="(Admin) Ajouter un objet au magasin.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(nom="Nom de l'objet", prix="Prix")
async def admin_ajouter_objet(interaction: discord.Interaction, nom: str, prix: int):
    shop = get_shop()
    shop[nom] = prix
    save_json(SHOP_FILE, shop)
    await interaction.response.send_message(f"✅ Objet **{nom}** ajouté pour {prix} AlBaidaCoins.")

# Lancer le bot
bot.run(TOKEN)
