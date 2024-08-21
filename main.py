import os
import nextcord, datetime, json, re, httpx, certifi
from nextcord.ext import commands

from myserver import server_on

config = json.load(open('./config.json', 'r', encoding='utf-8'))

bot = commands.Bot(command_prefix='nyx!',
                   help_command=None,
                   intents=nextcord.Intents.all(),
                   strip_after_prefix=True,
                   case_insensitive=True)


class topupModal(nextcord.ui.Modal):

    def __init__(self):
        super().__init__(title='เติมเงิน',
                         timeout=None,
                         custom_id='topup-modal')
        self.link = nextcord.ui.TextInput(
            label='กรุณาไส่ซองอังเปาค้าบ',
            placeholder=
            'https://gift.truemoney.com/campaign/?v=xxxxxxxxxxxxxxx',
            style=nextcord.TextInputStyle.short,
            required=True)
        self.add_item(self.link)

    async def callback(self, interaction: nextcord.Interaction):
        link = str(self.link.value).replace(' ', '')
        message = await interaction.response.send_message(content='checking.',
                                                          ephemeral=True)
        if re.match(
                r'https:\/\/gift\.truemoney\.com\/campaign\/\?v=+[a-zA-Z0-9]{18}',
                link):
            voucher_hash = link.split('?v=')[1]
            response = httpx.post(
                url=
                f'https://gift.truemoney.com/campaign/vouchers/{voucher_hash}/redeem',
                headers={
                    'User-Agent':
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/8a0.0.3987.149 Safari/537.36'
                },
                json={
                    'mobile': config['phoneNumber'],
                    'voucher_hash': f'{voucher_hash}'
                },
                verify=certifi.where(),
            )
            if (response.status_code == 200
                    and response.json()['status']['code'] == 'SUCCESS'):
                data = response.json()
                amount = int(float(data['data']['my_ticket']['amount_baht']))
                userJSON = json.load(
                    open('./database/users.json', 'r', encoding='utf-8'))
                if (str(interaction.user.id) not in userJSON):
                    userJSON[str(interaction.user.id)] = {
                        "userId":
                        interaction.user.id,
                        "point":
                        amount,
                        "all-point":
                        amount,
                        "transaction": [{
                            "topup": {
                                "url": link,
                                "amount": amount,
                                "time": str(datetime.datetime.now())
                            }
                        }]
                    }
                else:
                    userJSON[str(interaction.user.id)]['point'] += amount
                    userJSON[str(interaction.user.id)]['all-point'] += amount
                    userJSON[str(interaction.user.id)]['transaction'].append({
                        "topup": {
                            "url": link,
                            "amount": amount,
                            "time": str(datetime.datetime.now())
                        }
                    })
                json.dump(userJSON,
                          open('./database/users.json', 'w', encoding='utf-8'),
                          indent=4,
                          ensure_ascii=False)
                embed = nextcord.Embed(
                    description=
                    '<a:910538890123837470:1268107405405978655>﹒**เติมเงินสำเร็จแล้วคับ**',
                    color=nextcord.Color.green())
            else:
                embed = nextcord.Embed(
                    description=
                    '<a:1212049425128751214:1258640060710912010>﹒**เติมเงินไม่สำเร็จ:<**',
                    color=nextcord.Color.red())
        else:
            embed = nextcord.Embed(
                description=
                '<a:1212049425128751214:1258640060710912010>﹒**รูปแบบลิ้งค์ไม่ถูกต้องครับ:<**',
                color=nextcord.Color.red())
        await message.edit(content=None, embed=embed)


