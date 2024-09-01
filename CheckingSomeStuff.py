from os import stat
import pwd
def find_owner(filename):
    return pwd.getpwuid(stat(filename).st_uid).pw_name
print(find_owner('C:\\Users\\topor\\OneDrive\\Рабочий стол\\check'))