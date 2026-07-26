#!/bin/bash
echo "Starting auto github update (pull&push)"
cd /home/alicj/Documents/Github/led-bar-menu
git pull
git add .
git commit -m "Auto update"
git push
