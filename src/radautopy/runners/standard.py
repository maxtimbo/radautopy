from ..utils.audio import AudioFile

def perform_standard(config, mailer, email_bool, remote):
    config.concat_directories_filemap()
    downloads = [(x['input_file'].name, x['input_file']) for x in config.filemap]
    try:
        remote.download_files(downloads)
        for i, o in downloads:
            mailer.append_table_data('downloaded', i)
    except:
        mailer.p('Download unsuccessful')
    for track in config.filemap:
        audio = AudioFile(track['input_file'], track['output_file'])
        audio.apply_metadata(artist=track['artist'], title=track['title'], apply_input=True)
        try:
            audio.move()
            mailer.append_table_data('moved to', track['output_file'])
        except:
            mailer.p('move unsuccessful')

    mailer.concat_table()
    if email_bool: mailer.send_mail()

