# radautopy

### Requirements

`radautopy` assumes that `ffmpeg` and `rclone` is installed on your system. See [more about rclone](https://rclone.org/). `radautopy` has been tested against a NextCloud provider using `rclone`.

### Installation

Install dependencies:

```
$ sudo apt install rclone ffmpeg -y
```

Clone this repo and install via pip:

```
$ git clone https://github.com/maxtimbo/radautopy.git
$ cd radautopy
$ pip install .
```


### Initial Setup

`radautopy` ships with no configuration files by default. You can choose to write them by hand, or use `radautopy modify --[ftp | rclone | http] {some_new_config}.json edit`. For example:

`$ radautopy modify --ftp MyCoolShow.json edit`

This will create the directories for configs as well as logs at `~/radautopy/config` and `~/radautopy/logs`.

Initially, a global email config will be created at `~/radautopy/config/email.json`. 

> [!WARNING]  
> All passwords are stored in plaintext in the users home directory.

Once the initial email config is built, you will be prompted to create the show config. This will be different for each type `[ftp | rclone | http]`. See below for configuration templates.

Once the initial configuration is done, you can modify it either using the cli tool or you can edit the json file directly.

> [!WARNING]
> I will need to update these instructions. They are incorrect.


#### Filemaps

> [!TIP]
> Use `radauto-config modify --[ftp | rclone | http] {CONFIG.json} --filemap` to create the filemap config.

You can choose one of `Individual track edit | Filemap wizard | Quick Show Wizard`.

If you have a show that follows a pattern of hour/segment, use the `Quick Show Wizard`. The `Filemap Wizard` can be used if you just need to iterate from 0 to n or from 1 to n. Once you have a filemap and need to make any adjustments, use either `Filemap Wizard` to iterate all files in the `filemap` or use `Individual track edit` to choose just one track to edit.

#### Usage

`radautopy` has been designed with crontab in mind. You can also do one-offs with the verbose flag to make sure everything is working properly. Otherwise, there will be no output when any given config is ran.

To run a config, do:

```
$ radautopy run {CONFIG_FILE.json} [ftp | rclone | rclone]
```

If everything is configured correctly, recipients should recieve an email with what was downloaded and where the files were moved to. You can also check the logs in `~/radautopy/logs`.

Once the config is confirmed to be working correctly, you can add a cronjob. Here's an example cron entry:

```
00 4 * * 1-5 /home/myuser/.local/bin/radautopy run myshow.json ftp
```

This will run the config `myshow.json` FTP job at 4am every Monday through Friday.

### Config Templates

#### Global Email Config

```
{
  "email": {
    "sender": str,
    "subject": str,
    "server": str,
    "port": int,
    "username": str,
    "password": str,
    "reply_to": str,
    "recipient": str | list,
    "header": str,
    "footer": str
  }
}
```

#### Example FTP Config

```
{
  "FTP": {
    "server": str,
    "username": str,
    "password": str,
    "pasv": boolean,
    "directory": str
  }
}
```

#### Example rclone Config

```
{
  "cloud": {
    "server": str,
    "directory": str
  }
}
```


#### Example HTTP Config

> [!NOTE]
> HTTP has not yet been implemented

```
{
  "http": {
    "url": str
  }
}
```

##### Silence Settings

These settings are for the split silence function.

> [!NOTE]
> Not yet implemented

```
{
  "silence": {
    "threshold": -60,
    "duration": 15
  }
}
```


#### Directories

> [!NOTE]
> All configs require these directories, even if not all directories are used.

```
{
  "dirs": {
    "download_dir": "~/radautopy/download",
    "export_dir": "~/radautopy/export",
    "audio_tmp": "~/radautopy/audio_tmp"
  }
}
```

#### Filemap

```
{
  "filemap": [
    {
      "input_file": "input.mp3",
      "output_file": "output.wav",
      "artist": "Artist Metadata",
      "title": "Title Metadata"
    },
  ]
}
```

