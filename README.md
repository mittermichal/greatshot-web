# Wolfenstein: Enemy Territory demo tools
[![Discord](https://img.shields.io/discord/546291405404897290?label=discord)](https://discord.gg/p59kWdF)
## what it can do:
- cut demos (dm_84/tv_84) -> dm_84
- export demos (dm_84/tv_84) to json and analyze it to output:
	- hit regions (headshots) counter
	- fast consecutive kills <img src="/static/excellent.png" height="25" width="25"/> [example](https://streamable.com/a5tx7)
	- consecutive headshots - [example](https://streamable.com/e4ogi)
- download ettv demo (tv_84) from [gamestv.org](http://gamestv.org)
- render demo to video and publish it - [example](https://streamable.com/2d77)
- link highlights and statistics in comments of gamestv match
- render highlights from gamestv match
- add player name + flag to highlight [example](https://streamable.com/zn7r4)

## what it could do in future:
- create database of players with statistics
- visualize timeline of match
- have better documentation
- revive stats
- retrieve true damage stats when its bugged to 0


This project uses  [hannes's](http://www.crossfire.nu/user/view/id/6710) modified [Tech3 Demo API - 0.1](http://www.crossfire.nu/news/4632/tech3-demo-api-01) to cut and export demos.
It was modified to be able to cut ettv demo with selected player's POV. My modification: [Tech3 Demo API](https://github.com/mittermichal/Anders.Gaming.LibTech3)
