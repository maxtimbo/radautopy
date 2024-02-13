# radautopy

### Requirements

`radautopy` assumes that `ffmpeg` and `rclone` is installed on your system. See [more about rclone](https://rclone.org/). `radautopy` has been tested against a NextCloud provider using `rclone`.

### Installation

Install dependencies:

```
$ sudo apt install rclone ffmpeg -y

```

Install `radautopy`:

`pip install radautopy`


### Initial Setup

`radautopy` ships with no configuration files by default. You can choose to write them by hand, or use `radautopy modify --[ftp | rclone | http] {some_new_config}.json edit`. For example:

`$ radautopy modify --ftp MyCoolShow.json edit`

This will create the directories for configs as well as logs at `~/radautopy/config` and `~/radautopy/logs`.

Initially, a global email config will be created at `~/radautopy/config/email.json`. 

> [!WARNING]  
> All passwords are stored in plaintext in the users home directory.

Once the initial email config is built, you will be prompted to create the show config. This will be different for each type `[ftp | rclone | http]`. See below for configuration templates.

Once the initial configuration is done, you can modify it either using the cli tool or you can edit the json file directly.


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

These settings are the split silence function.

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
		}
	]
}


