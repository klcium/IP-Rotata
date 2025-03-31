# IP Rotata

```
iprotata -h
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

# Basic usage
You may use `iprotata` or `rotata` to call the tool.

```
rotata setup --profile rotate --region eu-west-1

WARNING:root:No key pair was defined in parameters, using the latest created key: XXX-KEYNAME
The following VPC was successfully created: ['VPC-Rotata'] - vpc-06e42d5a44c3355a1                                                                                                           
The following Subnet was successfully created: ['SNET-Rotata'] - subnet-07d0c3f321d4728b9
The following IGW was successfully created: igw-01afa2201c52d6dea
The following Security Group was successfully created: sg-020c858eff35051d4
The following EC2 Instance was successfully created: i-0a0319d2f304abdd1 - 13.37.203.12
                                               
You can now run the following command:                                                        
sudo wg-quick up wgrotata                                                                     
                                                                                              
Instance is still setting up, 'ping 10.0.0.1' until something comes back. UwU                 
```

```
rotata delete --profile rotate --region eu-west-1
This function will clean all ressources within VPC with the ROTATA tag.
Continue [y/N]? y
Terminating instances: ['i-0a0319d2f304abdd1']

This may take some time...
----------
Instance: i-0a0319d2f304abdd1   Status:shutting-down
----------
Instance: i-0a0319d2f304abdd1   Status:shutting-down
----------
Instance: i-0a0319d2f304abdd1   Status:terminated
----------
Disassociating public IP allocation: eipassoc-03236e7b253b73ad2
Releasing public IP allocation: eipalloc-03236e7b253b73ad2
Releasing public IP allocation: eipalloc-03236e7b253b73ad2
Deleting igw-01afa2201c52d6dea
Deleting subnet-07d0c3f321d4728b9
Deleting vpc-06e42d5a44c3355a1
```

# What it is
IP Rotata is a CLI tool that boots up a Wireguard tunnel infrastructure on AWS and nicely crafts the local WG interface on the local computer.

When the power of ROTATA is invoked, your public IP changes without having to turn down your VPN tunnel.
All AWS regions are now supported.

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
- `Python 3.12` or newer
- `python3-pip`
- `Poetry` you can install it [here](https://python-poetry.org/docs/#installing-with-the-official-installer).
- `aws-cli` See [here](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) for installation guide
- `A working wireguard app`
- `An AWS account`
- This tool writes files at `/etc/wireguard/`, you must run it as root. A non-root option may be implemented later.
- Working $PATH ;)



# Installation and configuration
## Configure AWS
- Create a user with the following privileges
- Configure the AWS CLI access keys in your config file or env vars.
```
"ec2:DescribeAddresses",
"ec2:DescribeInstances",
"ec2:DescribeInternetGateways",
"ec2:DescribeNetworkInterfaces",
"ec2:DescribeSecurityGroups",
"ec2:DescribeSubnets",
"ec2:DescribeImages",
"ec2:DisassociateAddress",
"ec2:DetachInternetGateway"
"ec2:DetachInternetGateway"
"ec2:DeleteInternetGateway",
"ec2:DeleteNetworkInterface",
"ec2:DeleteSecurityGroup",
"ec2:DeleteVpc",
"ec2:ReleaseAddress",
"ec2:TerminateInstances"
```
**YOU NEED TO HAVE AT LEAST ONE EXISTING SSH KEY IN THE REGION IN WHICH YOU ARE LAUNCHING THE EC2**
`aws ec2 create-key-pair --key-name MyKeyPair --query "KeyMaterial" --output text > MyKeyPair.pem`

### Add keys locally
Then setup you AWS creds, i recommend you setting a profile instead of using the default one
`aws configure --profile $profile`
You may also have to do it as no-root if you don't want to bother sudo-ing when rotating your IP.

## Build and install Iprotata
```
git clone https://github.com/klcium/IP-Rotata
cd IP-Rotata
poetry build
sudo su
python3 -m venv venv && source ./venv/bin/activate
pip install ./dist/iprotata-0.1.0.tar.gz
iprotata -h
```


____

## Troubleshooting
### BOTO3 can't find my local creds
Boto3 is sensitive to local env changes, if you "venv" into python, this may bring new issues. 
Same for sudoing,  hence the recommendation to run 'sudo su' to prevent issues with boto3 not finding your creds. 

An other remediation could be to setup env variables with "AWS_CONFIG_FILE" and its paths. Havent tested it yet. Check [AWS Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-environment-variables) for more. 

If the issue persists, try specifying creds location to Boto3. Find more information about how boto3 will look for theme [here](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials)

E.G: 
`export AWS_CONFIG_FILE=/home/linux/.aws/config`
`export AWS_SHARED_CREDENTIALS_FILE=/home/linux/.aws/credentials`

then `iprotata list keys --profile $profile`

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