class sellroleView(nextcord.ui.View):

    def __init__(self, message: nextcord.Message, value: str):
        super().__init__(timeout=None)
        self.message = message
        self.value = value

    @nextcord.ui.button(label='✅﹒ยืนยัน',
                        custom_id='already',
                        style=nextcord.ButtonStyle.primary,
                        row=1)
    async def already(self, button: nextcord.Button,
                      interaction: nextcord.Interaction):
        roleJSON = json.load(
            open('./database/roles.json', 'r', encoding='utf-8'))
        userJSON = json.load(
            open('./database/users.json', 'r', encoding='utf-8'))
        if (str(interaction.user.id) not in userJSON):
            embed = nextcord.Embed(
                description=
                '<:922922440454209606:1273121697888731167>﹒เติมเงินเพื่อเปิดบัญชีครับ',
                color=nextcord.Color.red())
        else:
            if (userJSON[str(interaction.user.id)]['point']
                    >= roleJSON[self.value]['price']):
                userJSON[str(interaction.user.id)]['point'] -= roleJSON[
                    self.value]['price']
                userJSON[str(interaction.user.id)]['transaction'].append({
                    "payment": {
                        "roleId": self.value,
                        "time": str(datetime.datetime.now())
                    }
                })
                json.dump(userJSON,
                          open('./database/users.json', 'w', encoding='utf-8'),
                          indent=4,
                          ensure_ascii=False)
                if ('package' in self.value):
                    for roleId in roleJSON[self.value]['roleIds']:
                        try:
                            await interaction.user.add_roles(
                                nextcord.utils.get(
                                    interaction.user.guild.roles, id=roleId))
                        except:
                            pass
                    channelLog = bot.get_channel(config['channelLog'])
                    if (channelLog):
                        embed = nextcord.Embed()
                        if interaction.user.avatar == None:
                            embed.set_thumbnail(url=None)
                        else:
                            embed.set_thumbnail(
                                url=interaction.user.avatar.url)
                        embed.title = '»——————⋆◦　ประวัติการซื้อยศ　◦⋆——————«'
                        embed.description = f'''
                       ﹒𝐔𝐬𝐞𝐫 : **<@{interaction.user.id}>**
                       ﹒𝐍𝐚𝐦𝐞 : **{interaction.user.name}**
                       ﹒𝐏𝐫𝐢𝐜𝐞 : **{roleJSON[self.value]['price']}**𝐓𝐇𝐁
                       ﹒𝐆𝐞𝐭𝐑𝐨𝐥𝐞 : <@&{roleJSON[self.value]["roleId"]}>
                       ୨⎯"　𝐈𝐍𝐌𝟏𝟖.　"⎯୧'''
                        embed.color = nextcord.Color.blue()
                        embed.set_footer(
                            text='INM18. COMMUNITY',
                            icon_url=
                            'https://cdn.discordapp.com/attachments/1228666001940418604/1275194176564363264/20240820_034441.png?ex=66c5009f&is=66c3af1f&hm=0710ed331cd12858755589373a5662047319de296810399c06e9bc1f62c55425&'
                        )
                        await channelLog.send(embed=embed)
                    embed = nextcord.Embed(
                        description=
                        f'✨﹒ซื้อยศสำเร็จ คุณได้รับ <@&{roleJSON[self.value]["name"]}>',
                        color=nextcord.Color.green())
                else:
                    channelLog = bot.get_channel(config['channelLog'])
                    if (channelLog):
                        embed = nextcord.Embed()
                        if interaction.user.avatar == None:
                            embed.set_thumbnail(url=None)
                        else:
                            embed.set_thumbnail(
                                url=interaction.user.avatar.url)
                        embed.title = '——————⋆◦　ประวัติการซื้อยศ　◦⋆——————'
                        embed.description = f'''
                       ﹒𝐔𝐬𝐞𝐫 : **<@{interaction.user.id}>**
                       ﹒𝐍𝐚𝐦𝐞 : **{interaction.user.name}**
                       ﹒𝐏𝐫𝐢𝐜𝐞 : **{roleJSON[self.value]['price']}**𝐓𝐇𝐁
                       ﹒𝐆𝐞𝐭𝐑𝐨𝐥𝐞 : <@&{roleJSON[self.value]["roleId"]}>
                       ——————⋆◦　𝐈𝐍𝐌𝟏𝟖.　◦⋆——————<'''
                        embed.color = nextcord.Color.blue()
                        embed.set_footer(
                            text='INM18. COMMUNITY',
                            icon_url=
                            'https://cdn.discordapp.com/attachments/1228666001940418604/1275194176564363264/20240820_034441.png?ex=66c5009f&is=66c3af1f&hm=0710ed331cd12858755589373a5662047319de296810399c06e9bc1f62c55425&'
                        )
                        await channelLog.send(embed=embed)
                    embed = nextcord.Embed(
                        description=
                        f'<a:1063444682752917595:1272257413231153243>﹒ยินดีด้วยซื้อยศซื้อ สำเร็จ <@&{roleJSON[self.value]["roleId"]}>',
                        color=nextcord.Color.green())
                    role = nextcord.utils.get(
                        interaction.user.guild.roles,
                        id=roleJSON[self.value]['roleId'])
                    await interaction.user.add_roles(role)
            else:
                embed = nextcord.Embed(
                    description=
                    f'<a:1238582383729573968:1258640114893066282>﹒เงินของคุณไม่เพียงพอครับ ขาดอีก ({roleJSON[self.value]["price"] - userJSON[str(interaction.user.id)]["point"]})',
                    color=nextcord.Color.red())
        return await self.message.edit(embed=embed, view=None, content=None)

    @nextcord.ui.button(label='❌﹒ยกเลิก',
                        custom_id='cancel',
                        style=nextcord.ButtonStyle.red,
                        row=1)
    async def cancel(self, button: nextcord.Button,
                     interaction: nextcord.Interaction):
        return await self.message.edit(
            content='<a:910538890123837470:1268107405405978655>﹒ยกเลิกสำเร็จ',
            embed=None,
            view=None)


