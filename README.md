# Greatshot
Demo analysis, cutting, IdTech3 games mainly Wolfenstein: Enemy Territory (etpro, legacy) and RTCW (RTCWPro)
[![Discord](https://img.shields.io/discord/546291405404897290?label=discord)](https://discord.gg/p59kWdF)
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=BRRRFPT7N9NP6&currency_code=EUR&source=url)

## Rewrite branch:

This branch doesn't have rendering stuff and Gamestv integration for simplier installation. Gamestv integration doesn't work anymore because login process was changed.

## Features:
- cut demos (dm_84/tv_84) -> dm_84
- export demos (dm_84/tv_84) to json and analyze it to output:
	- hit regions (headshots) counter
	- fast consecutive kills <img src="/app/static/excellent.png" height="25" width="25"/> [example](https://streamable.com/a5tx7)
	- consecutive headshots - [example](https://streamable.com/e4ogi)
	- revive stats (only for ETTV)

This project uses  [hannes's](http://www.crossfire.nu/user/view/id/6710) modified [Tech3 Demo API - 0.1](http://www.crossfire.nu/news/4632/tech3-demo-api-01) to cut and export demos.
It was modified to be able to cut [ETTV](http://wolfwiki.anime.net/index.php/ETTV:Viewer%27s_Guide) demo with selected player's POV. My modification: [Tech3 Demo API](https://github.com/mittermichal/Anders.Gaming.LibTech3)

## Run:

with python3.12: 
- `pip install -r requirements.txt`
- download parsing application from https://github.com/mittermichal/Anders.Gaming.LibTech3/releases its path is then referenced in `PARSERPATH` in `config.cfg`
- run `python greatshot_web.py`
- open `localhost:5000` in browser

alternatively use poetry to install dependencies