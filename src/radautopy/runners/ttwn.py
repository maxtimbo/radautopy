
from ..utils.config import ROOT_DIR
from ..utils.utilities import handle_status_code, make_dir

def perform_ttwn(config, mailer, email_bool, remote):
    affiliate_dir = make_dir(Path(ROOT_DIR, config.ttwn['affiliate']))
    timestamp = remote.probe_timestamp(affiliate_dir)
    if handle_status_code(remote.manifest.status_code):
        url = remote.get_manifest(timestamp)



