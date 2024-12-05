from random import randint
import os.path
import matplotlib.pyplot as plt
import io



# generates random ids for task
def generate_id():
    num = ""
    for i in range(5):
        digit = randint(0,9)
        num = num + str(digit)
    return num



# saves the upload picture and return the path to the picture
def upload_picture(picture_file, users_name):
    picture = picture_file.filename
    if not picture.endswith(('.jpg', '.png')):
        return 'profile_pic/default.jpg'
    filename = f"{users_name}.{picture[-4::]}"
    picture_path = os.path.join('static/profile_pic', filename)
    picture_file.save(picture_path)
    return f'profile_pic/{filename}'


def draw_pie_chart(data):
    label = list(data.keys())
    figures = list(data.values())
    if sum(figures) <1:
        return None
    print(figures)
    print(label)
    plt.pie(figures, labels=label)
    img_buffer = io.BytesIO()
    print(img_buffer.read())
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    return img_buffer


#function that create the id name
def id_name_generator(fn, mn, ln,database):
    # first letter of the first and middlename and the full lastname
    # . to add the names
    # if name already exists add the second letter the identical first or last name letter
    if mn is None or mn.strip() == '':
        fname = fn[0].upper()
        name = f'{fname}.{ln.capitalize()}'
        for user in database:
            if user.id_name == name:
                idname = user.id_name.split('.')
                fi = len(idname[0])
                fi += 1
                name = f'{fn[:fi].capitalize()}.{ln.capitalize()}'
    else:
        fname = fn[0].upper()
        mname = mn[0].upper()
        name = f'{fname}.{mname}.{ln.capitalize()}'
        for user in database:
            if user.id_name == name:
                idname = user.id_name.split('.')
                fi =len(idname[0])
                mi = len(idname[1])
                if fi <= mi:
                    fi +=1
                else:
                    mi +=1
                name = f'{fn[:fi].capitalize()}.{mn[:mi].capitalize()}.{ln.capitalize()}'
    return name



# Extracts the details of all staffs for admin accout
def all_staff_stats(data):
    # leave status
    leave = []
    available = []
    l_pend = []
    # active and terminated
    term = []
    active = []
    # staff and admin number
    ad_no = []
    st_no = []
    # on a job and idle
    working = []
    w_pen = []
    idle = []
    for staff in data:
        if staff.contract == 'Active':
            active.append(staff)
        else:
            term.append(staff)
        if staff.privilege == 'Staff':
            st_no.append(staff)
        elif staff.privilege == 'Administrator':
            ad_no.append(staff)
        if staff.calendar[-1].status == 'Available':
            available.append(staff)
        elif staff.calendar[-1].status == 'Pending':
            l_pend.append(staff)
        else:
            leave.append(staff)
        if staff.working is not None:
            wrk = [num.strip() for num in staff.working.split(',') if num.strip().isnumeric()]
            if len(wrk) > 0:
                working.append(staff)
        else:
            wrk = []
        if staff.pending is not None:
            pnd = [num.strip() for num in staff.pending.split(',') if num.strip().isnumeric()]
            if len(pnd) > 0:
                w_pen.append(staff)
        else:
            pnd = []
        if len(wrk) + len(pnd) == 0:
            idle.append(staff)
    summary = {
        'lv': (leave, len(leave)),
        'av': (available, len(available)),
        'lp': (l_pend, len(l_pend)),
        'tm': (term, len(term)),
        'ac': (active, len(active)),
        'ad': (ad_no, len(ad_no)),
        'st': (st_no, len(st_no)),
        'wk': (working, len(working)),
        'wp': (w_pen, len(w_pen)),
        'id': (idle, len(idle))
    }
    return summary

# Extracts the task info of a specific company
def company_taskinfo(companys):
    company_info = {}
    for company in companys:
        tsk_on = [task for task in company.task if task.status=='On going']
        tsk_comp = [task for task in company.task if task.status=='Complete']
        tsk_sus = [task for task in company.task if task.status=='Suspended']
        tsk_pen = [task for task in company.task if task.status == 'Pending']
        company_info[company.name] = (len(tsk_on), len(tsk_comp), len(tsk_pen), len(tsk_sus))

    return company_info


# gets the details of specific task
def task_info(tasks):
    if tasks:
        comp = [task for task in tasks if task.status=='Completed']
        on_going = [task for task in tasks if task.status=='On going']
        suspend = [task for task in tasks if task.status=='Suspended']
        pending = [task for task in tasks if task.status=='Pending']

        info = {
            'cm': (comp, len(comp)),
            'on': (on_going, len(on_going)),
            'su': (suspend, len(suspend)),
            'pn': (pending, len(pending))
        }
    else:
        info = {
            'cm': ([], 0),
            'on': ([], 0),
            'su': ([], 0),
            'pn': ([], 0)
        }


    return info



