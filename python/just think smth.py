print("Hello world i made loop, if, and else an so i'd try to make some functions and nested loops same for some math to")

num1 = int((input("Enter a number: ")))
num2 = int((input("Enter another number: ")))

if num1 > num2:
    print("The first number is greater than the second number.")

elif num1 < num2:
    print("The first number is less than the second number.")

else:
    print("The first number is equal to the second number.")

add1 = int((input("\nEnter a number to add: ")))
add2 = int((input("Enter another number to add: ")))
if add1 + add2 > 10:
    print("The sum of the two numbers is greater than 10.") 

elif add1 + add2 < 10:
    print("The sum of the two numbers is less than 10.")
else:
    print("The sum of the two numbers is equal to 10.")

sub1 = int((input("\nEnter a number to subtract: ")))
sub2 = int((input("Enter another number to subtract: ")))

if sub1 - sub2 > 0:
    print("The result of the subtraction is greater than 0.")

elif sub1 - sub2 < 0:
    print("The result of the subtraction is less than 0.") 

else:
    print("The result of the subtraction is equal to 0.")

print("\nNow let's try a loop")

for i in range(5):
    print("This is loop iteration number", i)  
print("Loop is done!")

print("\nNow let's try a while loop")
count = 0
while count < 5:
    print("This is while loop iteration number", count)
    count += 1
print("While loop is done!")

print("\nI was maybe thinking to make nested loops so here it is")

for i in range(3):
    for j in range(2):
        print("Outer loop iteration", i, "and inner loop iteration", j)

print("\nNow is function time")

def greet(name):
    return "Hello, " + name + "! Welcome to Python programming."

def add(a, b):
    return a + b
print(greet("Alice"))
print("The sum of 5 and 3 is:", add(5, 3))  

def factorial(n):
    if n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n - 1)

print("The factorial of 5 is:", factorial(5))

def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    else:
        fib_sequence = [0, 1]
        for i in range(2, n):
            next_fib = fib_sequence[i - 1] + fib_sequence[i - 2]
            fib_sequence.append(next_fib)
        return fib_sequence

print("The first 10 Fibonacci numbers are:", fibonacci(10))

print("\nI think that's enough for now, and i use VS code it have git copilot so it" \
" helped me a lot to write this code, but i also try to write some of it by myself")