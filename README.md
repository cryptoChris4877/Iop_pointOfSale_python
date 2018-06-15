# Iop_pointOfSale_python
Very rough code for IoP point of sale system. currently working, but could use some work.

To use you must have an IoP node on the target computer. when starting the IoP node you must specify a rpc username and password.

edit the main.py file setting up the server url

serverURL = 'http://<user>:<pass>@127.0.0.1:8337' 

where user is the user name passed to the iop node and password is passed to the iop node ( user and pass that you passed to the IoP node) 

also set up your receiving address to a receiving address on you IoP wallet.

self.out_address='<your receive address>' # receive address

Note: Make sure you run the IoP node before starting the Point of Sale code or it will not be able to communicate with the blockchain

now run main.py and you should be greated with the point of sale User Interface.
