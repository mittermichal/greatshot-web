@echo off
set @vcd=%cd%
cd %1
del etpro\screenshots\*.tga
et.exe +set fs_game etpro +demo demo-render +wait 150 +timescale 1 +cl_avidemo 60 +set nextdemo "exec gtvsound"

