def add(P,Q):
    return P + Q

def mutiply(P,Q):
    return P * Q

def sub(P,Q):
    return P - Q

def divede(P,Q):
    return P / Q

print("Please pick a operater")
print("a add")
print("b mutiply")
print("c sub")
print("d divede")

choice = input("Please and 'a' to 'd' to pick an operater")

num_1 = int(input("Enter a number"))
num_2 = int(input("enter a number like last time"))

if choice == "a":
    print(num_1,"+",num_2,"=",add(num_1, num_2))

