# Panopto downloader

Simple utility to download in "bastch mode" videos from an entire folder/course on panopto. Currently supports only the UNIVR sso login, but is easily extensible.

## Requirements

- Anaconda (raccomended for installation only)
- Google Chrome installed on your system, internally this script uses [Selenium](https://www.selenium.dev/documentation/) with the google chrtome web driver.

## Installation and usage

``` conda env create -f environment.yaml ``` to install the required dependecies.

Basic usage: ``` python3 panopto-dl.py -url <FOLDER_URL> -u <GIA_USERNAME>``` 

I don't know who has had the smart idea to put double quotes in `<FOLDER_URL>` query string so remeember to escape the url. In this way: `https://univr.cloud.panopto.eu/Panopto/Pages/Sessions/List.aspx#folderID=\"1bd8examplea2fa90\"`


To see all the options: ` python3 panopto-dl.py -h `

## Extensibility

Currently sso login types supported:

[X] Univr


***<!-- This repository is mirrorred from my own personal gitlab instance, it is possible tha is not update ->***


