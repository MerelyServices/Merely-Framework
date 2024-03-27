"""
  ControlPanel - Reduce command clutter by making settings available through ControlPanel instead.
  Works well with Premium, depends on other cogs to have a controlpanel_settings() and optionally a
  controlpanel_theme()
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING
import disnake
from disnake.ext import commands

if TYPE_CHECKING:
  from main import MerelyBot
  from babel import Resolvable
  from configparser import SectionProxy

# Models


class Setting():
  bot:MerelyBot
  buttonstyle:disnake.ButtonStyle
  pos:int

  def __init__(self, scope:str, key:str, babel_key:str):
    """
      Creates a setting that can be changed or unset by the user in controlpanel
    """
    self.scope = scope
    self.babel_key = babel_key
    self.key = key

  @property
  def id(self) -> str:
    return f'controlpanel_{self.scope}/{self.key}'

  def label(self, target:Resolvable) -> str:
    return self.bot.babel(target, self.scope, self.babel_key)

  def get(self, fallback=None):
    return self.bot.config.get(self.scope, self.key, fallback=fallback)

  def set(self, value:str | None):
    if value is None:
      self.bot.config.remove_option(self.scope, self.key)
    else:
      self.bot.config.set(self.scope, self.key, value)
    self.bot.config.save()

  def generate_components(self, target:Resolvable) -> list[disnake.ui.Item]:
    raise Exception("Setting.generate_components() must be overriden.")


class Toggleable(Setting):
  def __init__(self, scope:str, key:str, babel_key:str, default:bool | None = None):
    """ Creates a toggleable setting. If default is None, it cannot be unset by the user. """
    super().__init__(scope, key, babel_key)
    self.default = default

  def get(self, fallback=None):
    return self.bot.config.get(self.scope, self.key, fallback=fallback)

  def toggle(self):
    # Hides the unset state by assuming unset means self.default
    converter = {
      'True': None if self.default is False else 'False',
      'False': None if self.default is True else 'True',
      '_default': 'True' if self.default is None else str(not self.default)
    }
    value = converter.get(self.get('_default'), 'True')
    self.set(value)

  def generate_components(self, target:Resolvable) -> list[disnake.ui.Item]:
    """ Toggle button for settings which can only be true or false """
    value = self.get(str(self.default))
    b1 = disnake.ui.Button(
      style=self.buttonstyle,
      label=f'{self.label(target)}: {value}',
      custom_id=self.id,
      emoji='⚪' if value is None else ('🟢' if value == 'True' else '⭕'),
      row=self.pos
    )
    return [b1]


class Listable(Toggleable):
  delimiter = ','

  def __init__(self, scope:str, key:str, babel_key:str, value:str):
    """ Creates a listable setting, where true or false means the value's presence on the list. """
    super().__init__(scope, key, babel_key, default=False)
    self.value = value

  def get(self, _):
    return str(self.value in self.bot.config.get(self.scope, self.key, fallback=''))

  def set(self, include:bool):
    state = self.bot.config.get(self.scope, self.key, fallback='')
    if include:
      self.bot.config.set(self.scope, self.key, state + self.value + self.delimiter)
    else:
      newstate = state.replace(self.value + self.delimiter, '')
      self.bot.config.set(self.scope, self.key, newstate)
    self.bot.config.save()


class Selectable(Setting):
  def __init__(self, scope:str, key:str, babel_key:str, possible_values:list[str]):
    """ Creates a selectable setting. *unset* will be added to possible_values. """
    super().__init__(scope, key, babel_key)
    self.possible_values = possible_values

  def generate_components(self, target:Resolvable) -> list[disnake.ui.Item]:
    """ Select button for settings which can only have pre-determined values """
    value = self.get('*unset*')
    select = disnake.ui.Select(
      custom_id=self.id,
      placeholder=self.bot.utilities.truncate(f'{self.label(target)}: {value}', 40),
      min_values=1,
      max_values=1,
      options=['*unset*'] + self.possible_values
    )
    return [select]


class Stringable(Setting):
  def generate_components(self, target:Resolvable) -> list[disnake.ui.Item]:
    value = self.get('*unset*')
    b1 = disnake.ui.Button(
      style=self.buttonstyle,
      label=self.bot.utilities.truncate(f'{self.label(target)}: {value}', 40),
      custom_id=self.id,
      emoji='✏️',
      row=self.pos
    )
    b2 = disnake.ui.Button(
      style=self.buttonstyle,
      label='',
      custom_id=self.id+'_reset',
      emoji="🔁",
      row=self.pos
    )
    return [b1, b2]


