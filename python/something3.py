import turtle

turtle.Screen().bgcolor("black")
turtle.Screen(). setup(300,400)

polygon = turtle.Turtle()


num_side = 6 
side_leth = 70
angle = 360 / num_side

for i in range(num_side):
    polygon.forward(side_leth)
    polygon.left(angle)

turtle.done