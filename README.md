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

Installing creates two cli tools. `radauto-config` and `radautopy`.  
`radauto-config` will allow you to quckly create configs for shows and other jobs. The initial run will create a new directory tree in your user home:

```
~/radautopy/
├── audio_tmp
├── config
├── download
├── export
└── log
```

Using `radauto-config create MyCoolShow.json [job type, see below]` will create an `email.json` global email config file as well as `MyCoolShow.json`. Follow the prompts and fill in all the information.

> [!WARNING]
> All passwords are stored plaintext. Please keep this in mind when using this script.

> [!NOTE]
> The following job types have been added:
> - ftp
> - sftp
> - rclone
> - rss
> - ttwn

> [!TIP]
> `rclone` job type must be setup using rclone prior to running this script

Once created, you can use `radauto-config list-configs` to show a list of configs in `~/radautopy/configs`. You can also use `radauto-config modify [job_name.json]` to alter an existing config (do not include a job file to modify the global email config). You can also use `radauto-config validate [job_name.json]` to validate an existing job (once again, leave out the job file to validate the email config).

Finally, if you set the cron settings for your job, you can use `radauto-config set-cronjob [job_name.json]` to create a cron entry.

All json files can be edited using your favorite text editor. Just be sure that all entries are still in place following the examples below. You can add or remove any `"email": {}` entries to a job as these are email setting overrides.

#### Filemaps

During the job configuration prompts, you will be presented with three options for filemap creation:

- individual track edit
 - Allows you to select an idividual track to edit
- filemap wizard
 - Add filemaps one by one
- quick show wizard
 - quickly create an entire show filemap following the prompts

#### Usage

You can test your config by using `radautopy [job_name.json] [job_type] {optional_extra_args}`  
If you created a cron entry, it will run automatically at the specified time.

You can check the log output of all jobs in `~/radautopy/log/radautopy.log`

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

> [!NOTE]
> ```
> "email: {
>   "recipient":
> }
> ```
> can either be a single address: `"eaxample@test.com"` or a list:
> `["example1@test.com", "example2@test.com"]`

> [!TIP]
> You can add any of these email settings to a job config to override the global defaults. For example:
> 
> ```
> {
>   "job": {
>     "job_name": "My Cool job",
>     "description": "Daily show thats cool",
>     "job_type": "cloud",
>     "cron_expression": "00 04 * * *"
>   },
>   "cloud": {
>     "server": "CShow",
>     "directory": ""
>   },
>   "dirs": {
>     "download_dir": "/path/to/download",
>     "export_dir": "/path/to/export",
>     "audio_tmp": "/path/to/tmp"
>   },
>   "filemap": [
>     {
>       "input_file": "audio.mp3",
>       "output_file": "audio.wav",
>       "artist": "Cool Show {now}",
>       "title": "{month}{day}{year}-{week}"
>     }
>   ],
>   "email": {
>     "sender": "OVERIDE SENDER",
>     "subject": "OVERRIDE SUBJECT",
>     "recipient": ["override@r1.com", "override2@r2.com"]
>   }
> }
> ```

#### Job Metadata
```
{
  "job": {
    "job_name": str,
    "description": str,
    "job_type": str,
    "cron_expression": str,
    "job_runner": str,
    "extra_args": "",
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

#### Example SFTP Config

```
{
  "SFTP": {
    "server": str,
    "username": str,
    "password": str,
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

#### TTWN Config
```
{
  "ttwn": {
    "url": str,
    "affiliate": str,
    "username": str,
    "password": str
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