class ControlPanel(commands.Cog):
  """ Adds an echo command and logs new members """
  SCOPE = 'controlpanel'
  panels:dict[int, ControlPanelView]

  @property
  def config(self) -> SectionProxy:
    """ Shorthand for self.bot.config[scope] """
    return self.bot.config[self.SCOPE]

  def babel(self, target:Resolvable, key:str, **values: dict[str, str | bool]) -> list[str]:
    """ Shorthand for self.bot.babel(scope, key, **values) """
    return self.bot.babel(target, self.SCOPE, key, **values)

  def __init__(self, bot:MerelyBot):
    self.bot = bot
    self.section_styles:dict[str, disnake.ButtonStyle] = {}
    self.panels = {}
    # ensure config file has required data
    #if not bot.config.has_section(self.SCOPE):
    #  bot.config.add_section(self.SCOPE)

  # Events

  @commands.Cog.listener('on_connect')
  async def discover_styles(self):
    for cog in self.bot.cogs:
      fn = getattr(self.bot.cogs[cog], 'controlpanel_theme', None)
      if callable(fn):
        data:tuple[str, disnake.ButtonStyle] = fn()
        self.section_styles[data[0]] = data[1]

  def discover_settings(self, inter:disnake.Interaction) -> list[Setting]:
    out = []
    for cog in self.bot.cogs:
      fn = getattr(self.bot.cogs[cog], 'controlpanel_settings', None)
      if callable(fn):
        out += fn(inter)
    return out

  @commands.Cog.listener('on_message_interaction')
  async def on_panel_interaction(self, inter:disnake.MessageInteraction):
    if inter.message.id in self.panels:
      await self.panels[inter.message.id].callback_all(inter)
    return

  # Modals

  class StringEditModal(disnake.ui.Modal):
    """ Just provides a text box for editing the value of a stringable setting """
    def __init__(self, parent:ControlPanel.ControlPanelView, setting:Stringable):
      self.parent = parent

      super().__init__(
        title=setting.label(parent.msg),
        custom_id=setting.id,
        components=[disnake.ui.TextInput(
          label=setting.label(parent.msg),
          custom_id='value',
          placeholder=self.parent.parent.bot.utilities.truncate(setting.get(''), 100),
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
    msg:disnake.Message | None = None

    def __init__(
      self, inter:disnake.CommandInteraction, parent:ControlPanel, settings:list[Setting]
    ):
      super().__init__(timeout=300)

      self.parent = parent
      self.settings:dict[str, Setting] = {}
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

        # Toggle buttons take up one column
        buttonwidth = 1
        if type(setting).__name__ == Selectable.__name__:
          # Selections take up a full row
          buttonwidth = 5
        elif type(setting).__name__ == Stringable.__name__:
          # String buttons take up two columns
          buttonwidth = 2

        # Calculate positioning of this component based on the space it will take up
        pos = sectionnumber
        while rowcap.get(pos, 0) > (5 - buttonwidth):
          pos += 1
        rowcap[pos] = rowcap.get(pos, 0) + buttonwidth

        # Dereference setting from the Cog so command-specific changes can be made
        localsetting = copy.copy(setting)
        localsetting.bot = self.parent.bot
        localsetting.buttonstyle = buttonstyle
        localsetting.pos = pos
        items = localsetting.generate_components(inter)
        self.settings[localsetting.id] = localsetting
        for item in items:
          self.add_item(item)

    async def callback_all(self, inter:disnake.MessageInteraction | disnake.ModalInteraction):
      id = inter.data.custom_id
      reset = False
      if id.endswith('_reset') and id[0:-len('_reset')] in self.settings:
        reset = True
        setting = self.settings[id[0:-len('_reset')]]
      elif id in self.settings:
        setting = self.settings[id]
      else:
        return

      # Check for premium before continuing
      generickey = (
        setting.scope + '/' +
        setting.babel_key
      )
      if (
        generickey in self.parent.bot.config['premium']['restricted_config'].split()
        and 'Premium' in self.parent.bot.cogs
      ):
        if not await self.parent.bot.cogs['Premium'].check_premium(inter.user):
          embed = self.parent.bot.cogs['Premium'].error_embed(inter)
          await inter.response.send_message(embed=embed, ephemeral=True)
          return

      if reset:
        setting.set(None)
      elif isinstance(inter, disnake.ModalInteraction):
        # Callback from string edit modal
        setting.set(inter.text_values['value'])
      elif type(setting).__name__ in (Toggleable.__name__, Listable.__name__):
        # Toggle-style button was pressed
        setting.toggle()
      elif type(setting).__name__ == Selectable.__name__:
        # Selection was made
        if inter.data.values[0] == '*unset*':
          setting.set(None)
        else:
          setting.set(inter.data.values[0])
      elif type(setting).__name__ == Stringable.__name__:
        # String edit button was pressed
        await inter.response.send_modal(self.parent.StringEditModal(self, setting))
        return
      else:
        raise TypeError(setting)

      comps = setting.generate_components(inter)
      for comp in comps:
        oldcompindex = [
          i for i,c in enumerate(self.children)
          if (
            isinstance(c, (disnake.ui.Button, disnake.ui.Select)) and c.custom_id == comp.custom_id
          )
        ][0]
        if isinstance(self.children[oldcompindex], disnake.ui.Button):
          self.children[oldcompindex].label = comp.label
          self.children[oldcompindex].emoji = comp.emoji
        elif isinstance(self.children[oldcompindex], disnake.ui.Select):
          self.children[oldcompindex].placeholder = comp.placeholder
      self.timeout = 300
      await inter.response.edit_message(view=self)

    async def on_timeout(self):
      if self.msg:
        try:
          await self.msg.delete()
        except disnake.HTTPException:
          pass
      else:
        for component in self.children:
          if isinstance(component, (disnake.ui.Button, disnake.ui.Select)):
            component.disabled = True
        await self.msg.edit(view=self)

  # Commands

  @commands.slash_command()
  async def controlpanel(self, inter:disnake.CommandInteraction):
    """ Opens the control panel so you can change bot preferences for this guild and yourself """
    settings = self.discover_settings(inter)
    panel = self.ControlPanelView(inter, self, settings)
    if len(panel.settings) < 1:
      inter.response.send_message(self.babel(inter, 'no_settings'))
      return
    await inter.response.send_message(
      view=panel,
      ephemeral=True
    )
    panel.msg = await inter.original_response()
    self.panels[panel.msg.id] = panel


def setup(bot:MerelyBot):
  """ Bind this cog to the bot """
  bot.add_cog(ControlPanel(bot))
