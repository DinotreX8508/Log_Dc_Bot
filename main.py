import discord
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="m!", intents=intents)

# Ayarlar
admin_role_name = "Kurucu"  # Admin rolünün ismi
log_channel_id = None  # Log kanalının ID'si

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Böyle bir komut bulunmamaktadır.")

@bot.command(name="kayit")
async def kayit(ctx, hedef_kullanici: discord.Member, *, yeni_bilgiler):
    if admin_role_name not in [role.name for role in ctx.author.roles]:
        await ctx.send("Bu komutu kullanma yetkiniz yok.")
        return

    try:
        kullanici_adi, kullanici_yasi = [x.strip() for x in yeni_bilgiler.split("|")]

        if not kullanici_yasi.isdigit():
            raise ValueError("Yaş bir sayı olmalı.")
        kullanici_yasi = int(kullanici_yasi)

        if kullanici_yasi < 13:
            raise ValueError("Yaşınız 13'ten büyük olmalı.")
    except ValueError as e:
        await ctx.send(f"Hatalı kayıt formatı: {e}")
        return

    if hedef_kullanici.display_name == f"{kullanici_adi} | {kullanici_yasi}":
        await ctx.send("Bu takma adını zaten kullanıyor.")
        return

    try:
        yeni_takma_ad = f"{kullanici_adi} | {kullanici_yasi}"
        await hedef_kullanici.edit(nick=yeni_takma_ad)

        basari_mesaji = f"{hedef_kullanici.mention}, başarıyla kaydedildi! Yeni takma adı: {yeni_takma_ad}"
        await ctx.send(basari_mesaji)

        await log_kayit_bilgisi_gonder(hedef_kullanici, kullanici_adi, kullanici_yasi)

    except discord.errors.Forbidden as e:
        print(f"Hata: {e}")
        await ctx.send("İlgili izinlere sahip değilim. Lütfen yetkilerimi kontrol edin.")


async def log_kayit_bilgisi_gonder(kullanici, kullanici_adi, kullanici_yasi):
    if log_channel_id:
        log_channel = bot.get_channel(log_channel_id)

        if log_channel:
            log_message = await get_last_log_message(log_channel)
            if log_message:
                await log_message.edit(embed=create_log_embed(kullanici, kullanici_adi, kullanici_yasi))
            else:
                log_message = await log_channel.send(embed=create_log_embed(kullanici, kullanici_adi, kullanici_yasi))

            await log_message.delete(delay=60 * 5)  # 5 dakika sonra sil
        else:
            print("Hata: Log kanalı bulunamadı.")

async def get_last_log_message(channel):
    async for message in channel.history(limit=1):
        return message

def create_log_embed(kullanici, kullanici_adi, kullanici_yasi):
    log_embed = discord.Embed(
        title="Kullanıcı Kaydedildi",
        description=f"{kullanici.mention} adlı kullanıcı başarıyla kaydedildi!",
        color=0x42f56c  # Embed rengi
    )
    log_embed.add_field(name="Kullanıcı Adı", value=kullanici_adi, inline=False)
    log_embed.add_field(name="Kullanıcı Yaşı", value=kullanici_yasi, inline=False)
    log_embed.set_thumbnail(url=kullanici.avatar_url)  # Kullanıcının profili
    log_embed.set_footer(text="Profil", icon_url="https://i.imgur.com/your_logo.png")  # Botun logosu veya simgesi
    return log_embed

@bot.command(name="log_kanal_ata")
async def log_kanal_ata(ctx, log_channel: discord.TextChannel):
    if admin_role_name not in [role.name for role in ctx.author.roles]:
        await ctx.send("Bu komutu kullanma yetkiniz yok.")
        return

    global log_channel_id
    log_channel_id = log_channel.id
    await ctx.send(f"Log kanalı başarıyla ayarlandı: {log_channel.mention}")

@bot.command(name="log")
async def log(ctx):
    if admin_role_name not in [role.name for role in ctx.author.roles]:
        await ctx.send("Bu komutu kullanma yetkiniz yok.")
        return

    if log_channel_id:
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            await ctx.send(f"Log kanalı: {log_channel.mention}")
        else:
            await ctx.send("Hata: Log kanalı bulunamadı.")
    else:
        await ctx.send("Log kanalı ayarlı değil.")

async def help(ctx):
    if admin_role_name not in [role.name for role in ctx.author.roles]:
        await ctx.send("Bu komutu kullanma yetkiniz yok.")
        return

    help_message = (
        "**Komutlar**\n"
        "1. `m!kayit @HedefKullanici YeniAd|YeniYas`: Belirli bir kullanıcının takma adını ve yaşını değiştirir.\n"
        "2. `m!log_kanal_ata #log-kanalı`: Log kanalını belirler.\n"
        "3. `m!log`: Log kanalını gösterir.\n"
        "4. `m!help`: Tüm komutları ve işlevlerini gösterir.\n"
        "5. `m!log_kullanicilari`: Komutları kullanma yetkisine sahip kullanıcıları gösterir.\n"
        "6. `m!log_gecmisi`: Son 20 kaydı gösterir."
    )
    await ctx.send(help_message)

@bot.command(name="log_kullanicilari")
async def log_kullanicilari(ctx):
    if admin_role_name not in [role.name for role in ctx.author.roles]:
        await ctx.send("Bu komutu kullanma yetkiniz yok.")
        return

    admin_users = [member.mention for member in ctx.guild.members if admin_role_name in [role.name for role in member.roles]]
    await ctx.send(f"Log komutlarını kullanma yetkisi olan kullanıcılar: {', '.join(admin_users)}")

@bot.command(name="log_gecmisi")
async def log_gecmisi(ctx):
    if admin_role_name not in [role.name for role in ctx.author.roles]:
        await ctx.send("Bu komutu kullanma yetkiniz yok.")
        return

    if log_channel_id:
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            messages = await log_channel.history(limit=20).flatten()
            for message in messages:
                await ctx.send(message.content)
        else:
            await ctx.send("Hata: Log kanalı bulunamadı.")
    else:
        await ctx.send("Log kanalı ayarlı değil.")

# Botu çalıştır
bot.run("MTE1MDUxMjE4NTY1MTUwMzEzNA.GsXN4t.gtqt6sOQp2cj2OtfKOdzD4gogvAAygZX2jYdBg")
