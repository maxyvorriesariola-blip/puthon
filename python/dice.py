import random
import time

def roll_dice():
    print("🎲 Rolling the dice...")
    time.sleep(1)  
    
    die1 = random.randint(1, 6)
    die2 = random.randint(1, 6)
    total = die1 + die2
    
    print(f"Result: {die1} and {die2}")
    print(f"Total: {total}")
    
    if total == 7 or total == 11:
        print("Lucky number! ✨")
    elif die1 == die2:
        print("Doubles! Roll again? 🔄")

# Run the function
if __name__ == "__main__":
    roll_dice()