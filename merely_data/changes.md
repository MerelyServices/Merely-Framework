### 0.1.0
 - migration of all features from chatbot to merely - music module added.
### 0.2.0
 - improved logging and created the merelybot api at http://yiaysmc.noip.me:8000
#### 0.2.1
 - server owners now have more commands available to them, they recieve instructions when merely is added to their server.
#### 0.2.2
 - help command overhauled
#### 0.2.3
 - merelybot api improved and redundant 'please wait...'-like messages removed. cleaned up references to non-existant commands.
#### 0.2.4
 - music module replaced with JMusicBot. m/thonk added.
 - added interactive server list (m/servers). commands re-arranged to not conflict with JMusicBot.
### 0.3.0
 - migrated to discord.py[rewrite] to take advangage of new features.
 - m/janitor, m/welcome, m/farewell, m/purge and m/clean were broken.
 - musicbot functionality removed after being banned from a bot list for using JMusicBot.
### 0.4.0
 - fixed `m/welcome` and `m/farewell`.
 - fixed a variety of small bugs and removed all references to the long-gone music bot functionality.
 - added more information to `m/stats`.
 - added more thonks to `m/thonk`, including new gif emojis!
 - our moderators have overhauled the meme list.
 - moderators now have the ability to lock out misbehaving users from being able to abuse the bot.
#### 0.4.1
 - `m/meme` doesn't repeat memes as often.
 - added `m/meme repeatstats` and `m/meme count`.
 - merely can now notify server owners whenever an update rolls out.
#### 0.4.2
 - `m/clean, m/purge` have been fixed. however `m/janitor` is still broken.
#### 0.4.3
 - made it possible to opt out of update news if server owners don't want them.
 - fixed a major bug related to `m/echo` that thankfully was never exploited.
 - fixed a major bug related to `m/lockout` that prevented it from working properly.
#### 0.4.4
 - merely's censorship system (for image search) has been even further improved.
 - improved error handling for all commands that have a tendancy to fail when given strange input.
#### 0.4.5
 - improved the relevancy of search results in `m/command`
 - added tonnes of aliases to commands eg. `m/command, m/commands | m/image, m/images | m/stats, m/status` to reduce user error.
 - added `m/vote` - a vote command with progress bars, multiple choice, and custom countdown timers!
