string = input("Please enter your own word: ")

char = input("Please enter your own person: ")

i = 0
count = 0

while (i < len(string)):
    if(string[i] == char):
        count = count + 1
    i = i + 1
    
print("here is the total of the number of hundred times", char,"has happen", count)