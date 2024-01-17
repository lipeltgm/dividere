all: 

video.mp4:
	${SH} yt-dlp -f mp4 https://www.youtube.com/watch?v=K_7k3fnxPq0 -o $@

setup: 
	${SH} sudo apt-get install -y protobuf-compiler

configYolo: yolov3.cfg yolov3.weights coco.data coco.names

yolov3.cfg:
	${SH} wget https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg

yolov3.weights:
	${SH} wget https://pjreddie.com/media/files/yolov3.weights

coco.data:
	${SH} wget https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/coco.data
	${SH} mkdir -p data/
	${SH} mv $@ data/

coco.names:
	${SH} wget https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names
	${SH} mkdir -p data/
	${SH} mv $@ data/

clientMsgs.proto:
	${SH} echo "syntax='proto3';" > $@
	${SH} echo 'message Msg01 {' >> $@
	${SH} echo '  string field1=1;' >> $@
	${SH} echo '}' >> $@
	${SH} echo '' >> $@
	${SH} echo 'message Msg02 {' >> $@
	${SH} echo '  string field1=1;' >> $@
	${SH} echo '}' >> $@
	${SH} echo 'message Msg03 {' >> $@
	${SH} echo '  int64 field1=1;' >> $@
	${SH} echo '  bool isPrime=2;' >> $@
	${SH} echo '}' >> $@
	${SH} echo 'message ImageMsg {' >> $@
	${SH} echo '  string fileName=1;' >> $@
	${SH} echo '  bytes image=2;' >> $@
	${SH} echo '}' >> $@
	${SH} echo 'message BoundingBox {' >> $@
	${SH} echo '  int32 x=1;' >> $@
	${SH} echo '  int32 y=2;' >> $@
	${SH} echo '  int32 width=3;' >> $@
	${SH} echo '  int32 height=4;' >> $@
	${SH} echo '}' >> $@
	${SH} echo 'message Detection {' >> $@
	${SH} echo '  string category=1;' >> $@
	${SH} echo '  float score=2;' >> $@
	${SH} echo '  BoundingBox bbox=3;' >> $@
	${SH} echo '}' >> $@
	${SH} echo 'message ImageReply {' >> $@
	${SH} echo '  repeated Detection detection=1;' >> $@
	${SH} echo '}' >> $@

%_pb2.py: %.proto
	${SH} protoc --proto_path=./ --python_out=./ $<

run: clientMsgs_pb2.py 
	${SH} ./simplePubSub.py
	${SH} ./msgReactor.py
	${SH} ./yoloEx.py

clean:
	${RM} clientMsgs* 
	${RM} -rf ./__pycache__/
	${RM} *.jpg

