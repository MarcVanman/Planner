import dataReader
import datetime
import Solver
import numpy as np


filenames = ['C:/Users/marcv/Desktop/Planner test/møder.xlsx', 'C:/Users/marcv/Desktop/Planner test/personer.xlsx', 'C:/Users/marcv/Desktop/Planner test/Unavailability.xlsx']

data_reader = dataReader.dataReader()

data_reader.read_data(filenames)

solver = Solver.Solver()
solution = solver.Solve(data_reader)


def get_date(row):
    meeting_date = datetime.datetime.fromisocalendar(datetime.datetime.now().year+1, row['Week'], row['Day']) + datetime.timedelta(minutes=9*60+int(row['Kvarter']*15))
    return meeting_date

solution['Dato & Tid'] = solution.apply (lambda row: get_date(row), axis=1)
#solution = solution.drop(['num_meetings', 'days_between', 'Week', 'Day', 'Kvarter'], axis=1)
print(solution)
