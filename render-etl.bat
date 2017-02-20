@echo off
set @vcd=%cd%
cd %1
etl.exe +com_ignorecrash 1 +set fs_game uvMovieMod +demo demo-render.dm_84 +wait 150 +video render +nextdemo "quit"
