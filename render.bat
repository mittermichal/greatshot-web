@echo off
set @vcd=%cd%
cd %1
del etpro\screenshots\*.tga
et.exe +set fs_game etpro +demo demo-render +wait 150 +exec init-tga +timescale 1 +set nextdemo "exec preinit-wav"

