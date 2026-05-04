import turtle

t = turtle.Turtle()
s = turtle.Screen()
t.speed(0)

def draw(x, y):
    t.up(); t.goto(x, y); t.down()
    for _ in range(5):
        t.fd(50); t.rt(144)

print("hi ma'am")
s.onclick(draw)
s.listen()
s.mainloop()