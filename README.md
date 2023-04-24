# Panopto downloader

Simple utility to download in "batch mode" videos from an entire folder/course on panopto website. *Currently supports only the UNIVR sso login, but it is easily extensible.*

## Requirements

- Anaconda (reccomended for installation only)
- Google Chrome installed on your system, internally this script uses [Selenium](https://www.selenium.dev/documentation/) with the google chrome web driver.

## Installation and usage

To install the required dependencies: ``` conda env create -f environment.yaml ```

Basic usage: ``` python3 panopto-dl.py -url <FOLDER_URL> -u <GIA_USERNAME>``` 

I don't know who has had the smart idea to put double quotes in `<FOLDER_URL>` query string so remember to escape the url. In this way: `https://univr.cloud.panopto.eu/Panopto/Pages/Sessions/List.aspx#folderID=\"1bd8examplea2fa90\"`

To see all the options: ` python3 panopto-dl.py -h `

## Extensibility

Currently sso login types supported:

[X] Univr

## Disclaimer

Only for personal usage. This is not related in any way to panopto.


***<!-- This repository is mirrorred from a repository hosted on my own personal gitlab instance, it is possible that is not up-to-date to the last commit ->***



