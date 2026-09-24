# radautopy

### Radautopy Now Uses Docker
This new system uses docker to containerize everything. I've moved to using APScheduler instead of cron and built a simple web app for configuration. I've added [rclone-web](https://github.com/rclone/rclone-web) to manage rclone as well. Most everything can be setup in rclone-web and then automated using radautopy. This also moves files, renames them, and adds metadata with the scott header (Wide Orbit). 

### Requirements

You just need Docker and Docker Compose

### Installation

Clone this repo and configure `docker-compose.yml` and `.env`.

To setup, some key changes to docker-compose file must be made.

The `volumes` section has `radautopy-data` setup for each service and that must be the same for all. Any other volumes for export should also be configured in a similar fashion across all containers.

```
services:
  scheduler:
    volumes:
      - radautopy-data:/data
  web:
    volumes:
      - radautopy-data:/data
  rclone-gui:
    volumes:
      - radautopy-data:/data

volumes:
  radautopy-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /home/tfinley/radautopy
```

You can set different ports for the web-gui:

```
  web:
    ports:
      - "8000:8000"
```

Copy the `.env.sample` to `.env` and fill out the user/password for rclone. This is the only time this needs to be configured.

Then just run `docker compose up -d --build` to build the containers and start the app. Point a web browser to `[computer.ip]:[web-port]` or `localhost:[web-port]` if you're running on the same machine.


### Initial Setup
#### The following is legacy, but gives a good idea of how the web gui works.
#### To-Do: Update this section.

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

`server` is the name of a remote in rclone's config. In Docker, remotes are managed through the bundled [rclone web GUI](https://github.com/rclone/rclone-web) (the **rclone Remotes** link in the web UI, port 5522). Set `RCLONE_GUI_PASS` (and optionally `RCLONE_GUI_USER`) in a `.env` next to `docker-compose.yml` first.

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
    "api_key": str
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

