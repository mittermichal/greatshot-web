# Wolfenstein: Enemy Territory demo tools

## what it can do:
- cut demos (dm_84/tv_84) -> dm_84
- export demos (dm_84/tv_84) to json and analyze it to output:
	- hit regions (headshots) counter
	- fast consecutive kills <img src="/static/excellent.png" height="25" width="25"/>
- download ettv demo (tv_84) from [gamestv.org](http://gamestv.org)


## what it could do in future:
- render demo to video and publish it - [example](https://streamable.com/wkv8)
- create database of statistics
- render highlights from gamestv match
- link highlinghs and statistics in comments of gamestv match
- visualize timeline of match
- have better documentation
- find consecutive headshots
- revive counter


This project uses  [hannes's](http://www.crossfire.nu/user/view/id/6710) modified [Tech3 Demo API - 0.1](http://www.crossfire.nu/news/4632/tech3-demo-api-01) to cut and export demos.
It was modified to be able to cut ettv demo with selected player's POV.
