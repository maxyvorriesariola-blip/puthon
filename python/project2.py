def geart_user(hello):
   print("Hello world i am max and i am 13 to 14 year's old and i'd")
   print("learn coding in codingal and i did this project alone but it take me")
   print("45 mins or more so i hope you can read it and try it hope you enloy it")

geart_user("boom")

def making_a_game(code):
    print("\nparts of input, process, and output")
    print("\nthe 'input' is an area for you can put code's like 'print' and more then it prosess it")
    print("\nthe 'prosess' part is a loading area for the code you put in the input area so after is done procesing it show in the output area as a result")
    print("\nthe 'output' area it show after the finish code or the result for the in the input so that when you make a web it show you the finish code or result before you can make it public")     

making_a_game("input")
 
def adding(A, B):   
   return A + B 

def subtracting(A, B):   
   return A - B 

print("\nA. adding")
print("B, subtracting")

choice = input("Please enter choice A or B: ") 

num1 = input("Please enter a number [1] to [1000] is up to you what you will add")
num2 = input("Please enter a number like last time")

if (choice == "A"):
   print(num1, "+", num2, "=", adding(num1, num2))

elif (choice == "B"):
   print(num1, "-" ,num2, "=", subtracting(num1, num2))