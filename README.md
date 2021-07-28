# vk_message_parser
> vk_message_parser is an application written in Python that scrapes and downloads vk user's messages. Made it for my own purpose.

## Table of contents
* [General info](#general-info)
* [Technologies](#technologies)
* [Setup](#setup)
* [Usage](#Usage)
* [Status](#status)
* [Inspiration](#inspiration)
* [Contact](#contact)

## General info
The project is made for educational and scientific purposes.

## Technologies
* Selenium
* BeautifulSoup4

## Setup
Clone repo:\
`$ git clone https://github.com/ruhomor/vk_message_parser.git`\
Enter to project directory:\
`$ cd vk_message_parser`\
Create and activate virtualenv:\
`$ python3 -m venv vk_venv && source ./vk_venv/bin/activate`\
Install dependencies:\
`(vk_venv)$ pip3 install -r ./requirements.txt`

## Usage
Create a file with you "email_password.txt" with your credentials:\
`$ echo "your_phone your_password" > email_password.txt`\
Launch the spider:\
`$ scrapy crawl vk_spider`\
If a 2-factor authentification window appears type in auth-code into the shell

Never-To-Do list:
* Container?
* Fix receiver_id field()
* Save messages to DB
* Debugging

## Status
Project is: _dead_

## Inspiration
disgusting vk api that does not allow me to download my own messages

## Contact
Created by [@ruhomor] - feel free to contact me!
