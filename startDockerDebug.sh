docker build -t obu:debug  --target debug .
echo "Time to run the debugger!!"
docker run --rm -it -p 5678:5678 --name debugger --network=host -v ${PWD}/logs:/usr/src/app/logs:rw -v ${PWD}/certs:/usr/src/app/certs:ro -v ${PWD}/sslkeylog:/usr/src/app/sslkeylog:rw obu:debug 
