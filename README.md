# radautopy

radautopy automates radio show delivery. It downloads audio from FTP, SFTP, rclone remotes, RSS feeds or TTWN, converts and renames the files, adds Scott (cart chunk) metadata for WideOrbit, exports them, and emails a report.

### Radautopy Now Uses Docker
Everything runs in containers. Jobs are scheduled with APScheduler instead of cron, and a simple web app handles job configuration. [rclone-web](https://github.com/rclone/rclone-web) is bundled for managing rclone remotes, which radautopy can then download from on a schedule.

### Requirements

Docker and Docker Compose.

### Installation

1. Clone this repo.

2. Create the data directory on the host. It holds the database, logs and working audio, and must exist before the containers start. All containers run as uid 1000, so that user needs write access:

    ```
    mkdir -p /path/to/radautopy
    sudo chown 1000:1000 /path/to/radautopy
    ```

3. In `docker-compose.yml`, set `device` to that directory. Every service mounts the same `radautopy-data` volume at `/data`:

    ```
    volumes:
      radautopy-data:
        driver: local
        driver_opts:
          type: none
          o: bind
          device: /path/to/radautopy
    ```

4. Mount any export destinations (for example the WideOrbit import share) into both `scheduler` and `web`. A job's `export_dir` must use the **container** path, not the host path:

    ```
    services:
      scheduler:
        volumes:
          - radautopy-data:/data
          - /mnt/wideorbit/import:/export
      web:
        volumes:
          - radautopy-data:/data
          - /mnt/wideorbit/import:/export
    ```

    With this mount, a job would use `"export_dir": "/export"`.

5. Copy `.env.sample` to `.env` and set `RCLONE_GUI_PASS` (and optionally `RCLONE_GUI_USER`, which defaults to `admin`). Compose refuses to start until the password is set. See [Timezone](#timezone) for the optional `TZ` setting.

6. Build and start:

    ```
    docker compose up -d --build
    ```

    Then browse to `http://<server-ip>:8000`, or `http://localhost:8000` on the same machine.

#### Ports

| Port | Service |
| --- | --- |
| 8000 | radautopy web UI |
| 5522 | rclone web GUI |
| 5533 | rclone API (the GUI calls it directly from the browser) |

All three must be reachable from your browser. If you change the host side of the rclone ports (for example `"9000:5522"`), also set `RCLONE_GUI_PORT` and `RCLONE_API_PORT` under the `web` service's `environment` so the **rclone Remotes** page points to the right place.

> [!WARNING]
> The web UI has no login, and all passwords are stored in plain text. The **rclone Remotes** page logs straight into the rclone GUI, which can read everything under `/data`. Only expose these ports on a trusted network.

#### Timezone

All containers use the host's timezone by default (the compose file mounts the host's `/etc/localtime`). To use a different timezone, set `TZ` in `.env`:

```
TZ=America/New_York
```

Cron expressions, next run times and log timestamps all use this timezone.

#### Scheduling Jobs

Each job's **Cron Expression** uses standard crontab syntax (`minute hour day month weekday`). The job form includes a helper that shows a plain-English description, the next five run times and common presets as you type, plus a field reference. The job list shows the same description under each expression.

- Day of week follows crontab: `0` and `7` are Sunday, `1-5` is Monday through Friday. Names such as `mon-fri` also work.
- Leave the expression blank to only run the job manually.
- Untick **Enabled** (on the job list or the job form) to pause scheduled runs without deleting the job. A disabled job can still be run with the **Run** button.
- The scheduler checks for changes every 60 seconds, so there is no need to restart it after editing a job.

#### rclone Remotes

The **rclone Remotes** page embeds the rclone web GUI, already logged in. Use it to create the remotes that `cloud` jobs download from; the remote's name goes in the job's `server` field. The page also has a link to open the GUI in its own tab.

#### Updating

```
git pull
docker compose up -d --build
```

#### Logs

Job output goes to `<data dir>/log/radautopy.log` and scheduler output to `<data dir>/log/radautopy-scheduler.log`. Both can also be viewed on the web UI's Logs page.

#### Migrating from JSON configs

Configs are now stored in SQLite (`<data dir>/radautopy.db`). To import configs from an older install, copy the `.json` files into `<data dir>/config` and run:

```
docker compose exec web radautopy-json-to-sqlite
```

### Command Line Tools

> [!NOTE]
> This section is from the pre-Docker version. The web UI covers the same steps, and the CLI still works inside the containers, for example `docker compose exec web radauto-config list-configs`.

The package includes two CLI tools: `radauto-config` and `radautopy`.
`radauto-config` lets you quickly create configs for shows and other jobs.

Using `radauto-config create MyCoolShow.json [job type, see below]` will create the global email config as well as `MyCoolShow.json`. Follow the prompts and fill in all the information.

> [!NOTE]
> The following job types are available:
> - ftp
> - sftp
> - cloud (rclone)
> - rss
> - ttwn

> [!TIP]
> The rclone remote for a `cloud` job must exist before the job runs. Create it in the rclone web GUI first.

Once created, use `radauto-config list-configs` to list saved configs. Use `radauto-config modify [job_name.json]` to alter an existing config (leave out the job name to modify the global email config), and `radauto-config validate [job_name.json]` to validate a job (again, leave out the job name to validate the email config).

Jobs run on the schedule set in their `cron_expression`. Set `"enabled": false` in the job metadata (or untick Enabled in the web UI) to stop scheduled runs without deleting the job; a disabled job can still be run manually. Jobs without an `enabled` key are treated as enabled. The scheduler container picks up changes automatically, so `radauto-config set-cronjob` is not needed under Docker.

You can add or remove any `"email": {}` entries in a job, as these override the global email settings.

#### Filemaps

During job configuration, you will be offered three ways to build a filemap:

- individual track edit
  - Select an individual track to edit
- filemap wizard
  - Add filemaps one by one
- quick show wizard
  - Quickly create an entire show filemap by following the prompts

#### Usage

You can test a job with `radautopy [job_name.json] [job_runner] {optional_extra_args}`, or with the Run button in the web UI.

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
> "email": {
>   "recipient":
> }
> ```
> can either be a single address: `"example@test.com"` or a list:
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
>     "download_dir": "/data/download",
>     "export_dir": "/export",
>     "audio_tmp": "/data/audio_tmp"
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
>     "sender": "OVERRIDE SENDER",
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
    "enabled": boolean
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

`server` is the name of a remote in rclone's config. Remotes are managed in the bundled [rclone web GUI](https://github.com/rclone/rclone-web), opened from the **rclone Remotes** page in the web UI. The job type for rclone is `cloud`.

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
> All configs require these directories, even if not all directories are used. The defaults below are container paths.

```
{
  "dirs": {
    "download_dir": "/data/download",
    "export_dir": "/data/export",
    "audio_tmp": "/data/audio_tmp"
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
```

