import logging
import traceback
import pathlib

from ftplib import FTP

logger = logging.getLogger('__main__')


class RadFTP:
    def __init__(self, server: str, user: str, passwd: str, directory: str = None) -> None:
        self.server = server
        self.user = user
        self.passwd = passwd
        self.directory = directory

    def do_action(self, function, pasv: bool = True, *args, **kwargs):
        with FTP(self.server) as self.ftp:
            self.ftp.login(user = self.user, passwd = self.passwd)
            self.ftp.set_pasv(pasv)
            if self.directory is not None:
                self.ftp.cwd(self.directory)
            return function(*args, **kwargs)

    def list_remote(self, filename: str = None) -> list:
        files = [] if filname is not None else ""
        try:
            if filename is not None:
                files = self.ftp.nlst(filename)
            else:
                files += self.ftp.nlst()
        except ftplib.error_perm as resp:
            if str(resp) == '550 No files found':
                logger.critical("No files in this directory")
            else:
                raise

        if filename is None:
            files = list(filter(None, files))

            for f in files:
                logger.debug(f)

        return files

    def download_file(self, remote_file: str, local_file: pathlib.Path | str):
        try:
            self.ftp.nlst(remote_file)
            with open(local_file, 'wb') as f:
                self.ftp.retrbinary('RETR ' + remote_file, f.write, 1024)

            logger.info(f"Downloaded {remote_file} as {local_file}")
        except Exception as e:
            if str(e) == '550 The system cannot find the file specified. ':
                logger.exception(e)

            elif str(e) == '421 Control connection timed out ':
                logger.exception(e)
            else:
                logger.exception(e)

    def download_files(self, file_map: list[tuple]):
        for f in file_map:
            remote, local = f
            self.do_ftp(self.download_file, remote, local)

