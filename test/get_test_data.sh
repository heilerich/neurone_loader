#!/usr/bin/env bash
DATA_DIR="${TEST_DATA_DIR:-test/test_data}"

download_data () {
  find . -not -path "./.git/*" \( -type f -o -type l \) -exec rm {} \; -exec wget -q --show-progress https://web.gin.g-node.org/heilerich/NeuroneTestdata/raw/master/{} -O {} \;
}

if [ ! -d "${DATA_DIR}" ]
then
  git clone https://gin.g-node.org/heilerich/NeuroneTestdata
  mv NeuroneTestdata "${DATA_DIR}"
  pushd "${DATA_DIR}"
  download_data
else
  pushd "${DATA_DIR}"
  git fetch
  HEADHASH=$(git rev-parse HEAD)
  UPSTREAMHASH=$(git rev-parse master@{upstream})
  if [ "$HEADHASH" != "$UPSTREAMHASH" ]
  then
    echo "Test data not up to date with origin."
    git reset --hard
    git pull
    download_data
  else
    echo "Already on newest commit."
  fi
fi

popd
