import os 

a = os.listdir('E:\\Camera')
b = os.listdir('D:\\photos')
for i in b:
    if i not in a:
        print(i)