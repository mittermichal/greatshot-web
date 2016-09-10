@echo off
set @vcd=%cd%
cd %1
del etpro\screenshots\*.tga
et.exe +set fs_game etpro +demo demo-render +wait 150 +timescale 1 +cl_avidemo 60 +set nextdemo "exec gtvsound"
ffmpeg -y -framerate 60 -i "etpro/screenshots/shot%%04d.tga" -i etpro/wav/synctest.wav -c:a libvorbis -shortest render.mp4
move /Y render.mp4 "%@vcd%\render.mp4"
