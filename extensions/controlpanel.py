"""
  ControlPanel - Reduce command clutter by making settings available through ControlPanel instead.
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING
import disnake
from disnake.ext import commands

if TYPE_CHECKING:
  from main import MerelyBot
  from babel import Resolvable
  from config import Config

# Models


class Setting():
  buttonstyle:disnake.ButtonStyle
  pos:int

  @property
  def id(self) -> str:
    return f'controlpanel_{self.scope}/{self.key}'

  def __init__(self, label:str, config:Config, scope:str, key:str):
    self.label = label
    self.config = config
    self.scope = scope
    self.key = key

  def set(self, value:str):
    self.config.set(self.scope, self.key, value)
    self.config.save()

  def get(self, fallback=None):
    return self.config.get(self.scope, self.key, fallback=fallback)

  def generate_component(self) -> disnake.ui.Item:
    raise Exception("Setting.generate_component() must be overriden.")


class Toggleable(Setting):
  def get(self, fallback=None):
    try:
      return self.config.getboolean(self.scope, self.key)
    except Exception:
      return fallback

  def toggle(self):
    value = self.get(False)
    self.set(str(not value))

  def generate_component(self) -> disnake.ui.Item:
    """ Toggle button for settings which can only be true or false """
    value = self.get('*unset*')
    button = disnake.ui.Button(
      style=self.buttonstyle,
      label=f'{self.label}: {value}',
      custom_id=self.id,
      emoji='🟢' if value else '⭕',
      row=self.pos
    )
    return button


class Selectable(Setting):
  def __init__(self, label:str, config:Config, scope:str, key:str, possible_values:list[str]):
    super().__init__(label, config, scope, key)
    self.possible_values = possible_values

  def generate_component(self) -> disnake.ui.Item:
    """ Select button for settings which can only have pre-determined values """
    value = self.get('*unset*')
    select = disnake.ui.Select(
      custom_id=self.id,
      placeholder=f'{self.label}: {value}',
      min_values=1,
      max_values=1,
      options=self.possible_values
    )
    return select


class Stringable(Setting):
  def generate_component(self) -> disnake.ui.Item:
    value = self.get('*unset*')
    button = disnake.ui.Button(
      style=self.buttonstyle,
      label=f'{self.label}: {value}',
      custom_id=self.id,
      emoji='✏️',
      row=self.pos
    )
    return button


class ControlPanel(commands.Cog):
  """ Adds an echo command and logs new members """
  SCOPE = 'controlpanel'
  panels:dict[int, ControlPanelView]

  @property
  def config(self) -> dict[str, str]:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> list[str]:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  def __init__(self, bot:MerelyBot):
    self.bot = bot
    if not bot.config.getboolean('extensions', 'auth', fallback=False):
      raise Exception("'auth' must be enabled to use 'controlpanel'")
    self.settings:list[Toggleable | Selectable | Stringable] = []
    self.section_styles:dict[str, disnake.ButtonStyle] = {}
    self.panels = {}
    # ensure config file has required data
    #if not bot.config.has_section(self.SCOPE):
    #  bot.config.add_section(self.SCOPE)

  # Events

  @commands.Cog.listener('on_connect')
  async def discover_settings(self):
    for cog in self.bot.cogs:
      attr = getattr(self.bot.cogs[cog], 'controlpanel_settings', None)
      if callable(attr):
        self.settings += attr()
        if self.bot.verbose:
          print(f"Loaded controlpanel settings from '{cog}'")
      attr = getattr(self.bot.cogs[cog], 'controlpanel_theme', None)
      if callable(attr):
        data:tuple[str, disnake.ButtonStyle] = attr()
        self.section_styles[data[0]] = data[1]
        if self.bot.verbose:
          print(f"Loaded controlpanel theme from '{cog}'")

  @commands.Cog.listener('on_message_interaction')
  async def on_panel_interaction(self, inter:disnake.MessageInteraction):
    if inter.message.id in self.panels:
      await self.panels[inter.message.id].callback_all(inter)

  # Modals

  class StringEditModal(disnake.ui.Modal):
    """ Just provides a text box for editing the value of a stringable setting """
    def __init__(self, parent:ControlPanel.ControlPanelView, setting:Stringable):
      self.parent = parent

      super().__init__(
        title=setting.label,
        custom_id=setting.id,
        components=[disnake.ui.TextInput(
          label=setting.label,
          custom_id='value',
          placeholder=setting.get(''),
          value=setting.get(''),
          style=disnake.TextInputStyle.single_line,
          min_length=0
        )],
        timeout=300
      )

    async def callback(self, inter:disnake.ModalInteraction):
      await self.parent.callback_all(inter)

  # Views

  class ControlPanelView(disnake.ui.View):
    msg:disnake.Message | None

    def __init__(
      self,
      inter:disnake.CommandInteraction,
      parent:ControlPanel,
      settings:list[Toggleable | Selectable | Stringable]
    ):
      super().__init__(timeout=300)

      self.msg = None
      self.parent = parent
      self.components:dict[str, disnake.ui.Item] = {}
      self.settings:dict[str, Toggleable | Selectable | Stringable] = {}
      sections:list[str] = []
      rowcap:dict[int, int] = {}

      for setting in settings:
        buttonstyle = parent.section_styles.get(setting.scope, disnake.ButtonStyle.primary)
        if setting.scope not in sections:
          sections.append(setting.scope)
        sectionnumber = sections.index(setting.scope)

        # Automatically shift components until they fit within size constraints
        # Type checking has to be relaxed a bit here because of issues with importing these types in
        # other modules
        if type(setting).__name__ == Selectable.__name__:
          # Selections take up a full row
          pos = sectionnumber
          while rowcap.get(pos, 0) > 0:
            pos += 1
          rowcap[pos] = 5
        else:
          # Buttons take up a 5th of a row (?)
          pos = sectionnumber
          while rowcap.get(pos, 0) > 4:
            pos += 1
          rowcap[pos] = rowcap.get(pos, 0) + 1

        # Dereference setting from the Cog so command-specific changes can be made
        localsetting = copy.copy(setting)
        localsetting.key = (
          localsetting.key
          .replace('{g}', str(inter.guild_id))
          .replace('{u}', str(inter.user.id))
        )
        localsetting.buttonstyle = buttonstyle
        localsetting.pos = pos
        item = localsetting.generate_component()
        self.components[localsetting.id] = (item)
        self.settings[localsetting.id] = localsetting
        self.add_item(item)

    async def callback_all(self, inter:disnake.MessageInteraction | disnake.ModalInteraction):
      id = inter.data.custom_id
      if id in self.settings:
        setting = self.settings[id]

        # Verify an admin pressed the button
        self.parent.bot.cogs['Auth'].admins(inter)
        # Check with premium before continuing
        generickey = (
          setting.scope + '/' +
          setting.key.replace(str(inter.guild_id), '{g}').replace(str(inter.user.id), '{u}')
        )
        print(self.parent.bot.cogs)
        if (
          generickey in self.parent.bot.config['premium']['restricted_config'].split()
          and 'Premium' in self.parent.bot.cogs
        ):
          if not await self.parent.bot.cogs['Premium'].check_premium(inter.user):
            embed = self.parent.bot.cogs['Premium'].error_embed(inter)
            await inter.response.send_message(embed=embed, ephemeral=True)

        if isinstance(inter, disnake.ModalInteraction):
          # Callback from string edit modal
          setting.set(inter.text_values['value'])
        elif type(setting).__name__ == Toggleable.__name__:
          # Toggle button was pressed
          setting.toggle()
        elif type(setting).__name__ == Selectable.__name__:
          # Selection was made
          setting.set(inter.data.values[0])
        elif type(setting).__name__ == Stringable.__name__:
          # String edit button was pressed
          await inter.response.send_modal(self.parent.StringEditModal(self, setting))
          return
        else:
          raise TypeError(setting)

        comp = setting.generate_component()
        oldcompindex = [
          i for i,c in enumerate(self.children)
          if isinstance(c, (disnake.ui.Button, disnake.ui.Select)) and c.custom_id == id
        ][0]
        if isinstance(self.children[oldcompindex], disnake.ui.Button):
          self.children[oldcompindex].label = comp.label
          self.children[oldcompindex].emoji = comp.emoji
        elif isinstance(self.children[oldcompindex], disnake.ui.Select):
          self.children[oldcompindex].placeholder = comp.placeholder
        self.timeout = 300
        await inter.response.edit_message(view=self)

    async def on_timeout(self) -> None:
      if self.msg:
        await self.msg.delete()
      else:
        for component in self.children:
          if isinstance(component, (disnake.ui.Button, disnake.ui.Select)):
            component.disabled = True
        await self.msg.edit(view=self)

  # Commands

  @commands.default_member_permissions(administrator=True)
  @commands.guild_only()
  @commands.slash_command()
  async def controlpanel(self, inter:disnake.CommandInteraction):
    """ Opens the control panel so you can change bot settings for this guild """
    self.bot.cogs['Auth'].admins(inter)
    if len(self.settings) < 1:
      inter.response.send_message(self.babel(inter, 'no_settings'))
      return
    panel = self.ControlPanelView(inter, self, self.settings)
    await inter.response.send_message(
      view=panel,
      ephemeral=True
    )
    panel.msg = await inter.original_response()
    self.panels[panel.msg.id] = panel


def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  bot.add_cog(ControlPanel(bot))
