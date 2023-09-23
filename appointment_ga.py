import streamlit as st
import random
import plotly.express as px
import pandas as pd
import datetime

class Doctor:
    def _init_(self, id):
        self.id = id
        self.presence = False

class Patient:
    def _init_(self, id):
        self.id = id
        self.appointment = None

class Appointment:
    def _init_(self, doctor, timeslot):
        self.doctor = doctor
        self.timeslot = timeslot

# GA parameters
POPULATION_SIZE = 50
MUTATION_RATE = 0.01
GENERATIONS = 1000

def random_schedule(doctors, num_patients):
    schedule = []
    timeslots = list(range(10))  # Assuming 10 timeslots

    # Calculate all possible combinations of doctor and timeslots
    possible_combinations = [(doctor, timeslot) for doctor in doctors for timeslot in timeslots]
    random.shuffle(possible_combinations)

    # Create a schedule based on the number of patients or available slots, whichever is less
    num_schedules = min(num_patients, len(possible_combinations))
    for i in range(num_schedules):
        doctor, timeslot = possible_combinations[i]
        schedule.append(Appointment(doctor, timeslot))
    
    return schedule

def initialize_population(doctors, num_patients, size):
    return [random_schedule(doctors, num_patients) for _ in range(min(size, num_patients))]

def fitness(schedule):
    unique_timeslots = len(set([app.timeslot for app in schedule]))
    unique_doctors = len(set([app.doctor.id for app in schedule]))
    
    doctor_timeslot_pairs = [(app.doctor.id, app.timeslot) for app in schedule]
    unique_pairs = len(set(doctor_timeslot_pairs))
    penalty = len(doctor_timeslot_pairs) - unique_pairs

    return unique_timeslots + unique_doctors - penalty

def select(population):
    k = 3
    selected = random.sample(population, k)
    selected.sort(key=fitness, reverse=True)
    return selected[0]

def crossover(parent1, parent2, num_patients):
    crossover_point = random.randint(0, num_patients - 1)
    child1 = parent1[:crossover_point] + parent2[crossover_point:]
    child2 = parent2[:crossover_point] + parent1[crossover_point:]
    return child1, child2

def mutate(schedule, doctors, num_patients):
    for i in range(num_patients):
        if random.random() < MUTATION_RATE:
            schedule[i] = Appointment(random.choice(doctors), random.randint(0, 9))
    return schedule

def genetic_algorithm(doctors, num_patients):
    population = initialize_population(doctors, num_patients, POPULATION_SIZE)
    for _ in range(GENERATIONS):
        new_population = []
        while len(new_population) < POPULATION_SIZE:
            parent1 = select(population)
            parent2 = select(population)
            child1, child2 = crossover(parent1, parent2, num_patients)
            new_population.append(mutate(child1, doctors, num_patients))
            new_population.append(mutate(child2, doctors, num_patients))
        population = new_population
    return max(population, key=fitness)

def update_doctor_presence(doctor_id, is_present, doctors):
    doctor = [doc for doc in doctors if doc.id == doctor_id][0]
    doctor.presence = is_present

def app():
    st.title("Doctor Appointment Scheduling System")

    doctors = [Doctor(i) for i in range(10)]
    patients = [Patient(i) for i in range(100)]
    num_patients = len(patients)
    
    doc_ids = [i for i, _ in enumerate(doctors)]
    selected_doc_ids = st.multiselect("Select doctors available today:", doc_ids, default=doc_ids)

    for doc_id in selected_doc_ids:
        update_doctor_presence(doc_id, True, doctors)
        
    available_doctors = [doc for doc in doctors if doc.presence]

    if st.button('Allocate Appointments'):
        best_schedule = genetic_algorithm(available_doctors, num_patients)
        for i, patient in enumerate(patients):
            patient.appointment = best_schedule[i] if i < len(best_schedule) else None

        start_times = [datetime.datetime(2023, 1, 1, 8 + (p.appointment.timeslot if p.appointment else 0)) for p in patients]
        end_times = [stime + datetime.timedelta(hours=1) for stime in start_times]
        df = pd.DataFrame({
            'Patient': [p.id for p in patients],
            'Doctor': [p.appointment.doctor.id if p.appointment else None for p in patients],
            'x_start': start_times,
            'x_end': end_times
        }).dropna()  # remove patients without appointments

        fig = px.timeline(df, x_start='x_start', x_end='x_end', y='Patient', color='Doctor', labels={'Patient': 'Patient ID', 'Doctor': 'Doctor ID'})
        fig.update_yaxes(categoryorder='total ascending')
        st.plotly_chart(fig)

if _name_ == "_main_":
    app()
