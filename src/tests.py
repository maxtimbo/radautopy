#from radauto_mail import RadMail
from pathlib import Path
import defaults
import radftp.defaults
from utils.config import ConfigJSON
from time import sleep

#config = radftp.defaults.DEFAULT_CONFIG | defaults.DEFAULT_CONFIG | defaults.DEFAULT_FILEMAP
#
#confile = Path('test.json')
#conf = ConfigJSON(confile, config)

somebool = True

sleep(10) if somebool else print('false')

#   print(config)
#   for key, value in config.items():
#       print(key)



#from utils.cmdlts import BaseArgs
#import radftp.defaults
#
#def runner(blah:str, blah2: int):
#    print('runner')
#    print(blah)
#    print(blah2)
#
#def validate():
#    print('validate')
#
#test = BaseArgs(radftp.defaults.args_dict, runner, validate, blah="test", blah2=45)
#print(test.email)
#import defaults
#from utils.config import RadConfig
#
#DEFAULT_CONFIG = defaults.DEFAULT_CONFIG
#
#conf_file = Path('~/testconf.ini').expanduser()
#
#config = RadConfig(DEFAULT_CONFIG, conf_file)
#config.set_interactive()
#print(config.email_passwd)
#print(config.dirs)
#print(config.download_dir)
#print(config.audio_tmp)

#from utils.ftp import RadFTP
##from radauto_config import RadConfig
##from radauto_audio import AudioFile
##import radauto_settings
#
#base_dir = Path("/space/es1/TrafficCuts")
#server = "ftp.gregbeharrell.com"
#user = "WFXH-FM"
#passwd = "8tL&TA%y+cAU&p9C"
#directory = ""
#
#ftp = RadFTP(server, user, passwd)
#list_of = [("test", "test"), ("testd", "teds")]
#ftp.download_files(list_of)
#files = ftp.do_action(ftp.list_remote)
#
#print(files)
#dl = "Friday_01052024_Hour1_Segment5.mp3"
#local = Path(base_dir, dl)
#ftp.do_action(ftp.download_file, dl, local)

#config = RadConfig("test")
#print(config.log_file)
#base_dir = Path("/space/es1/TrafficCuts")
#audio = AudioFile(Path(base_dir, "NEW122.wav"), Path(base_dir, "TestOut"))
##print(audio.output_file)
#split = audio.split_silence()
#title = "My Title"
#artist = "My Artist"
#for i, c in enumerate(split):
#    c.apply_metadata(artist, title + str(i + 1), apply_today=True)
#    c.convert()
#    c.analyse()
#cuts = split.split_audio("Test")
#new_audio = split.split_audio()
#audio.move_copy(apply_input=True)
#audio.move_copy("/space/es1/this_does_not_exist")
#audio.convert()
#audio.apply_metadata("testArtist", "testTitle")

#test = RadMail("Rad Fromname", "Test", "tfinley@dbcradio.com", "tim.finley24@gmail.com", "smtp.gmail.com", 465, "timmystowers42@gmail.com", "tvspypyybapurrpu")
##
##test.h1("test Header")
##test.h2("test2")
#test.h3("test3")
#test.h4("test4")
#test.h5("test5")
#test.p("here is a longer string")
#test.p("test2")
#test.add_footer("Please do not reply to this email. Please contact <a href=\"mailto:tfinley@dbcradio.com\">tfinley@dbcradio.com</a>")
#
#
#test_xl = Path("/home/tfinley/Documents/wrwn.x")
#test.add_attachment(test_xl, 'xlsx')
#test_audio = Path("/space/es1/TrafficCuts/NEW902.mp3")
#test.add_attachment(test_audio, 'mp3')
#test.send_mail()
#t_a = Attachment(test_audio, 'mp3')
#print(t_a.subtype)

#output_file = test.mp3_attachment(test_audio)
#print(output_file)
#print(type(output_file))
#
#test.attach_mp3(output_file)
#
#print(test.audio_files)
#print(type(test.prepare()))




