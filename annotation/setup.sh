#!/bin/bash

wget http://weaver.nlplab.org/~brat/releases/brat-v1.3_Crunchy_Frog.tar.gz

# extract file
tar xzf brat-v1.3_Crunchy_Frog.tar.gz

cd brat-v1.3_Crunchy_Frog

# specify username and password after this command
./install.sh -u

# run using python2
python standalone.py

