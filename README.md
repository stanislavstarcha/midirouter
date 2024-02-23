# run midirouter on raspeberry

```
sudo apt-get install libopenblas-dev

cd /opt
sudo git clone https://github.com/stanislavstarcha/midirouter.git
cd midirouter
sudo pip install -r requirements.txt
```

sudo vim /lib/systemd/system/midirouter.service

```
[Unit]
Description=Midi Router
After=multi-user.target

[Service]
Type=idle
ExecStart=/usr/bin/python /opt/midirouter/src/route.py --config=mpd.full.json

[Install]
WantedBy=multi-user.target
```

```
sudo chmod 644 /lib/systemd/system/midirouter.service
sudo systemctl daemon-reload
sudo systemctl enable midirouter.service
```