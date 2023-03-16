all: msg test

#--os version specific setup instructions
devSetup: devSetup-$(shell uname -v | cut -f 2- -d '~' | cut -f 1 -d '-')

devSetup-18.04.1:
	${SH} sudo apt-get install -y libzmq3-dev
	${SH} sudo apt-get install -y python3-pip
	${SH} sudo pip3 install -y zmq
	${SH} sudo apt-get install -y libprotobuf-dev
	${SH} sudo pip3 install -y twine


devSetup-22.04.1:
	${SH} sudo apt-get install -y libzmq3-dev
	${SH} sudo apt-get install -y python3-pip
	${SH} sudo apt-get install -y protobuf-compiler
	${SH} sudo pip3 install -y zmq
	${SH} sudo pip3 install -y twine

buildPipPackage:
	${SH} python3 setup.py sdist bdist_wheel

uploadPackage: buildPipPackage
	${SH} twine upload dist/*

msg:
	${SH} protoc --proto_path=./ --python_out=./dividere/ MsgLib.proto

test: msg
	${SH} cd ./tests; protoc --proto_path=./ --python_out=. TestMsg.proto
#	${SH} cd ./tests; ./uTests.py --verbose
	${SH} cd ./tests; ./uTests.py 


clean:
	${RM} -rf build dist *.egg-info
	${RM} -rf ./dividere/__pycache__/
	${RM} -rf ./tests/__pycache__/
	${RM} -rf ./tests/TestMsg*py
	${RM} -rf ./dividere/MsgLib*py


