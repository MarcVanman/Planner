import numpy as np
import datetime
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

from datetime import date

#np.random.seed(42)

class Solver:

    def __init__(self):
        #self.weeks_left_of_year = datetime.date(datetime.date.today().isocalendar()[0],12,28).isocalendar()[1] - datetime.date.today().isocalendar()[1]  # According to the same ISO specification, January 4th is always going to be week 1 of a given year. By the same calculation, the 28th of December is then always in the last week of the year
        self.weeks_in_year = 52
        self.days_to_plan = 4    #How many days we have to plan on (including day 0) so 5 days is 4 here
        self.day_start = 8       #At what time the day starts
        self.day_end = 18        #At what time the day ends
        self.time_slots_per_day = (self.day_end-self.day_start)*4  #How many timeslots we have, in quarters after day start until day end.

    def Solve(self, data_reader):
        #Get a random initial solution with day of the year first and timeslot of that day. Shape = (num_meetings, 3)
        #Solution shape is (Week from today week, day of the week, time slot of the day)

        feasible = False
        count = 0
        while feasible == False:
            if count % 100 == 0 :
                print(count)

            sol = self.random_solution(data_reader)

            #Check feasibility of solution
            feasible = self.check_feasibility(sol, data_reader)

            if feasible == True:
                print(f"{count} solution was chekced before a solution was found")
                #print("Solution is feasible!")
                return sol
            else:
                count += 1
                #print("Solution was not feasible")


        #return feasible, error

    def random_solution(self, data_reader):

        sol = np.round(np.random.random(size=(data_reader.num_meetings,3))*np.array((self.weeks_in_year-1, self.days_to_plan, self.time_slots_per_day-1))).astype(int) + np.array((1,1,0)) #adding a day to the solution so day 1 equals monday. Minus 1 as no meeting is shorter than or equal to 15 min
        times = pd.DataFrame(sol)
        times.columns = ['Week', 'Day', 'Kvarter']
        sol = pd.concat([data_reader.m_data.reset_index(drop=True),times.reset_index(drop=True)], axis=1)
        # Get unique meeting type ids
        unique_ids = list(set(sol.ID.values))
        id_idx = []
        # Get first index of unique ids
        for id in unique_ids:
            id_idx.append(sol.ID.values.searchsorted(id, side='left'))
        # ignore rows with NAN in days between
        for i in range(len(sol)):
            if sol.num_meetings.values[i] == 1 or np.isnan(sol.days_between.values[i]):
                continue
        # If we are at a row where we see an ID for the first time, set the curr_idx to that index
            if i in id_idx:
                curr_idx = i
                continue
        # If we dont see it for the first time, set i week of that row to the week for curr_idx plus the distance to this instance
            else:
                #print(sol.Week.iloc[curr_idx])
                sol.Week.iloc[i] = int(sol.Week.iloc[curr_idx] + (i-curr_idx)*int(data_reader.unique_dict[sol.ID.iloc[i]][0]))
        return sol



    def check_feasibility(self, solution, data_reader):
        feasible = True
        #   For alle møder
        for i in range(len(solution)):

            #   Check om mødet starter senere end det må
            if solution.Kvarter.values[i] + solution.duration.values[i]/15 > self.time_slots_per_day:
                #if solution[i][2]+data_reader.meetings[i].duration/15 > self.time_slots_per_day:
                #print(f"Meeting {i} is placed too late!")
                feasible = False
                return feasible

            #   Check om ugen er gyldig
            if solution.Week.values[i]  > self.weeks_in_year:
                #if solution[i][2]+data_reader.meetings[i].duration/15 > self.time_slots_per_day:
                #print(f"Week of meeting {i} is placed too late!")
                feasible = False
                return feasible

            #   Check om personerne der skal deltage er ledige
            for pers in solution.participants.values[i].split(','): # Hvis der bruges DataFrame som løsning
            #for pers in data_reader.meetings[i].participants.split(','):
                if pers in data_reader.time_dict.keys():
                    for busy_time in data_reader.time_dict[pers]:
                        #Kan potentielt forbedres ved at ændre i data reader. Læs dato'er ind som dato istedet for tal, og spar et step
                        busy_start = datetime.datetime.combine(datetime.datetime.fromisocalendar(busy_time[0][0], busy_time[0][1], busy_time[0][2]), busy_time[0][3])
                        busy_end = datetime.datetime.combine(datetime.datetime.fromisocalendar(busy_time[1][0], busy_time[1][1], busy_time[1][2]), busy_time[1][3])

                        meeting_start = datetime.datetime.fromisocalendar(datetime.datetime.now().year+1, solution.Week.values[i], solution.Day.values[i]) + datetime.timedelta(hours=self.day_start+solution.Kvarter.values[i]/4)  # Hvis der bruges DataFrame som løsning
                        # meeting_start = datetime.datetime.fromisocalendar(datetime.datetime.now().year+1, solution[i][0], solution[i][1]) + datetime.timedelta(hours=self.day_start+solution[i][2]/4)

                        meeting_end = meeting_start + datetime.timedelta(minutes=int(solution.duration.values[i])) # Hvis der bruges DataFrame som løsning
                        # meeting_end = meeting_start + datetime.timedelta(minutes=int(data_reader.meetings[i].duration))

                        if busy_start < meeting_start < busy_end or busy_start < meeting_end < busy_end:
                            feasible = False
                            #print("Someone in the meeting is busy here")
                            return feasible

            for j in range(i+1, len(solution)):

                #   Tjek om der er deltagere i møderne der skal være i begge møder
                if (len(set(solution.participants.values[i].split(',')).intersection(
                set(solution.participants.values[j].split(',')))) > 0) :
                #if (len(set(data_reader.meetings[i].participants.split(',')).intersection(
                #        set(data_reader.meetings[j].participants.split(',')))) > 0):

                    #  Ligger møderne samme uge?
                    if solution.Week.values[i] == solution.Week.values[j]:
                    #if solution[i][0] == solution[j][0]:

                        # Ligger møderne samme dag?
                        if solution.Day.values[i] == solution.Day.values[j]:
                        #if solution[i][1] <= solution[j][1]:

                            #   Hvis møde "i" start plus møde længde når starten af møde "j"
                            if solution.Kvarter.values[i] + solution.duration.values[i]/15 <= solution.Kvarter.values[j]:
                            #if solution[i][2] + data_reader.meetings[i].duration/15 <= solution[j][2]:
                                feasible = False
                                return feasible
                                #print(f"Meeting {i} overlaps meeting {j}")

                        #   Hvis møde "j" starter før møde "i"
                        else:
                            #   Hvis møde "j" start plus møde længde når starten af møde "i"
                            if solution.Kvarter.values[j] + solution.duration.values[j]/15 >= solution.Kvarter.values[i]:
                            #if solution[j][2] + data_reader.meetings[j].duration/15 >= solution[i][2]:
                                feasible = False
                                return feasible
                                #print(f"Meeting {j} overlaps meeting {i}")

        return feasible