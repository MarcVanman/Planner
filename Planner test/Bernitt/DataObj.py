import numpy as np
import pandas as pd
import os
 
class DataObj:
 
    def __init__(self,data_path):
 
        # read in data files
        self.data_path = data_path
        filenames = ['basic.utt','courses.utt','curricula.utt','relation.utt','rooms.utt','unavailability.utt']
        self.readfiles(filenames)
 
        # store dimensions in data object
        self.nCourses = self.basic['Courses'][0]
        self.nRooms = self.basic['Rooms'][0]
        self.nDays = self.basic['Days'][0]
        self.nPeriods = self.basic['Periods_per_day'][0]
        self.nCurricula = self.basic['Curricula'][0]
        self.nConstraints = self.basic['Constraints'][0]
        self.nLecturers = self.basic['Lecturers'][0]
 
        # initialize lists used to generate the solution
        self.lectures = self.generate_lecture_list()
        self.unscheduled = []
        self.solution = np.nan*np.ones((self.nDays,self.nPeriods,self.nRooms)).astype(int)
 
        # objective function penalties
        self.unscheduled_penal = 10
        self.room_cap_penal = 1
        self.min_work_penal = 5
        self.curr_compact_penal = 2
        self.room_stab_penal = 1
 
    def readfiles(self,filenames):
        # read in data files and store them in a dictionary
        data_dict = dict()
        for file in filenames:
            name = file.split('.')[0]
            data_dict[name] = pd.read_csv(os.path.join(self.data_path,file),delimiter=' ')
 
        # unpack the dictionary and store data in the data object
        self.basic = data_dict['basic']
        self.rooms = data_dict['rooms']
        self.courses = data_dict['courses']
        self.relation = data_dict['relation']
        self.curricula = data_dict['curricula']
        self.unavailability = data_dict['unavailability']
 
        # create dictionary mapping courses to the corresponding curricula
        self.course2curr = dict()
        for course in self.relation['Course']:
            self.course2curr[course] = list(self.relation['Curriculum'][self.relation['Course']==course])
 
        # create dictionary mapping curricula to corresponding courses
        self.curr2course = dict()
        for curr in self.relation['Curriculum']:
            self.curr2course[curr] = list(self.relation['Course'][self.relation['Curriculum']==curr])
 
        self.unavailability = self.unavailability.groupby('Course') # group availabilities on course number
 
    def generate_lecture_list(self):
        # generate lecture list by looping through all course names and adding entries equal to the number of lectures
        lectures = []
        for c_nr in self.courses.index:
            nlec = self.courses.loc[c_nr,'Number_of_lectures']
            lectures += [c_nr]*nlec
 
        return np.array(lectures).astype(int)
 
    def check_feasibility(self,entry,course_nr):
        # check the feasibility of adding a given entry to the solution
 
        # unpack day, period and room + course name
        D,P,R = entry
        c_name = self.courses.loc[course_nr,'Course']
 
        # check whether entry collides with existing entries
        if ~np.isnan(self.solution[D,P,R]):
            return False
 
        # check course availability
        try:
            course_unavail = self.unavailability.get_group(c_name)
            if np.logical_and(course_unavail['Day'] == D,course_unavail['Period'] == P).any():
                #print(course_name,'is not available at this timeslot:',D,P)
                return False
        except KeyError:
            pass
 
        # get active courses, curricula and lecturers for the given day and period
        active_courses = self.solution[D,P,:][~np.isnan(self.solution[D,P,:])]
        active_curricula = self.get_list_of_course_curricula(active_courses)
        active_lecturers = self.courses.loc[active_courses,'Lecturer']
 
        # check conflicts
        if len(active_courses)!=len(set(active_courses)):
            return False
        elif len(active_curricula)!=len(set(active_curricula)):
            return False
        elif len(active_lecturers)!=len(set(active_lecturers)):
            return False
        else:
            return True
 
    def get_list_of_course_curricula(self,courses):
        curricula = []
        for c_nr in courses:
            c_name = self.courses.loc[c_nr,'Course']
            curricula+=self.course2curr[c_name]
        return curricula
 
    def generate_initial_solution(self):
        # generate a random initial solution
        lectures = self.lectures.copy()
        np.random.shuffle(lectures)
 
        # loop over all lecture id's
        for c_nr in lectures:
            # get the unused positions in the solution matrix
            free_pos = np.argwhere(np.isnan(self.solution))
            # randomly shuffle the positions
            np.random.shuffle(free_pos)
            # loop over all free positions
            for i in range(len(free_pos)):
                D,P,R = free_pos[i]
                # insert the entry if the solution is still feasible
                if self.check_feasibility((D,P,R),c_nr) is True:
                    self.solution[D,P,R] = c_nr
                    #print(lec_id,'assigned')
                    break
            # append to the unscheduled list if the lecture cannot be placed in the solution matrix
            if i==len(free_pos)-1:
                self.unscheduled.append(c_nr)
                #print(lec_id,'added to the unscheduled list')
 
    def solution_eval(self):
        # unscheduled
        unscheduled_val = len(self.unscheduled)
 
        # room capacity
        entries = np.argwhere(~np.isnan(self.solution))
        room_cap_val=0
        for e in entries:
            D,P,R = e
            c_nr = self.solution[D,P,R]
            room_cap = self.rooms.loc[R,'Capacity']
            nr_stud = self.courses.loc[c_nr,'Number_of_students']
            room_overflow = nr_stud-room_cap
            if room_overflow>0:
                room_cap_val+=room_overflow
 
        # not all courses may be present in the solution
        courses = np.unique(self.solution[~np.isnan(self.solution)]).astype(int)
 
        # room stability
        room_stab_val=0
        for c_nr in courses:
            distinct_rooms = set(np.argwhere(self.solution==c_nr)[:,2])
            room_stab_val+=len(distinct_rooms)-1
 
        # minimum working days
        min_work_val = 0
        for c_nr in courses:
            distinct_days = set(np.argwhere(self.solution==c_nr)[:,0])
            min_work_days = self.courses.loc[c_nr,'Minimum_working_days']
            diff = min_work_days-len(distinct_days)
            if diff>0:
                min_work_val+=diff
 
        # curriculum compactness
        curr_compact_val = 0
        for curr_nr in range(self.nCurricula):
            curr = self.curricula.loc[curr_nr,'Curriculum']
            curr_courses = self.curr2course[curr]
 
            bool_array = np.zeros(self.solution.shape,dtype=bool)
            for c_name in curr_courses:
                c_nr = np.argwhere(self.courses.Course==c_name)[0][0]
                bool_array+=(self.solution==c_nr)
 
            for d in range(self.nDays):
                curr_periods = np.argwhere(bool_array[d,:,:]==True)[:,0]
                for p in curr_periods:
                    if p==0:
                        if p+1 not in curr_periods:
                            curr_compact_val+=1
                    if p==(self.nPeriods-1):
                        if p-1 not in curr_periods:
                            curr_compact_val+=1
                    else:
                        if p-1 not in curr_periods or p+1 not in curr_periods:
                            curr_compact_val+=1
 
        print('unscheduled:', unscheduled_val)
        print('room capacity:', room_cap_val)
        print('minimum work:', min_work_val)
        print('curr compactness:', curr_compact_val)
        print('room stability:', room_stab_val)
 
        # objective value
        obj_val = (self.unscheduled_penal*unscheduled_val +
                   self.room_cap_penal*room_cap_val +
                   self.min_work_penal*min_work_val +
                   self.curr_compact_penal*curr_compact_val +
                   self.room_stab_penal*room_stab_val)
        
        performance=[obj_val,unscheduled_val,room_cap_val,min_work_val,curr_compact_val,room_stab_val]
        return performance 
 
    def delta_eval(self,entry,c_nr):
 
        D,P,R = entry
 
        # unscheduled
        unscheduled_val = -1 # 1 item is removed from the unscheduled list
 
        # room capacity
        room_cap = self.rooms.loc[R,'Capacity']
        nr_stud = self.courses.loc[c_nr,'Number_of_students']
        room_overflow = nr_stud-room_cap
        room_cap_val = 0
        if room_overflow>0:
            room_cap_val=room_overflow
 
 
        # minimum working days
        distinct_days = set(np.argwhere(self.solution==c_nr)[:,0])
        min_work_days = self.courses.loc[c_nr,'Minimum_working_days']
        diff = min_work_days-len(distinct_days)
 
        if D in distinct_days:
            min_work_val = 0
        else:
            if diff>0:
                min_work_val=-1
 
        # room stability
        distinct_rooms = set(np.argwhere(self.solution==c_nr)[:,2])
        if R in distinct_rooms:
            room_stab_val = 0
        else:
            if len(distinct_rooms)>0:
                room_stab_val = 1
 
        # curriculum compactness
        c_name = self.courses.loc[c_nr,'Course']
        curricula = self.course2curr[c_name]
 
        curr_compact_val = 0
        # loop over all curricula for the given course
        for curr in curricula:
            # get the courses in the given curricula
            curr_courses = self.curr2course[curr]
 
            # create boolean array indicating where courses
            bool_array = np.zeros(self.solution[D,:,:].shape,dtype=bool)
            for c_name in curr_courses:
                c_nr = np.argwhere(self.courses.Course==c_name)[0][0]
                bool_array+=(self.solution[D,:,:]==c_nr)
 
            curr_periods = np.argwhere(bool_array==True)[:,0]
            curr_periods = np.append(curr_periods,P)
            if P==0:
                if P+1 not in curr_periods:
                    curr_compact_val+=1
            if P==(self.nPeriods-1):
                if P-1 not in curr_periods:
                    curr_compact_val+=1
            else:
                if P-1 not in curr_periods or P+1 not in curr_periods:
                    curr_compact_val+=1
 
        # delta evaluation
        delta_val = (self.unscheduled_penal*unscheduled_val +
                   self.room_cap_penal*room_cap_val +
                   self.min_work_penal*min_work_val +
                   self.curr_compact_penal*curr_compact_val +
                   self.room_stab_penal*room_stab_val)
 
        return delta_val
 
    def insert(self,entry,c_nr):
        # insert entry in solution
        D,P,R = entry
        self.solution[D,P,R] = c_nr
        # remove entry from unscheduled list
        self.unscheduled.remove(self.unscheduled.index(c_nr))
 
        return self.delta_eval(entry,c_nr)
 
    def remove(self,entry):
        D,P,R = entry
        c_nr = self.solution[D,P,R]
        self.unscheduled.append(c_nr)
        self.solution[D,P,R] = np.nan
 
        return self.delta_eval(entry,c_nr)

    def RandDestroy(self, sol, no_of_destroys=1):
        for i in range(no_of_destroys):
            while True:
                D, P, R = np.random.randint(0, self.nDays), np.random.randint(0, self.nPeriods), np.random.randint(0, self.nRooms)
                if ~np.isnan(sol[D,P,R]):
                    self.remove([D,P,R])
                    break
                
     def print_solution(self):
        f = open("solution.sol", "w")
        performance=self.solution_eval()
        f.write("Objective "+str(performance[0])+"\n")
        f.write("Unscheduled "+str(performance[1])+"\n")
        f.write("RoomCapacity "+str(performance[2])+"\n")
        f.write("MinimumWorkingDays "+str(performance[3])+"\n")
        f.write("CurriculumCompactness "+str(performance[4])+"\n")
        f.write("RoomStability "+str(performance[5])+"\n")
        
        for day_idx,day in enumerate(self.solution):
            for period_idx,period in enumerate(day):
                for room_idx,room in enumerate(period):
                    if ~np.isnan(room):
                        outputStr=self.courses.loc[int(room)].Course+" "+str(day_idx)+" "+str(period_idx)+" "+self.rooms.loc[room_idx].Room
                        f.write(outputStr+"\n")