class sellroleSelect(nextcord.ui.Select):

    def __init__(self):
        options = []
        roleJSON = json.load(
            open('./database/roles.json', 'r', encoding='utf-8'))
        for role in roleJSON:
            options.append(
                nextcord.SelectOption(
                    label=roleJSON[role]['name'],
                    description=roleJSON[role]['description'],
                    value=role,
                    emoji=roleJSON[role]['emoji']))
        super().__init__(custom_id='select-role',
                         placeholder='[ เลือกยศที่คุณต้องการซื้อเลยครับ ]',
                         min_values=1,
                         max_values=1,
                         options=options,
                         row=0)

    async def callback(self, interaction: nextcord.Interaction):
        message = await interaction.response.send_message(
            content='[SELECT] กำลังตรวจสอบครับผม', ephemeral=True)
        selected = self.values[0]
        if ('package' in selected):
            roleJSON = json.load(
                open('./database/roles.json', 'r', encoding='utf-8'))
            embed = nextcord.Embed()
            embed.description = f'''
E {roleJSON[selected]['name']}**
'''
            await message.edit(content=None,
                               embed=embed,
                               view=sellroleView(message=message,
                                                 value=selected))
        else:
            roleJSON = json.load(
                open('./database/roles.json', 'r', encoding='utf-8'))
            embed = nextcord.Embed()
            embed.title = '୨⎯"　ยืนยันการสั่งซื้อยศ　"⎯୧'
            embed.description = f'''
           \n คุณแน่ใจหรอคะที่จะซื้อยศ <@&{roleJSON[selected]['roleId']}> \n
ถ้าแน่ใจกด **ยืนยัน** ถ้าไม่แน่ใจกด **ยกเลิก**
'''
            embed.color = nextcord.Color.blue()
            embed.set_thumbnail(
                url=
                'https://cdn.discordapp.com/attachments/1228666001940418604/1275194176564363264/20240820_034441.png?ex=66c5009f&is=66c3af1f&hm=0710ed331cd12858755589373a5662047319de296810399c06e9bc1f62c55425&'
            )
            await message.edit(content=None,
                               embed=embed,
                               view=sellroleView(message=message,
                                                 value=selected))


