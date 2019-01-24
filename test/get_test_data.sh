#!/usr/bin/env bash
git clone https://web.gin.g-node.org/heilerich/NeuroneTestdata
cd NeuroneTestdata
find . -not -path "./.git/*" \( -type f -o -type l \) -exec rm {} \; -exec wget -q --show-progress https://web.gin.g-node.org/heilerich/NeuroneTestdata/raw/master/{} -O {} \;
cd ..
mv NeuroneTestdata test/test_data