all:

setup:
	${SH} sudo apt-get install -y protobuf-compiler

clientMsgs.proto:
	${SH} echo "syntax='proto3';" > $@
	${SH} echo 'message msg01 {' >> $@
	${SH} echo '  string field1=1;' >> $@
	${SH} echo '}' >> $@

%_pb2.py: %.proto
	${SH} protoc --proto_path=./ --python_out=./ $<


run: clientMsgs_pb2.py
	${SH} ./simplePubSub.py

clean:
	${RM} clientMsgs*