class setupView(nextcord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(sellroleSelect())
        self.link_button = nextcord.ui.Button(
            style=nextcord.ButtonStyle.link,
            label="𝐈𝐍𝐌𝟏𝟖",
            url='https://discord.gg/inm18community')
        self.add_item(self.link_button)

    @nextcord.ui.button(label='💳﹒เติมเงิน',
                        custom_id='topup',
                        style=nextcord.ButtonStyle.primary,
                        row=1)
    async def topup(self, button: nextcord.Button,
                    interaction: nextcord.Interaction):
        await interaction.response.send_modal(topupModal())

    @nextcord.ui.button(label='🧧﹒เช็คเงิน',
                        custom_id='balance',
                        style=nextcord.ButtonStyle.primary,
                        row=1)
    async def balance(self, button: nextcord.Button,
                      interaction: nextcord.Interaction):
        userJSON = json.load(
            open('./database/users.json', 'r', encoding='utf-8'))
        if (str(interaction.user.id) not in userJSON):
            embed = nextcord.Embed(
                description=
                '<:922922440454209606:1273121697888731167>﹒เติมเงินเพื่อเปิดบัญชีน๊าาา',
                color=nextcord.Color.red())
        else:
            embed = nextcord.Embed(
                description=
                f'┏━━━━━━━━━━━━━━━┓\n\n💳﹒ยอดเงินคงเหลือ **__{userJSON[str(interaction.user.id)]["point"]}__** บาท\n\n┗━━━━━━━━━━━━━━━┛',
                color=nextcord.Color.green())
        return await interaction.response.send_message(embed=embed,
                                                       ephemeral=True)


@bot.event
async def on_ready():
    bot.add_view(setupView())
    print(f'LOGIN AS {bot.user}')


@bot.slash_command(name='setup',
                   description='setup',
                   guild_ids=[config['serverId']])
async def setup(interaction: nextcord.Interaction):
    if (interaction.user.id not in config['ownerIds']):
        return await interaction.response.send_message(
            content='[ERROR] No Permission For Use This Command.',
            ephemeral=True)
    embed = nextcord.Embed()
    embed.title = '୨⎯"       𝐈𝐍𝐌𝟏𝟖.       "⎯୧'
    embed.description = f'''

  ˗ˏˋ บอทซื้อยศ 24 ชั่วโมง ´ˎ˗

 <a:3381bellbag:1275445679980019853>.꒰ °เติมเงินด้วยอังเปา ꒱
 <a:timeout:1262615916693291080>.꒰ °ออโต้ 24 ชั่วโมง! ꒱
 <a:7223rainbow:1274604685596295189>.꒰ °ซื้อเสร็จยศเข้าตัว ꒱
 <a:910538341496270849:1268107378440667169>.꒰ °เติมเงินเพื่อเปิดบัญชี ꒱
'''
    embed.color = nextcord.Color.blue()
    embed.set_image(
        url=
        'https://cdn.discordapp.com/attachments/1228666001940418604/1275207251488931941/Cute_Blue_Girl_Gamer_Twitch_Banner.png?ex=66c50ccc&is=66c3bb4c&hm=7b3488cbdd46bef732e8f114f54aa2b31b67aefd721aef6a678c252414d0dec2&'
    )
    embed.set_thumbnail(
        url=
        'https://cdn.discordapp.com/attachments/1228666001940418604/1275194176564363264/20240820_034441.png?ex=66c5009f&is=66c3af1f&hm=0710ed331cd12858755589373a5662047319de296810399c06e9bc1f62c55425&'
    )
    await interaction.channel.send(embed=embed, view=setupView())
    await interaction.response.send_message(content='[SUCCESS] Done.',
                                            ephemeral=True)

server_on()

bot.run(os.getenv('TOKEN'))
