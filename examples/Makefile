all:

setup:
	${SH} sudo apt-get install -y protobuf-compiler

clientMsgs.proto:
	${SH} echo "syntax='proto3';" > $@
	${SH} echo 'message Msg01 {' >> $@
	${SH} echo '  string field1=1;' >> $@
	${SH} echo '}' >> $@
	${SH} echo '' >> $@
	${SH} echo 'message Msg02 {' >> $@
	${SH} echo '  string field1=1;' >> $@
	${SH} echo '}' >> $@

%_pb2.py: %.proto
	${SH} protoc --proto_path=./ --python_out=./ $<


run: clientMsgs_pb2.py
	${SH} ./simplePubSub.py
	${SH} ./msgReactor.py

clean:
	${RM} clientMsgs* 
	${RM} -rf ./__pycache__/

