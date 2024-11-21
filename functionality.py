from random import randint
db_head = ["id", 'company name',"location", 'task', "assign", 'status','cost', "payment", "Balance", "status", "start", "end", "confirm"]
company_db = {"shell": "14 noble street",
              "evinok": "elelenwo"}
engineers = ['John', 'Junior', 'bobby', 'James']

def add_company():
    company_name = input("enter company name: ")
    company_loc = input("enter company location: ")
    company_db[company_name] = {'location': company_loc}
    print(company_db)

# def add_task():
def generate_id():
    num = ""
    for i in range(5):
        digit = randint(0,9)
        num = num + str(digit)
    return num


def add_task():
    for count, name in enumerate(company_db.keys()):
        print(count, name)
    ind = int(input("Enter index corresponding to number: " ))
    company_name = (list(company_db.keys())[ind])
    print(company_name)

    location = company_db[company_name]
    task = [generate_id(), company_name, location]
    print(task)
    for i in db_head[3:]:
        data = input(f'enter {i}: ')
        task.append(data)
    print(task)

# add_task()