#### 0.4.6
 - overhauled statistics collection for compatibility with the [updated website](http://yiaysmc.noip.me)
#### 0.4.7
 - overhauled settings storage and saving, more settings will be persistent between restarts of merely now.
 - added `m/watching, m/streaming, m/listening` on top of `m/playing`.
 - you can now use `m/image more` multiple times or use `m/images` to automatically get 5 images.
 - yiaysmc.noip.me is down.
### 0.5.0
 - censor module overhauled, there may be more false positives now, but in general it's way more effective.
 - `m/image` can finally fetch full-size images from google images.
 - migrated to a faster server. *turns out merely was down because the old server couldn't keep up with all the servers.*
 - yiaysmc.noip.me is still down, no idea why.
 - several commands, like `m/google` no longer work with embeds, no idea why.
 - `m/censor` is a new command for server owners to test for false positives and false negatives in the censor module directly.
#### 0.5.1
 - All embeds should render normally again. 😠
#### 0.5.2
 - `m/stats` and yiaysmc.noip.me are back online.
 - `m/image` now checks to see if google autocorrected your search before showing results.
 - `m/blacklist` now supports adding words that are already covered by the blacklist if they're not identical in order to make it possible to catch more misspellings of words that previously weren't blacklisted directly.
### 0.6.0
 - Fixed an issue that was preventing `m/playing` from persisting after a restart
 - Created a meme database and an [accompanying website](https://meme.yiays.com) for better `m/meme` results.
 - Created a background service that can scan specific channels for memes and allow members to vote which are added to the meme database.
 - Moved merely's documentation website to [merely.yiays.com](https://merely.yiays.com) and updated all links. Old links work for now, but will be removed in the future.
#### 0.6.1
 - The meme background scanner has been tweaked, votes are now deleted once they're counted, and memes that were added to the website are given an additional tick react.
 - `m/stats` now calculates an accurate uptime percentage and tracks when the bot goes down.
 - `m/meme` is now a stub, no new memes can be added through the old method (`m/meme add`). All memes that were in `m/meme` are now in the memeDB. `m/meme` will show all memes from memeDB in the future.
#### 0.6.2
 - Fixed janitor, finally. - `m/janitor join (relaxed/strict)` is back in order.
 - `m/clean` now has another feature; `m/clean n strict` will delete *n* posts indiscriminately.
 - Fixed an issue with the meme background scanner (for [meme.yiays.com](https://meme.yiays.com/)) not supporting multiple urls in the same message.
### 0.7.0
With this release, we are launching [MemeDB](https://meme.yiays.com) - an online database full of memes, designed to be easily searchable!
 - `m/lockout` has a more reliable back-end now.
 - Music bot functionality is back, use `m/play` to find out more.
 - There are more restrictions on what can and can't be added to MemeDB.
 - `m/dice` added. Roll as many dice with as many sides as you want.
 - Merely now logs image search results, making improving the blacklist easier.
 - `m/meme` is now powered by [MemeDB](https://meme.yiays.com)
 - The meme background scanner *still* has issues with multiple urls.
#### 0.7.1
 - Plenty of progress has been put towards making it easier for developers to download merely and set up their own bot for testing.
 - Mods on [Merely's official server](https://discord.gg/f6TnEJM) can now blacklist and whitelist the types of urls that are considered memes.
 - `m/lockout` had an issue where it couldn't be used to ban members on another server, this has been fixed.
 - The meme count in `m/stats` has been discontinued. Also, `m/stats` appears to be malfunctioning.
#### 0.7.2
 - Music bot integration has been further improved.
 - Logging has been improved.
 - Image search has been improved again! Merely will now try harder to avoid coming up empty at random when you search, and will give a detailed explaination of what went wrong when it does.
 - Merely's sass when catching someone out with the censor has been updated and is now a little less cringe.
 - `m/blacklist` and `m/whitelist` have been improved so that they will work no matter the character length. (with a sane limit of 9500 characters at most)
#### 0.7.3
 - Meme has been updated to automatically download memes to the CDN immediately after adding them to the database.
 - Collections support has finally been fixed completely. Multiple URLs or uploaded images in one message will be grouped together as one collection when upvoted.
#### 0.7.4
 - Sadly, `m/google` and `m/image` have been blocked by google, so they no longer work.
 - Added in a link shortener which uses the new https://l.yiays.com service.
 - Tweaked the featured commands in `m/help` and https://merely.yiays.com
#### 0.7.5
 - `m/stats` is working once again!
 - Wording in help commands and information about merely has been updated to be more accurate.
 - Merely will now preload thumbnails as soon as a meme is upvoted, ensuring they're ready for anyone to view right away.
 - The blocked message in `m/lockout` now shows the correct waiting time.
### 0.8.0
 - Massive overhaul of the censor module, each guild now has a local blacklist and whitelist which server owners can modify.
#### 0.8.1
 - `m/meme` will now search the database whenever you follow the command with a search string.
 - `m/blacklist train` and `m/whitelist train` have been added back to the censor module. They're a little more robust now as well.
 - Protections have been put in place to prevent merely from hanging when fetching data from unknown sources.
#### 0.8.2
 - An uber blacklist has been added, which is a set of words in the blacklist that can never be removed for legal, discord TOS, or moral reasons.
### 0.9.0
 - The codebase has been restructured to improve stability and maintainability.
 - Some unit tests have been added to help catch bugs early
#### 0.9.1
 - Countless bugfixes while continuing work on the 1.0.0 release
#### 0.9.2
 - Tightening up security and professioinalism. Removed several commands that shouldn't be available to the public.
 - More error handling when minimal permissions are given.
#### 0.9.3
 - Removal of a few features related to counting members for the Discord API reform.
 - Improved error handling when merely isn't given enough permissions.
 - Moved website hosting to apache2 instead of in python.