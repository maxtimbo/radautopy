


def compare_hashes(new_audio, old_audio) -> tuple(bool, str):
    new_hash = new_audio.analyse()
    old_hash = old_audio.analyse()
    new_audio.move_copy()
    if new_hash == old_hash:
        return (False, f'{new_audio.input_file} not updated')
    else:
        return (True, f'{new_audio.input_file} updated')

