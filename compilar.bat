@echo off
title Compilando AmigoNeon...
echo ====================================
echo  Limpiando compilacion anterior...
echo ====================================
rmdir /s /q dist
rmdir /s /q build

echo ====================================
echo  Generando nuevo ejecutable...
echo ====================================
pyinstaller --noconsole --name "AmigoNeon" ^
  --add-data "assets;assets" ^
  --add-data "config;config" ^
  --add-data "core;core" ^
  --add-data "services;services" ^
  --add-data "ui;ui" ^
  main.py

echo ====================================
echo  Compilacion lista en /dist/AmigoNeon
echo ====================================
pause