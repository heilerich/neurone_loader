#!/usr/bin/env bash
DATA_DIR="${TEST_DATA_DIR:-test/test_data}"

TEST_COMMIT='ea70140b94160967fe92c0623d73af5f0c33cf0b'

download_data () {
  find . -not -path "./.git/*" \( -type f -o -type l \) -exec rm {} \; -exec wget -q --show-progress https://web.gin.g-node.org/heilerich/NeuroneTestdata/raw/${TEST_COMMIT}/{} -O {} \;
}

if [ ! -d "${DATA_DIR}" ]
then
  git clone https://gin.g-node.org/heilerich/NeuroneTestdata
  mv NeuroneTestdata "${DATA_DIR}"
  pushd "${DATA_DIR}"
  git checkout "${TEST_COMMIT}"
  download_data
else
  pushd "${DATA_DIR}"
  git fetch
  HEADHASH=$(git rev-parse HEAD)
  if [ "$HEADHASH" != "$TEST_COMMIT" ]
  then
    echo "Test data not up to date with origin."
    git reset --hard
    git fetch --all
    git checkout "${TEST_COMMIT}"
    download_data
  else
    echo "Already on required commit."
  fi
fi

popd
