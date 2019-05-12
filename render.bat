@echo off
set @vcd=%cd%
cd %1
del etpro\screenshots\*.tga
et.exe +viewlog 1 +logfile render.log +set fs_game etpro +set com_maxfps 125 +timescale 0 +demo demo-render +timescale 0 +wait 2 +timescale 1 +exec init-tga +condump init-tga.log +timescale 1 +set nextdemo "exec preinit-wav"

