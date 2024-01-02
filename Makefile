all: docs msg test 

#--os version specific setup instructions
devSetup: devSetup-$(shell uname -v | cut -f 2- -d '~' | cut -f 1 -d '-') protobuf

devSetup-18.04.1:
	${SH} sudo apt-get install -y libzmq3-dev
	${SH} sudo apt-get install -y python3-pip
	${SH} sudo pip3 install -y zmq
	${SH} sudo pip3 install -y twine

devSetup-22.04.1:
	${SH} sudo apt-get install -y libzmq3-dev
	${SH} sudo apt-get install -y python3-pip
	${SH} sudo pip3 install zmq
	${SH} sudo pip3 install twine
	${SH} sudo apt install -y texlive-latex-base
	${SH} sudo apt install -y texlive-full

docs: msg
	${SH} cd doc; make

buildPipPackage: msg
	${SH} python3 setup.py sdist bdist_wheel

uploadPackage: buildPipPackage
	${SH} twine upload dist/*

msg:
	${SH} protoc --proto_path=./ --python_out=./dividere/ MsgLib.proto

test: msg
	${SH} cd ./tests; protoc --proto_path=./ --python_out=. TestMsg.proto
        #--run tests w/ and w/o debug logging
	${SH} cd ./tests; ./uTests.py --verbose
	${SH} cd ./tests; ./uTests.py 

protobuf:
	${SH} mkdir temp/
	${SH} wget -O temp/v3.19.4.tar.gz https://github.com/protocolbuffers/protobuf/archive/refs/tags/v3.19.4.tar.gz
	${SH} cd temp; tar -zxvf v3.19.4.tar.gz
	${SH} cd temp/protobuf-3.19.4; ./autogen.sh; ./configure; make; 
	${SH} cd temp/protobuf-3.19.4; sudo make install; sudo ldconfig
	${SH} touch $@

clean:
	${RM} -rf build dist *.egg-info
	${RM} -rf ./dividere/__pycache__/
	${RM} -rf ./tests/__pycache__/
	${RM} -rf ./tests/TestMsg*py
	${RM} -rf ./dividere/MsgLib*py
	${SH} cd doc; make clean
	${RM} -rf ./temp/
	${SH} cd ./examples/; make clean
