# Cat Monitoring  
- this project records video from 2 USB web cams (number can be modified by adding or removing camera configs) on motion and then optionally uploads them to your google drive
- **this projects does not rely on any kind of AI, only on changes in scene**
- there is no real added value to this project, only goal is to help with setting up correctly motion package and optionally adding google drive upload capability
- works on most of the linux distributions
- if you wish to upload to google drive, linux with gui is required
- requires preinstalled python (at least 3.6)
- recording is handled by motion package
- video uploading is handled by python script (using google API)
- TODO:
	- verify motion.conf (there has been upgrade of motion and its configuration possibilities)

Thank you motion (https://motion-project.github.io/) for motion detection package and NeuralNine (https://www.youtube.com/@NeuralNine) for provided example code on how to upload to google drive with python.

# Installation guide  

## Motion install:  
	sudo apt update && sudo apt upgrade -y 
	mkdir /home/$USER/CatMonitoring
 	mkdir /home/$USER/CatMonitoring/repository 
	mkdir /home/$USER/CatMonitoring/Videos
	cd /home/$USER/CatMonitoring/repository
	git clone https://github.com/DotaPie/cat-monitoring.git .
	str1='s/dotapie/' && str2='/g' 
	sed -i $str1$USER$str2 /home/$USER/CatMonitoring/repository/src/MotionConfs/motion.conf
	sed -i $str1$USER$str2 /home/$USER/CatMonitoring/repository/src/VideosToDriveSync.py
	sudo apt install motion -y
	sudo rm /etc/motion/*  
	sudo cp /home/$USER/CatMonitoring/repository/src/MotionConfs/* /etc/motion  
	sudo chmod a+rwx /home/$USER/CatMonitoring/Videos 

- if you want more or less USB web cams:
	- you need to add or remove /etc/motion/camx.conf and modify identifications inside, there is always one file per each camera
	- add or remove these files in /etc/motion/motion.conf (look for "Camera config files" section) and add or remove as you wish
- verify cam1 and cam2 /dev/v4l/by-path/* path in /etc/motion/cam1.conf and /etc/motion/cam1.conf
- /dev/v4l/by-path/* works even if your cams have the same ID, name might be different, usually ends with index0, just dont swap cams in their physical USB sockets
![Untitled](https://github.com/DotaPie/cat-monitoring/assets/56398587/7acddc0d-ca55-432d-940c-c03e672ccb53)


## Run motion (keep window opened):
	sudo motion

- if a motion is picked up by camera, video is recorded and stored into /home/$USER/CatMonitoring
- console window can be closed now, process is now running on background
- if you wish to upload videos automatically to google drive, more steps are required

## Allow google API on your account and generate credentials.json:  
- just watch and follow https://www.youtube.com/watch?v=fkWM7A-MxR0 ... 1:30 - 5:50 to obtain your credentials.json
- after you receive your credentials.json, put it to /home/$USER/CatMonitoring folder
 
## Python script install:  
	mkdir /home/$USER/CatMonitoring/CatMonitoringEnv  
	python3 -m venv /home/$USER/CatMonitoring/CatMonitoringEnv
	source /home/$USER/CatMonitoring/CatMonitoringEnv/bin/activate  
	python3 -m pip install --upgrade pip  
	python3 -m pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib  
  
## Run python script (keep window opened):  
	source /home/$USER/CatMonitoring/CatMonitoringEnv/bin/activate 
	python3 -u /home/$USER/CatMonitoring/repository/src/VideosToDriveSync.py

- authorize via web browser to your google account (you can follow https://www.youtube.com/watch?v=fkWM7A-MxR0 ... 19:48 - 22:00), this step is needed only once every 1-3 months when token expires, sometimes you can be prompted to sign in directly in console, but it never worked for me, i just rejected all cokies by pressing N and then Q for leaving and ten just copy provided URL that is now in the console and grant the access
