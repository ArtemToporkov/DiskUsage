import os
import operator

def get_folder_size(folder):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def get_files(folder):
    file_list = []
    for dirpath, dirnames, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            file_list.append((fp, os.path.getsize(fp)))
    return file_list

def display_statistics(folder):
    total_size = get_folder_size(folder)
    print(f"Total size of folder '{folder}': {total_size} bytes")

    file_list = get_files(folder)
    file_list.sort(key=operator.itemgetter(1), reverse=True)

    print("\nFile List:")
    for file in file_list:
        print(f"{file[0]} - {file[1]} bytes")

if __name__ == "__main__":
    folder = 'C:\\Users\\topor\\OneDrive\\Рабочий стол\\check'
    display_statistics(folder)