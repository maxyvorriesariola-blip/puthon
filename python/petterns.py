print("half piramid pattern of stars (*): ")
n = int(input("Please enter the numder of rows: "))

for i in range(n):
    for j in range(i+1):
        print("* ", end="")
    print("")
