# IP Rotata

```
    _____________________________________________________________________________________
    
    ::::::::::: :::::::::        :::::::::   :::::::: ::::::::::: ::: ::::::::::: :::     
        :+:     :+:    :+:       :+:    :+: :+:    :+:    :+:   :+: :+:   :+:   :+: :+:   
        +:+     +:+    +:+       +:+    +:+ +:+    +:+    +:+  +:+   +:+  +:+  +:+   +:+  
        +#+     +#++:++#+        +#++:++#:  +#+    +:+    +#+ +#++:++#++: +#+ +#++:++#++: 
        +#+     +#+              +#+    +#+ +#+    +#+    +#+ +#+     +#+ +#+ +#+     +#+ 
        #+#     #+#              #+#    #+# #+#    #+#    #+# #+#     #+# #+# #+#     #+# 
    ########### ###              ###    ###  ########     ### ###     ### ### ###     ### 
    _____________________________________________________________________________________
    
                        Rotata makes your IP ROTATE FASSTERRR  !!!

                                VERSION : 0.0.9

Actions:
  available actions

  {setup,rotate,list,delete}
    setup               Setup an AWS environnement
    rotate              Rotate your IP
    list                List ressources of AWS
    delete              Delete resources in a region with Rotata tag
  
```

# What it is
IP Rotata is a CLI tool that boots up a Wireguard tunnel infrastructure on AWS and nicely crafts the local WG interface on the local computer.

When the power of ROTATA is invoked, your public IP changes without having to turn down your VPN tunnel.

## Hmm very sussy, what's the trick ?
 The tools attaches two IPs on the AWS EC2. The wireguard listens on the two IPs, but if you authenticate on the second one, your packets will come out on the main one.
 The rotata functions simple associate a new IP to the primary interface and free the previous one.


## Why should i use it
- Don't, you idiot
- I did it myself, vewy nice
- Red team operations, you can set a local cron to call the rotate function.

# Technical information
This code was developped on Kali linux (Debian based), if you encounter any issue with other distros, do not contact me because i don't care.

## Requirements
- `Linux`
- `Python 3.10` or newer
- `Poetry` you can install it [here](https://python-poetry.org/docs/#installing-with-the-official-installer).
- `A working wireguard app`
- `An AWS account`
- `aws-cli` (Optionnal but highly recommended) See [here](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) for installation guide
- `python3-pip`
- This tool writes files at `/etc/wireguard/`, you must run it as root. A non-root option may be implemented later.

# Installation and configuration

*THIS INSTALLATION IS FOR LINUX ONLY*

The installation is a little bit tricky. I recommend you to install it in two venv, one as Root, and one with your low privileged user.
The second one is optional, it's just to avoid having to sudo 

First install local dependencies

```
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

## Install Iprotata
### From release
```
sudo su
pip install iprotata-0.1.0.tar.gz
```

### From source 
```
git clone {THIS_URL}
cd IP-Rotata
poetry build
cd ./dist
sudo su
pip install iprotata-0.1.0.tar.gz
```

### Option: use venv:
Check the "I don't want your sudo su, i want virtual envs >:(" troubleshooting section

## Configure AWS
Access to the AWS console and create a user.
The following AWS are required for the tool to work:
```
"ec2:DescribeAddresses",
"ec2:DescribeInstances",
"ec2:DescribeInternetGateways",
"ec2:DescribeNetworkInterfaces",
"ec2:DescribeSecurityGroups",
"ec2:DescribeSubnets",
"ec2:DisassociateAddress",
"ec2:DetachInternetGateway"
"ec2:DetachInternetGateway"
"ec2:DeleteInternetGateway",
"ec2:DeleteNetworkInterface",
"ec2:DeleteSecurityGroup",
"ec2:DeleteVpc",
"ec2:ReleaseAddress",
"ec2:TerminateInstances",
```
These rules are based on CloudTrail activities, i did not tested them. Ping me if some are missing.
To ensure minimum privileges, you can add conditions to ensure that they only apply on ressources owned by the user.

### Add keys locally
Then setup you AWS creds, i recommend you setting a profile instead of using the default one
`aws configure --profile rotata`
You may also have to do it as no-root if you don't want to bother sudo-ing when rotating your IP.

## Troubleshooting
### BOTO3 can't find my local creds
Boto3 is sensitive to local env changes, if you "venv" into python, this may bring new issues. 
Same for sudoing,  hence the recommendation to run 'sudo su' to prevent issues with boto3 not finding your creds. 

An other remediation could be to setup env variables with "AWS_CONFIG_FILE" and its paths. Havent tested it yet. Check [AWS Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-environment-variables) for more. 

If the issue persists, try specifying creds location to Boto3. Find more information about how boto3 will look for theme [here](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials)

E.G: 
`export AWS_CONFIG_FILE=/home/linux/.aws/config`

`export AWS_SHARED_CREDENTIALS_FILE=/home/linux/.aws/credentials`

then `sudo -E iprotata list keys --profile rotata`

### I don't want to install aws-cli tool
Just create the dir with the config files in.
```
mkdir ~/.aws/

echo "[rotata]
aws_access_key_id=foo
aws_secret_access_key=bar" >> ~/.aws/credentials

echo "[profile rotata]
region = eu-west-3" >> ~/.aws/config
```
Remember that if you run both as root and non root, to setup the config file in the ~/ directory of each user.

### I don't want your sudo su, i want virtual envs >:(
Ok fine, here is the full install on how you do it .
First, setup your creds and conf file `~/.aws/credentials` and  `~/.aws/config`.
Then, run the following command. Don't foret the `sudo -E iprotata` option when you sudo
```
git clone $URL
cd IP-Rotata
poetry build
cd ./dist
python3 -m venv venv
source venv/bin/activate
umask 022
sudo pip install iprotata-0.1.0.tar.gz 
export AWS_CONFIG_FILE=/home/$(whoami)/.aws/config
export AWS_SHARED_CREDENTIALS_FILE=/home/$(whoami)/.aws/credentials
sudo -E iprotata list keys --profile default
```

# How to use
Don't use it UwU (may do this part later, if boto3 can't find you profile, it's probably because you sudo-ed your iprotata call. Do `sudo su` first, then run the tool.)

## Details
You may find a detailed presentation in this [blogpost](https://www.youtube.com/watch?v=xvFZjo5PgG0) i wrote.

## Supported regions
- ap-south-1
- ca-central-1
- eu-north-1
- eu-west-3
- eu-west-1
- ap-northeast-1
- sa-east-1
- ap-southeast-1
- us-east-1
- us-east-2


# Other
## Improvements
- List EC2 with the two pubip and instanceid, useful when multiple VPC
- Working logging functions
- Refactor code
- Working dry_run
- change the rotata name filter for vpc by a tag filter
- Setup arg to avoid setting up an EC2, gain time for debug
- Maybe make a create keygen function
- Make a configuration file for variables such as wg path etc etc
- Make something out of that DB ??

## Retex
- Maybe next time use terraform to setup the resources
- Be more rigorous with the \' and \" naming
- Same for the functions names
- Should have done a state of the art before going in, still happy i did it.
- Check what's best to use between boto3 resources and boto3 client.
- Logging is like unit tests, you either do them day 1 or you never will.
- stop being lazy with "print('UwU')" and use debugger instead
