import pandas as pd
from collections import defaultdict
from datetime import datetime, date
import Meetings
import Personer

class dataReader:

    def __init__(self):

        self.num_meetings = None
        self.num_persons = None
        self.meetings = []
        self.persons = []



    def read_data(self, filename):
        self.m_data = pd.read_excel(filename[0])
        self.m_data.participants = self.m_data.participants.str.replace(' ','')
        self.m_data['num_meetings'] = pd.to_numeric(self.m_data['num_meetings'].fillna(1), downcast='unsigned')
        self.m_data['ID'] = pd.to_numeric(self.m_data['ID'], downcast='unsigned')


        self.p_data = pd.read_excel(filename[1])
        self.u_data = pd.read_excel(filename[2],usecols="A:E", converters= {'B:E': pd.to_datetime})


        self.m_data = self.m_data.loc[self.m_data.index.repeat(self.m_data.num_meetings)].reset_index(drop=True)

        self.unique_meetings = self.m_data[['ID', 'days_between']].drop_duplicates(subset='ID').reset_index(drop=True)
        self.unique_dict = defaultdict(list)

        for _, row in self.unique_meetings.iterrows():
            vals = row.tolist()
            self.unique_dict[int(vals[0])].append(vals[1] // 7)
        self.unique_dict = dict(self.unique_dict)
        #print(self.unique_dict)


        self.num_meetings = len(self.m_data.index)
        self.num_persons = len(self.p_data.index)

        for i in range(self.num_meetings):
            meeting = self.m_data.iloc[i]
            self.meetings.append(meeting)

        for i in range(self.num_persons):
            person = self.p_data.iloc[i]
            self.persons.append(person)


        #self.u_data = self.u_data.set_index(['Initialer'])
        #unique_pers = list(self.u_data.index.unique())



        #Get week number and day of week for Start og Slut
        self.u_data['Start år'] = self.u_data['Start dato'].dt.isocalendar().year
        self.u_data['Start uge'] = self.u_data['Start dato'].dt.isocalendar().week
        self.u_data['Start dag'] = self.u_data['Start dato'].dt.weekday + 1

        self.u_data['End år'] = self.u_data['End dato'].dt.isocalendar().year
        self.u_data['End uge'] = self.u_data['End dato'].dt.isocalendar().week
        self.u_data['End dag'] = self.u_data['End dato'].dt.weekday + 1

        #Slet dato
        self.u_data = self.u_data.drop(columns=['Start dato', 'End dato'])

        #Flyt så vi har tiden til sidst
        self.u_data = self.u_data[['Initialer', 'Start år', 'Start uge', 'Start dag', 'Start tid', 'End år', 'End uge', 'End dag', 'End tid']]

        d = defaultdict(list)

        for _, row in self.u_data.iterrows():
            vals = row.tolist()
            d[vals[0]].append([tuple(vals[1:5]),tuple(vals[5:])])

        self.time_dict = dict(d)


