import os, datetime


class File:
    def __init__(self, path: str):
        self.name = os.path.basename(path)
        self.location = path
        self.size = os.path.getsize(path)
        self.creation_date = datetime.datetime.fromtimestamp(os.path.getctime(path))
        self.change_date = datetime.datetime.fromtimestamp(os.path.getmtime(path))
        self.extension = os.path.splitext(path)[1]
        self.files = []
        self.folders = []
        self.previous = None

    def __repr__(self):
        return (f'-- {self.name} -- {self.location} -- {self.size} -- {self.change_date} -- {self.creation_date}')


DIRECTORY = r'C:\Users\topor\OneDrive\Рабочий стол\check'
CURRENT = File(DIRECTORY)


def fill_disk_usage(path: str, current: File):
    for file in (f for f in os.listdir(path) if not os.path.isdir(os.path.join(path, f))):
        current.files.append(File(os.path.join(path, file)))

    for folder in (f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))):
        current.folders.append(File(os.path.join(path, folder)))

    for folder in current.folders:
        fill_disk_usage(os.path.join(path, folder.name), folder)


fill_disk_usage(DIRECTORY, CURRENT)
print(CURRENT)