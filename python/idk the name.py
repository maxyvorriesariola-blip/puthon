import time

# --- THE DATA ENGINE ---
class EmployeeSystem:
    def __init__(self):
        # Starting with some sample data
        self.employees = [
            {"id": 101, "name": "Alice", "dept": "Engineering", "salary": 95000},
            {"id": 102, "name": "Bob", "dept": "Design", "salary": 75000},
            {"id": 103, "name": "Charlie", "dept": "Marketing", "salary": 65000}
        ]

    def add_employee(self, name, dept, salary):
        new_id = self.employees[-1]["id"] + 1 if self.employees else 101
        new_emp = {"id": new_id, "name": name, "dept": dept, "salary": salary}
        self.employees.append(new_emp)
        print(f"\n✅ Added {name} successfully with ID {new_id}!")

    def list_all(self):
        print(f"\n{'ID':<5} | {'NAME':<12} | {'DEPARTMENT':<15} | {'SALARY':<10}")
        print("-" * 50)
        for emp in self.employees:
            print(f"{emp['id']:<5} | {emp['name']:<12} | {emp['dept']:<15} | ${emp['salary']:,}")

    def get_stats(self):
        if not self.employees:
            return print("No data available.")
        
        # Using Logic to calculate totals
        total_salary = sum(emp['salary'] for emp in self.employees)
        avg_salary = total_salary / len(self.employees)
        highest = max(self.employees, key=lambda x: x['salary'])
        
        print("\n--- 📊 DEPARTMENT ANALYTICS ---")
        print(f"Total Staff: {len(self.employees)}")
        print(f"Average Salary: ${avg_salary:,.2f}")
        print(f"Highest Earner: {highest['name']} (${highest['salary']:,})")

# --- THE USER INTERFACE ---
def run_app():
    system = EmployeeSystem()
    
    while True:
        print("\n=== 🏢 CORPORATE DIRECTORY v2.0 ===")
        print("1. View All Employees")
        print("2. Add New Hire")
        print("3. View Financial Stats")
        print("4. Search by Name")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ")
        
        if choice == '1':
            system.list_all()
        elif choice == '2':
            name = input("Enter name: ")
            dept = input("Enter department: ")
            try:
                sal = int(input("Enter annual salary: "))
                system.add_employee(name, dept, sal)
            except ValueError:
                print("❌ Error: Salary must be a number!")
        elif choice == '3':
            system.get_stats()
        elif choice == '4':
            search = input("Search name: ").lower()
            results = [e for e in system.employees if search in e['name'].lower()]
            if results:
                print("\nSearch Results:")
                for r in results: print(f"-> {r['name']} ({r['dept']})")
            else:
                print("No employees found.")
        elif choice == '5':
            print("Shutting down... Goodbye!")
            break
        else:
            print("Invalid input!")
        
        time.sleep(1) # Slows it down for readability

if __name__ == "__main__":
    run_app()