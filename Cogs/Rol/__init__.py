import csv
from pathlib import Path
import discord
from discord.ext import commands
import d20

class PaginationView(discord.ui.View):
    current_page : int = 0

    async def send(self, ctx):
        self.message = await ctx.send(view=self)
        await self.handle_change_page()

    def create_embed(self):
        pass

    def update_buttons(self):
        self.status_button.label = f"{self.current_page+1}/{self.page_count}"
        if self.current_page == 0:
            self.prev_button.disabled = True
            self.prev_button.style = discord.ButtonStyle.gray
            self.first_page_button.disabled = True
            self.first_page_button.style = discord.ButtonStyle.gray
        else:
            self.first_page_button.disabled = False
            self.first_page_button.style = discord.ButtonStyle.green
            self.prev_button.disabled = False
            self.prev_button.style = discord.ButtonStyle.primary

        if self.current_page == self.page_count - 1:
            self.next_button.disabled = True
            self.next_button.style = discord.ButtonStyle.gray
            self.last_page_button.disabled = True
            self.last_page_button.style = discord.ButtonStyle.gray
        else:
            self.next_button.disabled = False
            self.next_button.style = discord.ButtonStyle.primary
            self.last_page_button.disabled = False
            self.last_page_button.style = discord.ButtonStyle.green

    async def handle_change_page(self):
        self.update_buttons()
        await self.update_message()
    
    async def update_message(self):
        await self.message.edit(embed=self.create_embed(), view=self)

    @discord.ui.button(label="|<",
                       custom_id="btn_first",
                       style=discord.ButtonStyle.green)
    async def first_page_button(self, interaction:discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = 0
        await self.handle_change_page()

    @discord.ui.button(label="<",
                       custom_id="btn_prev",
                       style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction:discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = max(0, self.current_page-1)
        await self.handle_change_page()

    @discord.ui.button(label="-",
                       custom_id="btn_status",
                       style=discord.ButtonStyle.primary, disabled=True)
    async def status_button(self, interaction:discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

    @discord.ui.button(label=">",
                       custom_id="btn_next",
                       style=discord.ButtonStyle.primary)
    async def next_button(self, interaction:discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = min(self.page_count - 1, self.current_page + 1)
        await self.handle_change_page()

    @discord.ui.button(label=">|",
                       custom_id="btn_last",
                       style=discord.ButtonStyle.green)
    async def last_page_button(self, interaction:discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = self.page_count - 1
        await self.handle_change_page()

class SpellInfoView(PaginationView):
    CHAR_LIMIT = 1024
    def __init__(self, spell_name:str, spell_data, color:discord.Color):
        super().__init__()
        self.embed_data = discord.Embed(title=spell_name,
                                        description=f"{spell_data[2]} Lvl {spell_data[0]}",
                             color=color)
        
        # cast_time, reach, components, duration, description, src
        self.embed_data.add_field(name=spell_data[-1], value="", inline=False) # Source
        self.embed_data.add_field(name=spell_data[3], value="", inline=True) # cast time
        self.embed_data.add_field(name=spell_data[4], value="", inline=True) # reach
        self.embed_data.add_field(name=spell_data[6], value="", inline=True) #duration

        desc = (spell_data[7].replace('<strong>','**').replace('</strong>','**').replace('<BR>','\n')
                .replace('</i>','*').replace('<i>','*')
                )
        
        start_desc_idx = 0
        material_comp = ""
        if desc[0] == '(' and 'M' in spell_data[5]:
            start_desc_idx = desc.index(')')+1
            material_comp = desc[:start_desc_idx]
        self.embed_data.add_field(name=spell_data[5]+material_comp, value="", inline=True) #components

        self.data_description = desc[start_desc_idx:]
        nchar = len(self.data_description) 
        self.page_count = nchar//self.CHAR_LIMIT + int((nchar%self.CHAR_LIMIT) > 0)
    
    def create_embed(self):
        data = self.embed_data.copy()
        desc = self.data_description[self.current_page*self.CHAR_LIMIT:(self.current_page+1)*self.CHAR_LIMIT]
        data.set_field_at(-1, name="", value=desc, inline=False)
        return data

class SpellListView(PaginationView):
    SPELL_LIMIT = 10
    def __init__(self, spells, color:discord.Color):
        super().__init__()
        self.spells = [[sp[1], sp[-1]] for sp in spells]
        nspells = len(self.spells) 
        self.page_count = nspells//self.SPELL_LIMIT + int((nspells%self.SPELL_LIMIT) > 0)
    
    def create_embed(self):
        data = discord.Embed(title="Lista de Conjuros",
                                        description=f"(Los marcados con un * están siempre preparados)")
        spells = self.spells[self.current_page*self.SPELL_LIMIT:(self.current_page+1)*self.SPELL_LIMIT]
        for name, src in spells:
            data.add_field(name=name, value=src, inline=False)
        return data



BASE_DIR = Path(__file__).resolve().parent

def levenshteinDistance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

class Rol(commands.Cog):
    """Roleplay commands."""
    CLASSES = ["Artífice", "Bardo", "Brujo", "Clérigo", "Druida", "Explorador", "Hechicero", "Mago", "Paladín",]
    WITH_ACCENT = {
        "Artifice":"Artífice", "Bardo":"Bardo", "Brujo":"Brujo", "Clerigo":"Clérigo",
        "Druida":"Druida", "Explorador":"Explorador", "Hechicero":"Hechicero",
        "Mago":"Mago", "Paladin":"Paladín",
    }
    # layout
    # [name, subclass, optional]
    CLASS2SPELL = {}
    for c in CLASSES:
        CLASS2SPELL[c] = []
    CLASS2CASTER = {"Artífice":1, "Bardo":0, "Brujo":0, "Clérigo":0, "Druida":0, "Explorador":1, "Hechicero":0, "Mago":0, "Paladín":1}

    MAX_SPELL_LVL = [
        lambda lvl: min((lvl+1)//2, 9),
        lambda lvl: min((lvl-1)//4 +1, 5)
    ]
    # layout
    # [lvl, name, school, cast_time, reach, components, duration, description, src]
    ALL_SPELLS = {}

    SCHOOL2COLOR = {
        "Nigromancia": (255,0,0),
        "Adivinación": (255,255,0),
        "Abjuración": (128, 0, 255),
        "Transmutación": (255,0,255),
        "Evocación": (0,0,255),
        "Ilusión": (0,255,0),
        "Encantamiento": (128,128,128),
        "Conjuración": (128, 255, 255)
    }
    
    def __init__(self, bot):
        self.bot = bot
        if Rol.ALL_SPELLS:
            return
        with (BASE_DIR/"all_spells.csv").open(encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, delimiter=';', quotechar='"')
            for row in reader:
                Rol.ALL_SPELLS[row[1]] = row
        INPUT_DIR = BASE_DIR/"class_spells"
        for fname in INPUT_DIR.glob('*.csv'):
            class_name = fname.stem
            with fname.open(encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile, delimiter=';', quotechar='"')
                for row in reader:
                    Rol.CLASS2SPELL[class_name].append(row)
    
    def correct_spell(self, spell:str):
        if spell in self.ALL_SPELLS:
            return spell
        closest = min(self.ALL_SPELLS.keys(),
                    key=lambda s:min(levenshteinDistance(spell+" (RITUAL)", s), levenshteinDistance(spell, s)))
        # print(f"{spell} unknown. Do you mean {closest}?")
        return closest

    def get_spells(self, classes):
        # layout [class, subclass, lvl]
        classes = classes or []
        result = {}
        for c, sc, lvl in classes:
            max_sp_lvl = Rol.MAX_SPELL_LVL[Rol.CLASS2CASTER[c]](int(lvl))
            entries = filter(lambda e: (e[1] == "" or e[1] == sc)
                            and (int(Rol.ALL_SPELLS[e[0]][0]) <= max_sp_lvl), Rol.CLASS2SPELL[c])
            for entry in entries:
                class_disp = f"{c}({entry[1]})" if entry[1] else c
                if entry[0] in result:
                    if entry[2] == "False":
                        if result[entry[0]][1][-1] == '*':
                            result[entry[0]][1] += f", {class_disp}*"
                        else:
                            result[entry[0]] = [entry[0], f"{class_disp}*"]
                    else:
                        if result[entry[0]][1][-1] != '*':
                            result[entry[0]][1] += f", {class_disp}" #
                else:
                    if entry[2] == "False":
                        result[entry[0]] = [entry[0], f"{class_disp}*"]
                    else:
                        result[entry[0]] = [entry[0], class_disp] #
        
        spells = sorted([
            [Rol.ALL_SPELLS[e[0]][0], f"Lv.{Rol.ALL_SPELLS[e[0]][0]} {Rol.ALL_SPELLS[e[0]][1]}", *Rol.ALL_SPELLS[e[0]][2:-1], e[1]+" "+Rol.ALL_SPELLS[e[0]][-1]]
            for e in result.values()
        ])
        return spells

    @commands.command(aliases=["r"])
    async def roll(self, ctx, *cmd):
        """Rolls dices"""
        await ctx.send(str(d20.roll(" ".join(cmd))))

    @commands.command()
    async def spell(self, ctx, *query):
        """Queries DnD spell by name"""
        query = (" ".join(query)).upper()
        spell_name = self.correct_spell(query)
        spell_data = self.ALL_SPELLS[spell_name]

        view = SpellInfoView(spell_name, spell_data, discord.Color.from_rgb(*self.SCHOOL2COLOR[spell_data[2]]))

        await view.send(ctx)
    
    def process_class_entry(self, query):
        splitted = query.upper().split(',')
        splitted[0] = splitted[0].capitalize()

        try:
            splitted[1] = splitted[1].capitalize()
            lvl = int(splitted[2])
        except:
            return None
        
        if (lvl > 20 or lvl < 1 or (splitted[0] not in Rol.CLASSES and splitted[0] not in Rol.WITH_ACCENT)):
            return None
        if splitted[0] in Rol.WITH_ACCENT:
            splitted[0] = Rol.WITH_ACCENT[splitted[0]]
        return splitted[:3]
    
    @commands.command()
    async def spelllist(self, ctx, *query):
        query = (" ".join(query)).lower().strip()
        classes = []
        for q in query.split():
            pq = self.process_class_entry(q)
            if pq is None:
                return await ctx.send("Usage: -spelllist Class,Subclass,Level ...")
            classes.append(pq)
        spells = self.get_spells(classes)
        view = SpellListView(spells, None)
        await view.send(ctx)
        

async def setup(bot):
    await bot.add_cog(Rol(bot))
