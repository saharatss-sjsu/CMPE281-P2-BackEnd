cd $(dirname "$0")
pip3 install \
--platform manylinux2014_x86_64 \
--target=python \
--implementation cp \
--python-version 3.11 \
--only-binary=:all: --upgrade \
pillow boto3 requests