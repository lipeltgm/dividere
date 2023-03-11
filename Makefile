all: 

#--os version specific setup instructions
setup: setup-$(shell uname -v | cut -f 2- -d '~' | cut -f 1 -d '-')

setup-18.04.1:
	${SH} sudo apt-get install -y libzmq3-dev
	${SH} sudo apt-get install -y python3-pip
	${SH} sudo pip3 install zmq
	${SH} sudo apt-get install libprotobuf-dev


setup-22.04.1:
	${SH} sudo apt-get install -y libzmq3-dev
	${SH} sudo apt-get install -y python3-pip
	${SH} sudo apt-get install -y protobuf-compiler
	${SH} sudo pip3 install zmq



