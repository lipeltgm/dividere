all:

setup:
	${SH} sudo apt-get install -y protobuf-compiler

foo.proto:
	${SH} echo "syntax='proto3';" > $@
	${SH} echo 'message msg01 {' >> $@
	${SH} echo '  string field1=1;' >> $@
	${SH} echo '}' >> $@

%_pb2.py: %.proto
	${SH} protoc --proto_path=./ --python_out=./ $<


run: foo_pb2.py

clean:
	${RM} foo*

