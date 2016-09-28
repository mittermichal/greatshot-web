#http://stackoverflow.com/a/15561383/2560239
def chdir(ftp, directory):
  ch_dir_rec(ftp, directory.split('/'))


# Check if directory exists (in current location)
def directory_exists(ftp, directory):
  filelist = []
  ftp.retrlines('LIST', filelist.append)
  for f in filelist:
    if f.split()[-1] == directory and f.upper().startswith('D'):
      return True
  return False


def ch_dir_rec(ftp, descending_path_split):
  if len(descending_path_split) == 0:
    return

  next_level_directory = descending_path_split.pop(0)

  if not directory_exists(ftp, next_level_directory):
    ftp.mkd(next_level_directory)
  ftp.cwd(next_level_directory)
  ch_dir_rec(ftp, descending_path_split)

