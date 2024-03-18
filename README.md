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

#### Filemaps

#### Usage

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

