import turtle

my_nw = turtle.Screen()
my_nw.bgcolor("red")
my_pen = turtle.Turtle()

while True:
    for i in range(4):
        my_pen.forward(size + 1)
        my_pen.left(90)
        size = size - 5
    size = size + 1

turtle.done